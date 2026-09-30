import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_pool, close_pool, fetch_all, fetch_one, execute, execute_returning
from app.cv_parser import extraer_texto, FormatoNoSoportado
from app.embeddings import indexar_cv
from app.llm_extraction import extraer_datos_postulante
from app.evaluation_engine import evaluar_puesto
from app.schemas import NuevaEvaluacionRequest, PostulanteOut

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ats")

app = FastAPI(title="ATS Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_pool()


@app.on_event("shutdown")
def shutdown():
    close_pool()


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- CVs / postulantes ----------

@app.post("/api/cvs", response_model=list[PostulanteOut])
async def cargar_cvs(files: list[UploadFile] = File(...)):
    """Sube uno o mas CVs: extrae el texto, saca datos de contacto con
    el LLM, crea/reutiliza el postulante (por email) y carga el CV al
    indice RAG (chunking + embeddings en pgvector)."""
    resultados = []

    for file in files:
        contenido = await file.read()
        try:
            texto = extraer_texto(file.filename, contenido)
        except FormatoNoSoportado as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not texto.strip():
            raise HTTPException(
                status_code=422,
                detail=f"No se pudo extraer texto de '{file.filename}' (¿es un PDF escaneado sin OCR?)",
            )

        datos = extraer_datos_postulante(texto)

        postulante = None
        if datos.email:
            postulante = fetch_one(
                "SELECT id, nombre, email, telefono FROM postulantes WHERE email = %s",
                (datos.email,),
            )

        if postulante is None:
            postulante = execute_returning(
                """
                INSERT INTO postulantes (nombre, email, telefono)
                VALUES (%s, %s, %s)
                RETURNING id, nombre, email, telefono
                """,
                (datos.nombre, datos.email, datos.telefono),
            )

        cv = execute_returning(
            """
            INSERT INTO cvs (postulante_id, nombre_archivo, texto_extraido, estado)
            VALUES (%s, %s, %s, 'procesando')
            RETURNING id
            """,
            (postulante["id"], file.filename, texto),
        )

        try:
            cantidad_chunks = indexar_cv(cv["id"], texto)
            execute("UPDATE cvs SET estado = 'procesado' WHERE id = %s", (cv["id"],))
        except Exception:
            execute("UPDATE cvs SET estado = 'error' WHERE id = %s", (cv["id"],))
            logger.exception("Error indexando CV %s", file.filename)
            raise HTTPException(
                status_code=500, detail=f"Error indexando '{file.filename}' en el RAG"
            )

        resultados.append(
            PostulanteOut(
                postulante_id=postulante["id"],
                nombre=postulante["nombre"],
                email=postulante["email"],
                telefono=postulante["telefono"],
                cv_id=cv["id"],
                nombre_archivo=file.filename,
                estado="procesado",
                cantidad_chunks=cantidad_chunks,
            )
        )

    return resultados


@app.get("/api/postulantes", response_model=list[PostulanteOut])
def listar_postulantes():
    filas = fetch_all(
        """
        SELECT DISTINCT ON (p.id)
            p.id AS postulante_id, p.nombre, p.email, p.telefono,
            c.id AS cv_id, c.nombre_archivo, c.estado,
            (SELECT count(*) FROM cv_chunks WHERE cv_id = c.id) AS cantidad_chunks
        FROM postulantes p
        JOIN cvs c ON c.postulante_id = p.id
        ORDER BY p.id, c.created_at DESC
        """
    )
    return filas


# ---------- Evaluacion de un puesto ----------

@app.post("/api/evaluaciones")
def nueva_evaluacion(body: NuevaEvaluacionRequest):
    candidatos = fetch_all("SELECT id FROM postulantes LIMIT 1")
    if not candidatos:
        raise HTTPException(
            status_code=400,
            detail="Todavia no hay CVs cargados. Subi al menos un CV antes de evaluar un puesto.",
        )

    puesto = execute_returning(
        "INSERT INTO puestos (titulo, descripcion) VALUES (%s, %s) RETURNING id",
        (body.titulo, body.descripcion),
    )

    for s in body.skills:
        execute(
            """
            INSERT INTO puesto_skills (puesto_id, nombre_skill, tipo, peso)
            VALUES (%s, %s, %s, %s)
            """,
            (puesto["id"], s.nombre_skill, s.tipo, s.peso),
        )

    skills_puesto = [s.model_dump() for s in body.skills]
    resultados = evaluar_puesto(puesto["id"], skills_puesto)

    return {"puesto_id": puesto["id"], "titulo": body.titulo, "resultados": resultados}

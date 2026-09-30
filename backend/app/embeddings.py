from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.db import get_conn, fetch_all

_embeddings_client: OpenAIEmbeddings | None = None

# funcion para convertir un vector a literal de postgres
def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"

# funcion para obtener el cliente de embeddings (singleton)
def get_embeddings_client() -> OpenAIEmbeddings:
    global _embeddings_client
    if _embeddings_client is None:
        _embeddings_client = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    return _embeddings_client

# funcion para chunkear un texto en pedazos mas chicos, para luego generar embeddings de cada chunk
def chunkear_texto(texto: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(texto)
    return [c.strip() for c in chunks if c.strip()]

# funcion para indexar un CV en la base de datos, generando embeddings de cada chunk y guardandolos en cv_chunks
def indexar_cv(cv_id: int, texto: str) -> int:
    """Chunkea el texto del CV, genera embeddings y los guarda en
    cv_chunks. Devuelve la cantidad de chunks guardados."""
    chunks = chunkear_texto(texto)
    if not chunks:
        return 0

    vectores = get_embeddings_client().embed_documents(chunks)

    with get_conn() as conn:
        with conn.cursor() as cur:
            for i, (chunk, vector) in enumerate(zip(chunks, vectores)):
                cur.execute(
                    """
                    INSERT INTO cv_chunks (cv_id, chunk_index, contenido, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (cv_id, i, chunk, _vector_literal(vector)),
                )
    return len(chunks)

# funcion para buscar los chunks mas relevantes de un CV dado, segun una consulta (ej: nombre de una skill)
def buscar_chunks_relevantes(cv_id: int, consulta: str, top_k: int | None = None) -> list[dict]:
    """Busca, dentro de los chunks de UN cv puntual, los mas parecidos
    (por similitud coseno) a la consulta (ej: el nombre de una skill).
    Esto es lo que le da evidencia concreta al LLM para juzgar si el
    candidato tiene o no esa skill."""
    top_k = top_k or settings.RAG_TOP_K
    vector_consulta = _vector_literal(get_embeddings_client().embed_query(consulta))

    return fetch_all(
        """
        SELECT contenido, 1 - (embedding <=> %s::vector) AS similitud
        FROM cv_chunks
        WHERE cv_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (vector_consulta, cv_id, vector_consulta, top_k),
    )

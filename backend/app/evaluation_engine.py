import json

from app.db import fetch_all, execute_returning
from app.embeddings import buscar_chunks_relevantes
from app.llm_extraction import evaluar_candidato, EvaluacionSkill

# funcion para obtener todos los candidatos (postulantes con CV procesado) y evaluarlos contra un puesto
def _obtener_candidatos() -> list[dict]:
    return fetch_all(
        """
        SELECT DISTINCT ON (p.id)
            p.id AS postulante_id,
            p.nombre,
            p.email,
            c.id AS cv_id,
            c.nombre_archivo
        FROM postulantes p
        JOIN cvs c ON c.postulante_id = p.id
        WHERE c.estado = 'procesado'
        ORDER BY p.id, c.created_at DESC
        """
    )


def _normalizar(nombre_skill: str) -> str:
    return nombre_skill.strip().lower()

# funcion para evaluar un candidato (postulante con CV procesado) contra un conjunto de skills de un puesto
def _evaluar_un_candidato(cv_id: int, skills_puesto: list[dict]) -> list[EvaluacionSkill]:
    evidencia_por_skill: dict[str, list[str]] = {}
    for skill in skills_puesto:
        chunks = buscar_chunks_relevantes(cv_id, skill["nombre_skill"])
        evidencia_por_skill[skill["nombre_skill"]] = [c["contenido"] for c in chunks]

    return evaluar_candidato(evidencia_por_skill)

# funcion para la Capa 1 de descarte: si el candidato no tiene alguna skill obligatoria, se descarta y no se evalua la Capa 2
def _capa1_descarte(
    evaluaciones_skill: list[EvaluacionSkill], skills_puesto: list[dict]
) -> str | None:
    """Devuelve el motivo de descarte, o None si pasa la Capa 1."""
    por_nombre = {_normalizar(e.nombre_skill): e for e in evaluaciones_skill}
    faltantes = []

    for skill in skills_puesto:
        if skill["tipo"] != "obligatoria":
            continue
        evaluacion = por_nombre.get(_normalizar(skill["nombre_skill"]))
        if evaluacion is None or not evaluacion.presente:
            faltantes.append(skill["nombre_skill"])

    if not faltantes:
        return None

    return "No cumple con la(s) skill(s) obligatoria(s): " + ", ".join(faltantes)

# funcion para la Capa 2 de scoring: calcula el score final del candidato segun las skills del puesto y sus pesos, y devuelve el detalle de cada skill evaluada
def _capa2_score(
    evaluaciones_skill: list[EvaluacionSkill], skills_puesto: list[dict]
) -> tuple[float, list[dict]]:
    por_nombre = {_normalizar(e.nombre_skill): e for e in evaluaciones_skill}
    detalle = []
    suma_ponderada = 0.0
    suma_pesos = 0.0

    for skill in skills_puesto:
        evaluacion = por_nombre.get(_normalizar(skill["nombre_skill"]))
        score = evaluacion.score if evaluacion else 0
        presente = evaluacion.presente if evaluacion else False
        justificacion = evaluacion.justificacion if evaluacion else "No se encontro evidencia."
        peso = float(skill["peso"])

        suma_ponderada += peso * score
        suma_pesos += peso

        detalle.append(
            {
                "nombre_skill": skill["nombre_skill"],
                "tipo": skill["tipo"],
                "peso": peso,
                "presente": presente,
                "score": score,
                "justificacion": justificacion,
            }
        )

    score_final = round(suma_ponderada / suma_pesos, 1) if suma_pesos > 0 else 0.0
    return score_final, detalle

# funcion para evaluar un puesto y todos sus postulantes
def evaluar_puesto(puesto_id: int, skills_puesto: list[dict]) -> list[dict]:
    candidatos = _obtener_candidatos()
    resultados = []

    for candidato in candidatos:
        evaluaciones_skill = _evaluar_un_candidato(candidato["cv_id"], skills_puesto)
        motivo_descarte = _capa1_descarte(evaluaciones_skill, skills_puesto)
        descartado = motivo_descarte is not None

        if descartado:
            score_final = None
            _, detalle = _capa2_score(evaluaciones_skill, skills_puesto)
        else:
            score_final, detalle = _capa2_score(evaluaciones_skill, skills_puesto)

        fila = execute_returning(
            """
            INSERT INTO evaluaciones
                (puesto_id, postulante_id, cv_id, descartado, motivo_descarte, score_final, detalle_skills)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id, created_at
            """,
            (
                puesto_id,
                candidato["postulante_id"],
                candidato["cv_id"],
                descartado,
                motivo_descarte,
                score_final,
                json.dumps(detalle),
            ),
        )

        resultados.append(
            {
                "evaluacion_id": fila["id"],
                "postulante_id": candidato["postulante_id"],
                "nombre": candidato["nombre"],
                "email": candidato["email"],
                "cv_id": candidato["cv_id"],
                "nombre_archivo": candidato["nombre_archivo"],
                "descartado": descartado,
                "motivo_descarte": motivo_descarte,
                "score_final": score_final,
                "detalle_skills": detalle,
            }
        )

    resultados.sort(
        key=lambda r: (r["descartado"], -(r["score_final"] or 0))
    )
    return resultados

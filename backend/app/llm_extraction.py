from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.OPENAI_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
    return _llm


# ---------- 1. Datos basicos del postulante ----------
# Extrae los datos de contacto basicos de un CV.
class DatosPostulante(BaseModel):
    nombre: str | None = Field(None, description="Nombre completo del postulante, si figura en el CV")
    email: str | None = Field(None, description="Email de contacto, si figura en el CV")
    telefono: str | None = Field(None, description="Telefono de contacto, si figura en el CV")


_PROMPT_DATOS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extraes datos de contacto basicos de un CV. Si un dato no "
            "aparece explicitamente, dejalo en null. No inventes nada.",
        ),
        ("human", "Texto del CV:\n\n{texto_cv}"),
    ]
)


def extraer_datos_postulante(texto_cv: str) -> DatosPostulante:
    chain = _PROMPT_DATOS | get_llm().with_structured_output(DatosPostulante)
    # Con CVs muy largos alcanza con el principio para los datos de contacto
    return chain.invoke({"texto_cv": texto_cv[:4000]})


# ---------- 2. Evaluacion de skills contra evidencia RAG ----------
# Extrae, para cada skill requerida, si el postulante la tiene y que tan fuerte la tiene, segun la evidencia encontrada en el CV.
class EvaluacionSkill(BaseModel):
    nombre_skill: str = Field(description="Nombre de la skill evaluada, tal cual se paso")
    presente: bool = Field(
        description="True si el CV demuestra genuinamente que el postulante tiene esta skill"
    )
    score: int = Field(
        ge=0, le=100,
        description=(
            "0-100. 0 si no hay evidencia. Score bajo (1-40) si se menciona "
            "de forma generica o basica. Score medio (41-70) si hay uso "
            "concreto/intermedio. Score alto (71-100) si el CV muestra "
            "nivel avanzado/experto, con anios de experiencia o proyectos "
            "concretos que lo respalden."
        ),
    )
    justificacion: str = Field(
        description="1-2 frases explicando el score, citando o parafraseando el CV"
    )


class EvaluacionCompleta(BaseModel):
    resultados: list[EvaluacionSkill]


_PROMPT_EVALUACION = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Sos un evaluador tecnico de RRHH muy exigente y objetivo. "
            "Para cada skill requerida vas a recibir fragmentos del CV "
            "recuperados por busqueda semantica (pueden no ser perfectos "
            "ni estar completos). Con eso, decidi si el postulante "
            "realmente tiene esa skill y que tan fuerte la tiene. "
            "Si los fragmentos no muestran evidencia real de la skill, "
            "presente=false y score=0, aunque la palabra aparezca "
            "mencionada de pasada. No inventes informacion que no este "
            "en los fragmentos.",
        ),
        (
            "human",
            "Skills a evaluar, con la evidencia encontrada en el CV para cada una:\n\n{bloques_evidencia}",
        ),
    ]
)


def evaluar_candidato(evidencia_por_skill: dict[str, list[str]]) -> list[EvaluacionSkill]:
    """evidencia_por_skill: {nombre_skill: [chunks de texto relevantes]}"""
    bloques = []
    for nombre_skill, chunks in evidencia_por_skill.items():
        if chunks:
            evidencia = "\n".join(f"  - \"{c}\"" for c in chunks)
        else:
            evidencia = "  (no se encontro evidencia relevante en el CV)"
        bloques.append(f"Skill: {nombre_skill}\nEvidencia:\n{evidencia}")

    bloques_evidencia = "\n\n".join(bloques)

    chain = _PROMPT_EVALUACION | get_llm().with_structured_output(EvaluacionCompleta)
    resultado: EvaluacionCompleta = chain.invoke({"bloques_evidencia": bloques_evidencia})
    return resultado.resultados

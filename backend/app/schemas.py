from pydantic import BaseModel, Field


class SkillRequerida(BaseModel):
    nombre_skill: str = Field(min_length=1)
    tipo: str = Field(pattern="^(obligatoria|deseable)$")
    peso: float = Field(gt=0, default=1)


class NuevaEvaluacionRequest(BaseModel):
    titulo: str = Field(min_length=1)
    descripcion: str | None = None
    skills: list[SkillRequerida] = Field(min_length=1)


class PostulanteOut(BaseModel):
    postulante_id: int
    nombre: str | None
    email: str | None
    telefono: str | None
    cv_id: int
    nombre_archivo: str
    estado: str
    cantidad_chunks: int | None = None

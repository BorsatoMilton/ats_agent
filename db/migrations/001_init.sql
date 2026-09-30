CREATE EXTENSION IF NOT EXISTS vector;

-- Un puesto de trabajo que se busca cubrir.
CREATE TABLE IF NOT EXISTS puestos (
    id          SERIAL PRIMARY KEY,
    titulo      TEXT NOT NULL,
    descripcion TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Skills requeridas para un puesto. "tipo" define si son obligatorias
-- (descartan al postulante si faltan, Capa 1) o deseables (solo suman
-- puntos, Capa 2). "peso" pondera la importancia relativa de esa skill
-- dentro de su categoria.
CREATE TABLE IF NOT EXISTS puesto_skills (
    id            SERIAL PRIMARY KEY,
    puesto_id     INTEGER NOT NULL REFERENCES puestos(id) ON DELETE CASCADE,
    nombre_skill  TEXT NOT NULL,
    tipo          TEXT NOT NULL CHECK (tipo IN ('obligatoria', 'deseable')),
    peso          NUMERIC NOT NULL DEFAULT 1 CHECK (peso > 0),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_puesto_skills_puesto_id ON puesto_skills(puesto_id);

-- Una persona postulante. Se crea/reutiliza al cargar un CV.
CREATE TABLE IF NOT EXISTS postulantes (
    id         SERIAL PRIMARY KEY,
    nombre     TEXT,
    email      TEXT,
    telefono   TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- El archivo de CV subido y su texto ya extraido (pypdf / python-docx).
CREATE TABLE IF NOT EXISTS cvs (
    id              SERIAL PRIMARY KEY,
    postulante_id   INTEGER NOT NULL REFERENCES postulantes(id) ON DELETE CASCADE,
    nombre_archivo  TEXT NOT NULL,
    texto_extraido  TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'procesado'
                        CHECK (estado IN ('procesando', 'procesado', 'error')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cvs_postulante_id ON cvs(postulante_id);

-- Chunks del CV con su embedding: esto es el indice del RAG.
-- 1536 = dimension de text-embedding-3-small (ver EMBEDDING_DIM en .env).
CREATE TABLE IF NOT EXISTS cv_chunks (
    id          SERIAL PRIMARY KEY,
    cv_id       INTEGER NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    contenido   TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cv_chunks_cv_id ON cv_chunks(cv_id);

-- Indice ivfflat para busqueda por similitud coseno. Con pocos datos
-- (etapa de desarrollo) no aporta demasiado, pero ya queda preparado.
-- Requiere ANALYZE cv_chunks; despues de cargar los primeros CVs para
-- que el planner lo aproveche bien.
CREATE INDEX IF NOT EXISTS idx_cv_chunks_embedding
    ON cv_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Resultado de evaluar un postulante contra un puesto: la Capa 1
-- (descarte) y la Capa 2 (score) quedan registradas aca, junto con el
-- detalle por skill para poder mostrarlo/auditarlo en el frontend.
CREATE TABLE IF NOT EXISTS evaluaciones (
    id              SERIAL PRIMARY KEY,
    puesto_id       INTEGER NOT NULL REFERENCES puestos(id) ON DELETE CASCADE,
    postulante_id   INTEGER NOT NULL REFERENCES postulantes(id) ON DELETE CASCADE,
    cv_id           INTEGER NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    descartado      BOOLEAN NOT NULL DEFAULT false,
    motivo_descarte TEXT,
    score_final     NUMERIC,
    detalle_skills  JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_puesto_id ON evaluaciones(puesto_id);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_postulante_id ON evaluaciones(postulante_id);

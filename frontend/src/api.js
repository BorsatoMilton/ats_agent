import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

export async function cargarCVs(files, onProgress) {
  const formData = new FormData();
  for (const file of files) formData.append("files", file);

  const { data } = await api.post("/api/cvs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });
  return data;
}

export async function listarPostulantes() {
  const { data } = await api.get("/api/postulantes");
  return data;
}

export async function crearEvaluacion({ titulo, descripcion, skills }) {
  const { data } = await api.post("/api/evaluaciones", {
    titulo,
    descripcion: descripcion || null,
    skills,
  });
  return data;
}

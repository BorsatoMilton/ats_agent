import { useEffect, useState, useCallback } from "react";
import { cargarCVs, listarPostulantes } from "../api";

export default function CargaCVs() {
  const [arrastrando, setArrastrando] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const [error, setError] = useState(null);
  const [postulantes, setPostulantes] = useState([]);

  // Carga la lista de postulantes desde el backend
  const cargarLista = useCallback(async () => {
    try {
      const data = await listarPostulantes();
      setPostulantes(data);
    } catch {
      // silencioso: si el backend todavia no esta arriba, no rompemos la pantalla
    }
  }, []);

  useEffect(() => {
    cargarLista();
  }, [cargarLista]);

  // Maneja la subida de archivos: filtra por extensiones, llama a la API y actualiza el progreso
  const subirArchivos = async (fileList) => {
    const files = Array.from(fileList).filter((f) =>
      /\.(pdf|docx)$/i.test(f.name)
    );
    if (files.length === 0) {
      setError("Solo se aceptan archivos .pdf o .docx");
      return;
    }

    setError(null);
    setSubiendo(true);
    setProgreso(0);
    try {
      await cargarCVs(files, setProgreso);
      await cargarLista();
    } catch (err) {
      setError(err.response?.data?.detail || "Error subiendo los CVs");
    } finally {
      setSubiendo(false);
      setProgreso(0);
    }
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastrando(false);
          subirArchivos(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
          arrastrando ? "border-indigo-400 bg-indigo-50" : "border-slate-300 bg-white"
        }`}
      >
        <p className="text-slate-600 mb-2">
          Arrastrá los CVs acá (.pdf / .docx), o elegilos manualmente
        </p>
        <label className="inline-block cursor-pointer rounded-md bg-indigo-600 text-white text-sm font-medium px-4 py-2 hover:bg-indigo-700">
          Elegir archivos
          <input
            type="file"
            multiple
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => subirArchivos(e.target.files)}
          />
        </label>

        {subiendo && (
          <p className="mt-3 text-sm text-indigo-600">
            Subiendo y procesando (parseo + embeddings)... {progreso}%
          </p>
        )}
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">
          CVs cargados ({postulantes.length})
        </h2>
        {postulantes.length === 0 ? (
          <p className="text-sm text-slate-400">Todavía no cargaste ningún CV.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full">
              <thead className="bg-slate-100">
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 px-3">Nombre</th>
                  <th className="py-2 px-3">Email</th>
                  <th className="py-2 px-3">Archivo</th>
                  <th className="py-2 px-3">Estado</th>
                  <th className="py-2 px-3">Chunks en el RAG</th>
                </tr>
              </thead>
              <tbody>
                {postulantes.map((p) => (
                  <tr key={p.cv_id} className="border-t border-slate-100">
                    <td className="py-2 px-3 text-sm font-medium text-slate-700">
                      {p.nombre || "(sin nombre detectado)"}
                    </td>
                    <td className="py-2 px-3 text-sm text-slate-500">{p.email || "—"}</td>
                    <td className="py-2 px-3 text-sm text-slate-500">{p.nombre_archivo}</td>
                    <td className="py-2 px-3 text-sm">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          p.estado === "procesado"
                            ? "bg-emerald-100 text-emerald-700"
                            : p.estado === "error"
                            ? "bg-red-100 text-red-700"
                            : "bg-amber-100 text-amber-700"
                        }`}
                      >
                        {p.estado}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-sm text-slate-500">{p.cantidad_chunks ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

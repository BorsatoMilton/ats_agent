import { useState } from "react";
import BusquedaCandidatos from "./components/BusquedaCandidatos";
import CargaCVs from "./components/CargaCVs";

export default function App() {
  const [tab, setTab] = useState("busqueda");

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-slate-800">ATS Agent</h1>
          <p className="text-sm text-slate-500">
            Filtrado y ranking de candidatos con IA + RAG
          </p>
        </div>
      </header>

      <nav className="max-w-5xl mx-auto px-4 mt-4">
        <div className="inline-flex rounded-lg bg-slate-100 p-1">
          <button
            onClick={() => setTab("busqueda")}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
              tab === "busqueda" ? "bg-white shadow text-slate-800" : "text-slate-500"
            }`}
          >
            Buscar candidatos
          </button>
          <button
            onClick={() => setTab("cargar")}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
              tab === "cargar" ? "bg-white shadow text-slate-800" : "text-slate-500"
            }`}
          >
            Cargar CVs
          </button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {tab === "busqueda" ? <BusquedaCandidatos /> : <CargaCVs />}
      </main>
    </div>
  );
}

import { useState } from "react";
import SkillsForm, { nuevaSkill } from "./SkillsForm";
import ResultadosRanking from "./ResultadosRanking";
import { crearEvaluacion } from "../api";

export default function BusquedaCandidatos() {
  const [titulo, setTitulo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [skills, setSkills] = useState([nuevaSkill()]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [resultado, setResultado] = useState(null);

  // Maneja el submit del formulario: valida los datos y llama a la API para crear la evaluación
  const submit = async (e) => {
    e.preventDefault();
    setError(null);

    const skillsValidas = skills
      .filter((s) => s.nombre_skill.trim())
      .map((s) => ({ nombre_skill: s.nombre_skill.trim(), tipo: s.tipo, peso: s.peso }));

    if (!titulo.trim()) {
      setError("Ingresá el título del puesto.");
      return;
    }
    if (skillsValidas.length === 0) {
      setError("Agregá al menos una skill.");
      return;
    }

    setCargando(true);
    setResultado(null);
    try {
      const data = await crearEvaluacion({ titulo, descripcion, skills: skillsValidas });
      setResultado(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Error evaluando a los candidatos");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div>
      <form onSubmit={submit} className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Título del puesto
          </label>
          <input
            type="text"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder="Ej: Desarrollador/a Backend Python Senior"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Descripción del puesto (opcional)
          </label>
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={3}
            placeholder="Contexto adicional del puesto, equipo, responsabilidades..."
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <SkillsForm skills={skills} setSkills={setSkills} />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={cargando}
          className="rounded-md bg-indigo-600 text-white text-sm font-medium px-4 py-2 hover:bg-indigo-700 disabled:opacity-50"
        >
          {cargando ? "Evaluando candidatos (puede tardar un poco)..." : "Buscar y rankear candidatos"}
        </button>
      </form>

      <ResultadosRanking resultado={resultado} />
    </div>
  );
}

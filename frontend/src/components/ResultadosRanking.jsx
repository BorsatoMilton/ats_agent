import { useState } from "react";

function FilaCandidato({ resultado, posicion }) {
  const [abierto, setAbierto] = useState(false);
  // Maneja la apertura/cierre del detalle de un candidato al hacer click en la fila
  return (
    <>
      <tr
        className={`border-b border-slate-100 cursor-pointer hover:bg-slate-50 ${
          resultado.descartado ? "opacity-60" : ""
        }`}
        onClick={() => setAbierto(!abierto)}
      >
        <td className="py-3 px-3 text-sm text-slate-500">
          {resultado.descartado ? "—" : posicion}
        </td>
        <td className="py-3 px-3 text-sm font-medium text-slate-800">
          {resultado.nombre || "(sin nombre detectado)"}
        </td>
        <td className="py-3 px-3 text-sm text-slate-500">{resultado.email || "—"}</td>
        <td className="py-3 px-3 text-sm text-slate-500">{resultado.nombre_archivo}</td>
        <td className="py-3 px-3 text-sm">
          {resultado.descartado ? (
            <span className="inline-flex items-center rounded-full bg-red-100 text-red-700 px-2.5 py-0.5 text-xs font-medium">
              Descartado
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-emerald-100 text-emerald-700 px-2.5 py-0.5 text-xs font-medium">
              Apto
            </span>
          )}
        </td>
        <td className="py-3 px-3 text-sm font-semibold text-slate-800 text-right">
          {resultado.descartado ? "—" : resultado.score_final}
        </td>
        <td className="py-3 px-3 text-slate-400 text-sm">{abierto ? "▲" : "▼"}</td>
      </tr>
      {abierto && (
        <tr className="bg-slate-50 border-b border-slate-100">
          <td colSpan={7} className="px-4 py-3">
            {resultado.motivo_descarte && (
              <p className="text-sm text-red-600 mb-2">
                Motivo de descarte: {resultado.motivo_descarte}
              </p>
            )}
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="py-1 pr-2 font-medium">Skill</th>
                  <th className="py-1 pr-2 font-medium">Tipo</th>
                  <th className="py-1 pr-2 font-medium">Peso</th>
                  <th className="py-1 pr-2 font-medium">¿Presente?</th>
                  <th className="py-1 pr-2 font-medium">Score</th>
                  <th className="py-1 font-medium">Justificación del LLM</th>
                </tr>
              </thead>
              <tbody>
                {resultado.detalle_skills.map((d, i) => (
                  <tr key={i} className="border-t border-slate-200 align-top">
                    <td className="py-1.5 pr-2 font-medium text-slate-700">{d.nombre_skill}</td>
                    <td className="py-1.5 pr-2 text-slate-500 capitalize">{d.tipo}</td>
                    <td className="py-1.5 pr-2 text-slate-500">{d.peso}</td>
                    <td className="py-1.5 pr-2">{d.presente ? "✅" : "❌"}</td>
                    <td className="py-1.5 pr-2 text-slate-700">{d.score}</td>
                    <td className="py-1.5 text-slate-500">{d.justificacion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}

export default function ResultadosRanking({ resultado }) {
  if (!resultado) return null;

  const aptos = resultado.resultados.filter((r) => !r.descartado);
  const descartados = resultado.resultados.filter((r) => r.descartado);

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-slate-800 mb-1">
        Resultados para: {resultado.titulo}
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        {aptos.length} candidato(s) apto(s) · {descartados.length} descartado(s) · click en una fila para ver el detalle
      </p>

      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full">
          <thead className="bg-slate-100">
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="py-2 px-3">#</th>
              <th className="py-2 px-3">Nombre</th>
              <th className="py-2 px-3">Email</th>
              <th className="py-2 px-3">CV</th>
              <th className="py-2 px-3">Estado</th>
              <th className="py-2 px-3 text-right">Score</th>
              <th className="py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {resultado.resultados.map((r, i) => (
              <FilaCandidato key={r.evaluacion_id} resultado={r} posicion={i + 1} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

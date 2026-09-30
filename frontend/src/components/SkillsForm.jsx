const nuevaSkill = () => ({
  id: crypto.randomUUID(),
  nombre_skill: "",
  tipo: "obligatoria",
  peso: 1,
});

export default function SkillsForm({ skills, setSkills }) {
  // Actualiza un campo de una skill en el estado
  const actualizar = (id, campo, valor) => {
    setSkills(skills.map((s) => (s.id === id ? { ...s, [campo]: valor } : s)));
  };

  const agregar = () => setSkills([...skills, nuevaSkill()]);

  const quitar = (id) => {
    if (skills.length === 1) return;
    setSkills(skills.filter((s) => s.id !== id));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-700">
          Skills requeridas
        </label>
        <button
          type="button"
          onClick={agregar}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          + Agregar skill
        </button>
      </div>

      <div className="space-y-2">
        {skills.map((skill) => (
          <div
            key={skill.id}
            className="grid grid-cols-12 gap-2 items-center bg-slate-50 border border-slate-200 rounded-lg p-2"
          >
            <input
              type="text"
              placeholder="Ej: Python, liderazgo de equipos..."
              value={skill.nombre_skill}
              onChange={(e) => actualizar(skill.id, "nombre_skill", e.target.value)}
              className="col-span-6 rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />

            <select
              value={skill.tipo}
              onChange={(e) => actualizar(skill.id, "tipo", e.target.value)}
              className="col-span-3 rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="obligatoria">Obligatoria (descarta)</option>
              <option value="deseable">Deseable (suma)</option>
            </select>

            <input
              type="number"
              min="0.1"
              step="0.1"
              title="Peso / importancia relativa"
              value={skill.peso}
              onChange={(e) => actualizar(skill.id, "peso", Number(e.target.value))}
              className="col-span-2 rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />

            <button
              type="button"
              onClick={() => quitar(skill.id)}
              disabled={skills.length === 1}
              className="col-span-1 text-slate-400 hover:text-red-500 disabled:opacity-30 disabled:hover:text-slate-400"
              title="Quitar skill"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-400">
        Peso = importancia relativa de esa skill dentro del score final (ej: Python=3 pesa el triple que Inglés=1).
      </p>
    </div>
  );
}

export { nuevaSkill };

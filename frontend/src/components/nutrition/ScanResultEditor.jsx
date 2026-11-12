import Button from "../ui/Button";
import Field, { inputClass } from "../ui/Field";
import Badge from "../ui/Badge";

const emptyItem = () => ({
  name: "",
  quantity: 1,
  unit: "serving",
  grams: "",
  kcal: 0,
  protein_g: 0,
  carbs_g: 0,
  fat_g: 0,
  fiber_g: 0,
  confidence: "medium",
  was_edited: true,
});

export function analysisToItems(analysis) {
  if (!analysis?.items?.length) return [emptyItem()];
  return analysis.items.map((item) => ({
    name: item.name,
    quantity: item.quantity,
    unit: item.unit,
    grams: item.estimated_grams,
    kcal: item.calories_kcal,
    protein_g: item.protein_g,
    carbs_g: item.carbs_g,
    fat_g: item.fat_g,
    fiber_g: item.fiber_g,
    confidence: item.confidence,
    was_edited: false,
  }));
}

export default function ScanResultEditor({ items, onChange, warnings = [] }) {
  const setItem = (index, patch) => {
    const next = items.map((row, i) => (i === index ? { ...row, ...patch, was_edited: true } : row));
    onChange(next);
  };

  const totalKcal = items.reduce((sum, row) => sum + Number(row.kcal || 0), 0);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
        AI estimate only — check portions and calories before saving. Not medical advice.
      </div>
      {warnings.map((w) => (
        <p key={w} className="text-sm text-ink-300">
          • {w}
        </p>
      ))}
      {items.map((row, index) => (
        <div key={index} className="card space-y-3 p-4">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase text-ink-400">Item {index + 1}</span>
            {row.confidence && <Badge variant="muted">{row.confidence} confidence</Badge>}
          </div>
          <Field label="Name">
            <input className={inputClass()} value={row.name} onChange={(e) => setItem(index, { name: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Field label="Qty">
              <input
                type="number"
                className={inputClass()}
                value={row.quantity}
                onChange={(e) => setItem(index, { quantity: e.target.value })}
              />
            </Field>
            <Field label="Unit">
              <input className={inputClass()} value={row.unit} onChange={(e) => setItem(index, { unit: e.target.value })} />
            </Field>
            <Field label="Grams">
              <input
                type="number"
                className={inputClass()}
                value={row.grams}
                onChange={(e) => setItem(index, { grams: e.target.value })}
              />
            </Field>
            <Field label="Calories">
              <input
                type="number"
                className={inputClass()}
                value={row.kcal}
                onChange={(e) => setItem(index, { kcal: e.target.value })}
              />
            </Field>
          </div>
        </div>
      ))}
      <Button type="button" variant="secondary" onClick={() => onChange([...items, emptyItem()])}>
        Add item
      </Button>
      <p className="text-sm font-semibold text-brand-400">Meal total: {Math.round(totalKcal)} kcal</p>
    </div>
  );
}

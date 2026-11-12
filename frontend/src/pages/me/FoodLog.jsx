import { useCallback, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Camera } from "lucide-react";
import ScanResultEditor, { analysisToItems } from "../../components/nutrition/ScanResultEditor";
import Button from "../../components/ui/Button";
import Field, { inputClass } from "../../components/ui/Field";
import Modal from "../../components/ui/Modal";
import PageHeader from "../../components/ui/PageHeader";
import { ErrorState, PageLoader } from "../../components/ui/States";
import { nutritionApi, portalApi } from "../../api";
import { useFetch } from "../../hooks/useFetch";
import { useToast } from "../../context/ToastContext";
import { MEAL_TYPES, CHART_COLORS } from "../../utils/constants";
import { downscaleImageFile } from "../../utils/image";
import { getErrorMessage } from "../../utils/errors";
import { formatDate, todayISO } from "../../utils/format";

const tooltipProps = {
  contentStyle: { background: "#16161a", border: "1px solid #2a2a32", borderRadius: 12, color: "#e4e4ea" },
};

export default function FoodLog() {
  const toast = useToast();
  const profile = useFetch(() => portalApi.profile(), []);
  const summary = useFetch(() => nutritionApi.summary({ days: 7 }), []);
  const entries = useFetch(() => nutritionApi.entries.list({ page_size: 20 }), []);

  const [mealType, setMealType] = useState("LUNCH");
  const [note, setNote] = useState("");
  const [scanning, setScanning] = useState(false);
  const [draft, setDraft] = useState(null);
  const [items, setItems] = useState([]);
  const [eatenOn, setEatenOn] = useState(todayISO());
  const [saving, setSaving] = useState(false);

  const consent = profile.data?.nutrition_consent_at;

  const acceptConsent = async () => {
    try {
      await nutritionApi.consent();
      profile.reload();
      toast.success("Disclaimer accepted. You can scan meals now.");
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const onPickPhoto = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!consent) {
      toast.error("Accept the disclaimer first.");
      return;
    }
    setScanning(true);
    try {
      const blob = await downscaleImageFile(file);
      const form = new FormData();
      form.append("image", blob, "meal.jpg");
      form.append("meal_type", mealType);
      form.append("note", note);
      const scan = await nutritionApi.scans.upload(form);
      if (scan.status === "FAILED") {
        toast.error(scan.error || "Could not analyse this photo.");
        return;
      }
      setDraft(scan);
      setItems(analysisToItems(scan.analysis));
      setEatenOn(todayISO());
    } catch (error) {
      toast.error(getErrorMessage(error, "Scan failed."));
    } finally {
      setScanning(false);
    }
  };

  const saveMeal = async () => {
    if (!draft) return;
    setSaving(true);
    try {
      const edited = items.some((row) => row.was_edited);
      await nutritionApi.scans.confirm(draft.id, {
        eaten_on: eatenOn,
        meal_type: mealType,
        edited,
        items: items.map((row) => ({
          name: row.name,
          quantity: row.quantity,
          unit: row.unit,
          grams: row.grams === "" ? null : row.grams,
          kcal: row.kcal,
          protein_g: row.protein_g,
          carbs_g: row.carbs_g,
          fat_g: row.fat_g,
          fiber_g: row.fiber_g,
          confidence: row.confidence,
          was_edited: row.was_edited,
        })),
      });
      toast.success("Meal saved.");
      setDraft(null);
      entries.reload();
      summary.reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const closeDraft = useCallback(() => setDraft(null), []);

  if (profile.loading && !profile.data) return <PageLoader />;
  if (profile.error && !profile.data) return <ErrorState message={profile.error} onRetry={profile.reload} />;

  const chartData = (summary.data?.daily ?? []).map((row) => ({
    label: new Date(row.date).toLocaleDateString("en-GB", { weekday: "short", day: "numeric" }),
    kcal: row.kcal,
  }));

  return (
    <div>
      <PageHeader title="Food log" subtitle="Photo scan or review past meals" />

      {!consent && (
        <div className="card mb-6 space-y-3 p-5">
          <h2 className="font-display text-lg font-bold uppercase">Food photo disclaimer</h2>
          <p className="text-sm text-ink-300">
            Photos are sent to an AI model for calorie estimates only. Results are not medical advice. Images are not
            stored on the server after analysis.
          </p>
          <Button onClick={acceptConsent}>I understand — enable scanning</Button>
        </div>
      )}

      <section className="card mb-6 space-y-4 p-5">
        <h2 className="font-display text-lg font-bold uppercase">Scan a meal</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Meal type">
            <select className={inputClass()} value={mealType} onChange={(e) => setMealType(e.target.value)}>
              {MEAL_TYPES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Note (optional)" hint="e.g. home-made, 2 rotis, less oil">
            <input className={inputClass()} value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} />
          </Field>
        </div>
        <label className={`btn btn-primary inline-flex cursor-pointer gap-2 ${!consent ? "pointer-events-none opacity-50" : ""}`}>
          <Camera className="h-4 w-4" />
          {scanning ? "Analysing…" : "Take or upload photo"}
          <input type="file" accept="image/*" capture="environment" className="hidden" disabled={!consent || scanning} onChange={onPickPhoto} />
        </label>
      </section>

      <section className="card mb-6 p-5">
        <h2 className="mb-4 font-display text-lg font-bold uppercase">Last 7 days</h2>
        {chartData.length ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a32" />
              <XAxis dataKey="label" tick={{ fill: "#8a8a96", fontSize: 11 }} />
              <YAxis tick={{ fill: "#8a8a96", fontSize: 11 }} />
              <Tooltip {...tooltipProps} />
              <Bar dataKey="kcal" fill={CHART_COLORS[0]} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-ink-300">No meals logged yet.</p>
        )}
      </section>

      <section className="card p-5">
        <h2 className="mb-4 font-display text-lg font-bold uppercase">Recent meals</h2>
        <ul className="divide-y divide-ink-700">
          {(entries.data?.results ?? []).map((entry) => (
            <li key={entry.id} className="flex justify-between gap-3 py-3 text-sm">
              <div>
                <p className="font-semibold text-ink-100">{formatDate(entry.eaten_on)} · {entry.meal_type}</p>
                <p className="text-ink-400">
                  {entry.items?.map((i) => i.name).join(", ") || "—"}
                </p>
              </div>
              <span className="font-semibold text-brand-400">{Math.round(entry.total_kcal)} kcal</span>
            </li>
          ))}
        </ul>
      </section>

      {draft && (
        <Modal
          size="lg"
          title="Review meal"
          subtitle={draft.status === "NEEDS_REVIEW" ? "Please double-check these estimates" : "Confirm and save"}
          onClose={saving ? undefined : closeDraft}
          footer={
            <>
              <Button variant="secondary" onClick={closeDraft} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={saveMeal} loading={saving}>
                Save meal
              </Button>
            </>
          }
        >
          <Field label="Date eaten" className="mb-4">
            <input type="date" className={inputClass()} value={eatenOn} onChange={(e) => setEatenOn(e.target.value)} max={todayISO()} />
          </Field>
          <ScanResultEditor
            items={items}
            onChange={setItems}
            warnings={draft.analysis?.warnings ?? []}
          />
        </Modal>
      )}
    </div>
  );
}

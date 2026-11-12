import PageHeader from "../../components/ui/PageHeader";
import { ErrorState, PageLoader } from "../../components/ui/States";
import { portalApi } from "../../api";
import { useFetch } from "../../hooks/useFetch";
import { formatDate } from "../../utils/format";

export default function MyVisits() {
  const { data, loading, error, reload } = useFetch(() => portalApi.attendance({ page_size: 30 }), []);

  if (loading && !data) return <PageLoader />;
  if (error && !data) return <ErrorState message={error} onRetry={reload} />;

  const rows = data.results ?? [];

  return (
    <div>
      <PageHeader title="Gym visits" subtitle="Your check-in history" />
      <ul className="card divide-y divide-ink-700">
        {rows.map((row) => (
          <li key={row.id} className="flex justify-between px-4 py-3 text-sm">
            <span>{formatDate(row.date)}</span>
            <span className="text-ink-300">
              {row.check_in}
              {row.check_out ? ` → ${row.check_out}` : " (still inside)"}
            </span>
          </li>
        ))}
        {!rows.length && <li className="px-4 py-8 text-center text-ink-400">No visits yet.</li>}
      </ul>
    </div>
  );
}

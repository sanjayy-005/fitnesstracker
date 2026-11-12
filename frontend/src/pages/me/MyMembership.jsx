import PageHeader from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/Badge";
import { ErrorState, PageLoader } from "../../components/ui/States";
import { portalApi } from "../../api";
import { useFetch } from "../../hooks/useFetch";
import { formatCurrency, formatDate, formatDaysLeft } from "../../utils/format";

export default function MyMembership() {
  const { data, loading, error, reload } = useFetch(() => portalApi.memberships(), []);

  if (loading && !data) return <PageLoader />;
  if (error && !data) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div>
      <PageHeader title="My memberships" subtitle="Plans you have purchased" />
      <ul className="space-y-3">
        {data.map((row) => (
          <li key={row.id} className="card flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="font-semibold text-ink-100">{row.plan_name}</p>
              <p className="text-sm text-ink-300">
                {formatDate(row.start_date)} → {formatDate(row.end_date)} · {formatDaysLeft(row.days_left)}
              </p>
            </div>
            <div className="text-right">
              <StatusBadge status={row.status} />
              <p className="mt-1 text-sm text-ink-400">{formatCurrency(row.price)}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

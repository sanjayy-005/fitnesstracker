import { Link } from "react-router-dom";
import { Apple, CalendarCheck, CreditCard } from "lucide-react";
import { StatusBadge } from "../../components/ui/Badge";
import PageHeader from "../../components/ui/PageHeader";
import StatCard from "../../components/ui/StatCard";
import { ErrorState, PageLoader } from "../../components/ui/States";
import { nutritionApi, portalApi } from "../../api";
import { useFetch } from "../../hooks/useFetch";
import { formatDate, formatDaysLeft } from "../../utils/format";

export default function MyHome() {
  const profile = useFetch(() => portalApi.profile(), []);
  const summary = useFetch(() => nutritionApi.summary({ days: 7 }), []);

  if (profile.loading && !profile.data) return <PageLoader />;
  if (profile.error && !profile.data) return <ErrorState message={profile.error} onRetry={profile.reload} />;

  const { membership } = profile.data;
  const todayKcal = summary.data?.today_kcal ?? 0;

  return (
    <div>
      <PageHeader
        title={`Hi, ${profile.data.full_name.split(" ")[0]}`}
        subtitle={`Member ${profile.data.member_code} · joined ${formatDate(profile.data.joined_date)}`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Calories today" value={Math.round(todayKcal)} icon={Apple} hint="From your food log" />
        <StatCard
          label="Membership"
          value={membership?.plan_name ?? "None"}
          icon={CreditCard}
          hint={
            membership
              ? `Ends ${formatDate(membership.end_date)} (${formatDaysLeft(membership.days_left)})`
              : "Ask the desk to renew"
          }
        />
        <StatCard
          label="Trainer"
          value={profile.data.trainer_name ?? "Not assigned"}
          icon={CalendarCheck}
        />
      </div>

      {membership && (
        <div className="card mt-6 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-xl font-bold uppercase tracking-wide">Current plan</h2>
              <p className="text-sm text-ink-300">{membership.plan_name}</p>
            </div>
            <StatusBadge status={membership.status} />
          </div>
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/me/food" className="btn btn-primary">
          Log a meal
        </Link>
        <Link to="/me/membership" className="btn btn-secondary">
          Membership history
        </Link>
        <Link to="/me/visits" className="btn btn-secondary">
          Visit history
        </Link>
      </div>

      {!profile.data.nutrition_consent_at && (
        <p className="mt-4 text-sm text-amber-400">
          Accept the food-photo disclaimer on the Food log page before using AI calorie scan.
        </p>
      )}
    </div>
  );
}

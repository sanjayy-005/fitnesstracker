import { Link, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Attendance from "./pages/Attendance";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Members from "./pages/Members";
import Memberships from "./pages/Memberships";
import Payments from "./pages/Payments";
import Plans from "./pages/Plans";
import Trainers from "./pages/Trainers";
import Users from "./pages/Users";
import FoodLog from "./pages/me/FoodLog";
import MyHome from "./pages/me/MyHome";
import MyMembership from "./pages/me/MyMembership";
import MyVisits from "./pages/me/MyVisits";
import { ADMIN_ONLY, ADMIN_STAFF, MEMBER_ONLY, ROLES, STAFF_ROLES } from "./utils/constants";
import { useAuth } from "./context/AuthContext";

function HomeRedirect() {
  const { user } = useAuth();
  if (user?.role === ROLES.MEMBER) return <Navigate to="/me" replace />;
  return <Dashboard />;
}

function NotFound() {
  return (
    <div className="flex flex-col items-center gap-3 py-24 text-center">
      <p className="font-display text-8xl font-bold text-brand-500">404</p>
      <h1 className="font-display text-3xl font-bold uppercase tracking-wide">Page not found</h1>
      <Link to="/" className="btn btn-primary mt-2">
        Back to dashboard
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomeRedirect />} />

        <Route
          path="me"
          element={
            <ProtectedRoute roles={MEMBER_ONLY}>
              <MyHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="me/food"
          element={
            <ProtectedRoute roles={MEMBER_ONLY}>
              <FoodLog />
            </ProtectedRoute>
          }
        />
        <Route
          path="me/membership"
          element={
            <ProtectedRoute roles={MEMBER_ONLY}>
              <MyMembership />
            </ProtectedRoute>
          }
        />
        <Route
          path="me/visits"
          element={
            <ProtectedRoute roles={MEMBER_ONLY}>
              <MyVisits />
            </ProtectedRoute>
          }
        />

        <Route
          path="members"
          element={
            <ProtectedRoute roles={STAFF_ROLES}>
              <Members />
            </ProtectedRoute>
          }
        />
        <Route
          path="trainers"
          element={
            <ProtectedRoute roles={ADMIN_STAFF}>
              <Trainers />
            </ProtectedRoute>
          }
        />
        <Route
          path="plans"
          element={
            <ProtectedRoute roles={STAFF_ROLES}>
              <Plans />
            </ProtectedRoute>
          }
        />
        <Route
          path="memberships"
          element={
            <ProtectedRoute roles={STAFF_ROLES}>
              <Memberships />
            </ProtectedRoute>
          }
        />
        <Route
          path="payments"
          element={
            <ProtectedRoute roles={ADMIN_STAFF}>
              <Payments />
            </ProtectedRoute>
          }
        />
        <Route
          path="attendance"
          element={
            <ProtectedRoute roles={STAFF_ROLES}>
              <Attendance />
            </ProtectedRoute>
          }
        />
        <Route
          path="users"
          element={
            <ProtectedRoute roles={ADMIN_ONLY}>
              <Users />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

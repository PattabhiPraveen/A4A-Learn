import {
  Route,
  Routes,
} from "react-router-dom";

import ProtectedRoute from
  "../components/auth/ProtectedRoute";

import AppShell from
  "../components/layout/AppShell";

import DashboardPage from
  "../pages/DashboardPage";

import HomePage from
  "../pages/HomePage";

import ISLPracticePage from
  "../pages/ISLPracticePage";

import LearnPage from
  "../pages/LearnPage";

import LoginPage from
  "../pages/LoginPage";

import NotFoundPage from
  "../pages/NotFoundPage";

import ProgressPage from
  "../pages/ProgressPage";

import ReviewsPage from
  "../pages/ReviewsPage";

import TutorPage from
  "../pages/TutorPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/"
          element={<HomePage />}
        />

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route element={<ProtectedRoute />}>
          <Route
            path="/dashboard"
            element={<DashboardPage />}
          />

          <Route
            path="/learn"
            element={<LearnPage />}
          />

          <Route
            path="/tutor"
            element={<TutorPage />}
          />

          <Route
            path="/isl"
            element={<ISLPracticePage />}
          />

          <Route
            path="/progress"
            element={<ProgressPage />}
          />

          <Route
            path="/reviews"
            element={<ReviewsPage />}
          />
        </Route>

        <Route
          path="*"
          element={<NotFoundPage />}
        />
      </Route>
    </Routes>
  );
}
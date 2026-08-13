import { Routes, Route, Navigate } from "react-router-dom";

import { AuthPage } from "../features/auth/AuthPage";
import { RegisterPage } from "../features/auth/RegisterPage";

import ProtectedRoutes from "./ProtectedRoutes";
import PublicRoutes from "./PublicRoutes";

import DashboardPage from "../pages/DashboardPage";
import ResumePage from "../pages/ResumePage";
import InterviewPage from "../pages/InterviewPage";
import AnalyticsPage from "../pages/AnalyticsPage";
import ReportsPage from "../pages/ReportsPage";
import MemoryPage from "../pages/MemoryPage";
import CareerPage from "../pages/CareerPage";
import AdminPage from "../pages/AdminPage";
import SettingsPage from "../pages/SettingsPage";

export default function AppRoutes() {
    return (
        <Routes>

            <Route element={<PublicRoutes />}>
                <Route path="/login" element={<AuthPage />} />
                <Route path="/register" element={<RegisterPage />} />
            </Route>

            <Route element={<ProtectedRoutes />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/resumes" element={<ResumePage />} />
                <Route path="/interviews" element={<InterviewPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/reports/:interviewId" element={<ReportsPage />} />
                <Route path="/memory" element={<MemoryPage />} />
                <Route path="/career" element={<CareerPage />} />
                <Route path="/job-descriptions" element={<CareerPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="/settings" element={<SettingsPage />} />
            </Route>

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />

        </Routes>
    );
}
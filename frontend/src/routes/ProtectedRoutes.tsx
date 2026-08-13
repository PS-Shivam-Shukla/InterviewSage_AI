import { Navigate, Outlet } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoutes() {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return (
        <AppLayout>
            <Outlet />
        </AppLayout>
    );
}
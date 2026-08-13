import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

export default function PublicRoutes() {
    const { isAuthenticated } = useAuth();

    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />;
    }

    return <Outlet />;
}
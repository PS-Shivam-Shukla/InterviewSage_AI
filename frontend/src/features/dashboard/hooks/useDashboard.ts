import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "../services/dashboard.service";
import { useAuth } from "../../../hooks/useAuth";

export function useDashboard() {
    const { user } = useAuth();
    const userId = user?.id;

    const summary = useQuery({
        queryKey: ["dashboard-summary", userId],
        queryFn: dashboardService.getSummary,
        enabled: !!userId,
    });

    const trends = useQuery({
        queryKey: ["dashboard-trends", userId],
        queryFn: dashboardService.getTrends,
        enabled: !!userId,
    });

    const competencies = useQuery({
        queryKey: ["dashboard-competencies", userId],
        queryFn: dashboardService.getCompetencies,
        enabled: !!userId,
    });

    return {
        summary,
        trends,
        competencies
    };
}
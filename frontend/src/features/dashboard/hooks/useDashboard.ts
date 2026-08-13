import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "../services/dashboard.service";

export function useDashboard() {

    const summary = useQuery({
        queryKey: ["dashboard-summary"],
        queryFn: dashboardService.getSummary
    });

    const trends = useQuery({
        queryKey: ["dashboard-trends"],
        queryFn: dashboardService.getTrends
    });

    const competencies = useQuery({
        queryKey: ["dashboard-competencies"],
        queryFn: dashboardService.getCompetencies
    });

    return {
        summary,
        trends,
        competencies
    };

}
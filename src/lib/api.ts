export interface OverviewStat {
  name: string;
  value: string;
  trend: string;
  icon: string;
  tone: string;
}

export interface OverviewApp {
  id: string;
  name: string;
  description: string;
  status: string;
  icon: string;
}

export interface OverviewWorkflow {
  id: string;
  name: string;
  status: string;
  runs_today: number;
  latency_ms: number;
}

export interface OverviewActivity {
  id: string;
  type: string;
  name: string;
  action: string;
  time: string;
}

export interface OverviewData {
  product: {
    name: string;
    tagline: string;
  };
  stats: OverviewStat[];
  apps: OverviewApp[];
  workflows: OverviewWorkflow[];
  activities: OverviewActivity[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export const apiRoutes = {
  overview: `${API_BASE_URL}/api/overview`,
  chat: `${API_BASE_URL}/api/chat`,
};

export async function getOverview(): Promise<OverviewData> {
  const response = await fetch(apiRoutes.overview);

  if (!response.ok) {
    throw new Error("Failed to load overview data from the backend.");
  }

  return (await response.json()) as OverviewData;
}

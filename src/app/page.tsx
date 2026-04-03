import { AppOverview } from "@/components/AppOverview";
import { DashboardLayout } from "@/components/DashboardLayout";

export default function Home() {
  return (
    <DashboardLayout>
      <AppOverview />
    </DashboardLayout>
  );
}

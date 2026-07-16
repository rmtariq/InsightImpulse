import { Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { PrnMonitoringPage } from "@/features/prn-monitoring/pages/PrnMonitoringPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<PrnMonitoringPage />} />
      </Route>
    </Routes>
  );
}

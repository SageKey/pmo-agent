import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ExecutiveSummary } from "@/pages/ExecutiveSummary";
import { Portfolio } from "@/pages/Portfolio";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { Capacity } from "@/pages/Capacity";
import { TeamRoster } from "@/pages/TeamRoster";
import { Timeline } from "@/pages/Timeline";
import { Financials } from "@/pages/Financials";
import { Timesheets } from "@/pages/Timesheets";
import { AIAssistant } from "@/pages/AIAssistant";
import { Admin } from "@/pages/Admin";
import { Planning } from "@/pages/Planning";
import { Initiatives } from "@/pages/Initiatives";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/executive" replace /> },
      { path: "executive", element: <ExecutiveSummary /> },
      { path: "initiatives", element: <Initiatives /> },
      { path: "portfolio", element: <Portfolio /> },
      { path: "portfolio/:projectId", element: <ProjectDetail /> },
      { path: "capacity", element: <Capacity /> },
      { path: "timeline", element: <Timeline /> },
      { path: "financials", element: <Financials /> },
      { path: "timesheets", element: <Timesheets /> },
      { path: "roster", element: <TeamRoster /> },
      { path: "planning", element: <Planning /> },
      { path: "assistant", element: <AIAssistant /> },
      { path: "admin", element: <Admin /> },
    ],
  },
]);

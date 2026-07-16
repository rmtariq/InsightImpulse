import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AppRoutes } from "./routes";
import "./index.css";

const savedTheme = localStorage.getItem("prn-dashboard-theme");
document.documentElement.classList.toggle("dark", savedTheme !== "light");

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter basename="/insightpulse/prn-monitoring">
      <AppRoutes />
    </BrowserRouter>
  </StrictMode>,
);

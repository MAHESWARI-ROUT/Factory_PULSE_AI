import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import ExecutiveDashboard from "./pages/ExecutiveDashboard.jsx";
import RiskDashboard from "./pages/RiskDashboard.jsx";
import MachineList from "./pages/MachineList.jsx";
import MachineDetail from "./pages/MachineDetail.jsx";
import MaintenanceReports from "./pages/MaintenanceReports.jsx";
import ChatAssistant from "./pages/ChatAssistant.jsx";
import BatchPredict from "./pages/BatchPredict.jsx";

export default function App() {
  return (
    <div className="flex min-h-screen bg-base-950">
      <Sidebar />
      <main className="flex-1 px-8 py-7 max-w-[1400px]">
        <Routes>
          <Route path="/" element={<ExecutiveDashboard />} />
          <Route path="/risk" element={<RiskDashboard />} />
          <Route path="/machines" element={<MachineList />} />
          <Route path="/machines/:machineId" element={<MachineDetail />} />
          <Route path="/reports" element={<MaintenanceReports />} />
          <Route path="/chat" element={<ChatAssistant />} />
          <Route path="/batch-predict" element={<BatchPredict />} />
        </Routes>
      </main>
    </div>
  );
}

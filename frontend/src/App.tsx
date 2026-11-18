import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Drawings from "./pages/Drawings";
import Upload from "./pages/Upload";
import Reconciliation from "./pages/Reconciliation";
import AgentChat from "./pages/AgentChat";
import Architecture from "./pages/Architecture";
import SidebarUploadProgress from "./components/SidebarUploadProgress";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <div className="sidebar">
          <div className="logo">
            <div className="logo-brand">Material360</div>
          </div>
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} end>
            Drawings
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            Upload
          </NavLink>
          <div className="nav-sep" />
          <NavLink to="/reconciliation" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            BOM Reconciliation
          </NavLink>
          <div className="nav-sep" />
          <NavLink to="/chat" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            Agent Chat
          </NavLink>
          <div className="nav-sep" />
          <NavLink to="/architecture" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            Architecture
          </NavLink>
          <div className="sidebar-bottom">
            <SidebarUploadProgress />
            <div className="sidebar-footer">
              Snowflake Cortex AI<br />
              SNOWFLAKE_INTELLIGENCE
            </div>
          </div>
        </div>
        <div className="main">
          <Routes>
            <Route path="/" element={<Drawings />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/reconciliation" element={<Reconciliation />} />
            <Route path="/chat" element={<AgentChat />} />
            <Route path="/architecture" element={<Architecture />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SiteProvider } from './context/SiteContext';
import { WebSocketProvider } from './context/WebSocketContext';

import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { Login } from './pages/Login';
import { StationDashboard } from './pages/StationDashboard';
import { CentralCommandDashboard } from './pages/CentralCommandDashboard';
import { VehiclesPage } from './pages/VehiclesPage';
import { JourneyDetailPage } from './pages/JourneyDetailPage';
import { QueuePage } from './pages/QueuePage';
import { BaysPage } from './pages/BaysPage';
import { AlertsPage } from './pages/AlertsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { CamerasPage } from './pages/CamerasPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { SiteManagementPage } from './pages/SiteManagementPage';
import { UserManagementPage } from './pages/UserManagementPage';

const ProtectedLayout = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  return (
    <SiteProvider>
      <WebSocketProvider>
        <div className="app-layout">
          <Sidebar />
          <div className="content-wrapper">
            <Navbar />
            <main className="main-content">
              <Routes>
                <Route path="/station-dashboard" element={<StationDashboard />} />
                <Route path="/central-command" element={<CentralCommandDashboard />} />
                <Route path="/journeys" element={<VehiclesPage />} />
                <Route path="/journeys/:id" element={<JourneyDetailPage />} />
                <Route path="/queue" element={<QueuePage />} />
                <Route path="/bays" element={<BaysPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/audit" element={<AuditLogsPage />} />
                <Route path="/cameras" element={<CamerasPage />} />
                <Route path="/simulator" element={<SimulatorPage />} />
                <Route path="/sites-manage" element={<SiteManagementPage />} />
                <Route path="/users-manage" element={<UserManagementPage />} />
                <Route path="*" element={<Navigate to="/station-dashboard" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </WebSocketProvider>
    </SiteProvider>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

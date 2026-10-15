import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { Radio, MapPin, LogOut, Bell, User as UserIcon, ShieldAlert } from 'lucide-react';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const { sites, selectedSiteId, setSelectedSiteId } = useSite();
  const { isConnected } = useWebSocket();
  const location = useLocation();
  const [showNotifications, setShowNotifications] = useState(false);

  const routeTitleMap = {
    '/station-dashboard': 'Station Operations Dashboard',
    '/central-command': 'Central Command Network Overview',
    '/journeys': 'Active Site Vehicle Journeys',
    '/queue': 'Live Site Queue Management',
    '/bays': 'Inspection Bay Allocation & Status',
    '/alerts': 'Alerts & Operational Incidents',
    '/cameras': 'ANPR Camera Feed & Device Health',
    '/simulator': 'Operational Event Simulator',
    '/audit': 'Immutable Audit Logs & Compliance Traceability',
    '/sites-manage': 'Multi-Site Terminal Directory',
    '/users-manage': 'RBAC User & Permission Directory',
  };

  const pageTitle = routeTitleMap[location.pathname] || 'Operational Console';

  return (
    <header className="top-navbar">
      {/* Page Title & Breadcrumb Context */}
      <div>
        <h2 className="text-base font-bold text-slate-100">{pageTitle}</h2>
        <p className="text-[11px] text-slate-400 font-mono">Real-time Compliance & Inspection Engine</p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Site Selector */}
        <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
          <MapPin className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-400">STATION:</span>
          <select
            value={selectedSiteId}
            onChange={(e) => setSelectedSiteId(Number(e.target.value))}
            className="bg-transparent text-xs font-bold text-slate-100 focus:outline-none cursor-pointer"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id} className="bg-slate-900 text-slate-200">
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </div>

        {/* Live WS Connection Pill */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono">
          <Radio className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400 live-pulse' : 'text-rose-500'}`} />
          <span className={isConnected ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
            {isConnected ? 'LIVE WEBSOCKET' : 'RECONNECTING'}
          </span>
        </div>

        {/* Notifications Icon Pill */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg relative"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full animate-ping" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-3 z-50">
              <div className="flex-between pb-2 border-b border-slate-800 text-xs font-bold text-slate-200">
                <span>System Notifications</span>
                <span className="text-rose-400">Live Feed</span>
              </div>
              <div className="py-3 text-xs text-slate-400 space-y-2">
                <div className="p-2 bg-slate-800/80 rounded border border-slate-700 flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-slate-200">ANPR Verification Active</div>
                    <div className="text-[10px] text-slate-400">Real-time socket connected for active site.</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Info & Logout */}
        {user && (
          <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-slate-200">{user.full_name}</span>
                <span className="text-[10px] font-bold text-indigo-400 uppercase font-mono">{user.role}</span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { Radio, MapPin, LogOut, Bell, User as UserIcon, ShieldAlert, Menu } from 'lucide-react';

export const Navbar = ({ onToggleMobileMenu }) => {
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
      {/* Mobile Hamburger & Page Title Context */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          onClick={onToggleMobileMenu}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 lg:hidden shrink-0 border border-slate-700/80 bg-slate-850"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <h2 className="text-sm sm:text-base font-bold text-slate-100 truncate max-w-[130px] xs:max-w-[180px] sm:max-w-xs md:max-w-md">
            {pageTitle}
          </h2>
          <p className="hidden sm:block text-[10px] sm:text-[11px] text-slate-400 font-mono truncate">
            Real-time Compliance & Inspection Engine
          </p>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
        {/* Site Selector */}
        <div className="flex items-center gap-1 sm:gap-2 bg-slate-800/80 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg border border-slate-700">
          <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="hidden md:inline text-xs font-semibold text-slate-400">STATION:</span>
          <select
            value={selectedSiteId}
            onChange={(e) => setSelectedSiteId(Number(e.target.value))}
            className="bg-transparent text-[11px] sm:text-xs font-bold text-slate-100 focus:outline-none cursor-pointer max-w-[95px] sm:max-w-[140px] truncate"
            aria-label="Select Station"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id} className="bg-slate-900 text-slate-200">
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </div>

        {/* Live WS Connection Pill */}
        <div
          className="flex items-center gap-1.5 px-2 sm:px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-[10px] sm:text-xs font-mono"
          title={isConnected ? 'Live WebSocket Connected' : 'Reconnecting WebSocket'}
        >
          <Radio className={`w-3 h-3 sm:w-3.5 sm:h-3.5 ${isConnected ? 'text-emerald-400 live-pulse' : 'text-rose-500'}`} />
          <span className={`hidden sm:inline ${isConnected ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}`}>
            {isConnected ? 'LIVE WEBSOCKET' : 'RECONNECTING'}
          </span>
        </div>

        {/* Notifications Icon Pill */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-1.5 sm:p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg relative"
            title="Notifications"
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full animate-ping" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 max-w-[calc(100vw-2rem)] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-3 z-50">
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
          <div className="flex items-center gap-1.5 sm:gap-3 border-l border-slate-800 pl-2 sm:pl-3">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <div className="p-1 sm:p-1.5 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30 shrink-0">
                <UserIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </div>
              <div className="hidden md:flex flex-col">
                <span className="text-xs font-bold text-slate-200 truncate max-w-[100px]">{user.full_name}</span>
                <span className="text-[10px] font-bold text-indigo-400 uppercase font-mono">{user.role}</span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 sm:p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
              title="Logout"
              aria-label="Log out"
            >
              <LogOut className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

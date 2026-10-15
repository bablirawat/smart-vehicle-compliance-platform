import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSite } from '../context/SiteContext';
import {
  LayoutDashboard,
  Globe,
  Truck,
  ListOrdered,
  Grid,
  Bell,
  FileCheck2,
  Camera,
  Cpu,
  Building2,
  Users,
  ShieldCheck,
  MapPin,
  UserCheck
} from 'lucide-react';

export const Sidebar = () => {
  const { user } = useAuth();
  const { selectedSite } = useSite();

  const navItems = [
    { label: 'Dashboard', path: '/station-dashboard', icon: LayoutDashboard, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Central Command', path: '/central-command', icon: Globe, roles: ['Regional Manager', 'Site Manager', 'Auditor', 'Admin'] },
    { label: 'Active Journeys', path: '/journeys', icon: Truck, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Live Queue', path: '/queue', icon: ListOrdered, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Bay Management', path: '/bays', icon: Grid, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Alerts', path: '/alerts', icon: Bell, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Camera Status', path: '/cameras', icon: Camera, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Admin'] },
    { label: 'Event Simulator', path: '/simulator', icon: Cpu, roles: ['Operator', 'Site Manager', 'Regional Manager', 'Auditor', 'Admin'] },
    { label: 'Audit Logs', path: '/audit', icon: FileCheck2, roles: ['Auditor', 'Site Manager', 'Regional Manager', 'Admin'] },
    { label: 'Site Directory', path: '/sites-manage', icon: Building2, roles: ['Regional Manager', 'Admin'] },
    { label: 'User Management', path: '/users-manage', icon: Users, roles: ['Admin'] },
  ];

  const visibleItems = navItems.filter((item) => !user || item.roles.includes(user.role));

  return (
    <aside className="sidebar-container">
      <div>
        {/* Brand Logo */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3">
          <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30 text-blue-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-slate-100 tracking-wide">SMART VEHICLE</h1>
            <p className="text-[10px] text-slate-400 font-mono">Compliance Platform</p>
          </div>
        </div>

        {/* Nav Links List */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            COMMAND CENTER
          </div>
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'nav-link-active' : ''}`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom User Info Pill */}
      {user && (
        <div className="p-3 border-t border-slate-800 bg-slate-900/60 m-3 rounded-xl">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg border border-indigo-500/30">
              <UserCheck className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-slate-200 truncate">{user.full_name}</div>
              <div className="text-[10px] font-bold text-indigo-400 font-mono uppercase tracking-wider">{user.role}</div>
              <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5 truncate">
                <MapPin className="w-3 h-3 text-cyan-400" />
                <span>{selectedSite?.name || 'All Stations'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

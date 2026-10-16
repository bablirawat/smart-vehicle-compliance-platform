import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { Building2, RefreshCw } from 'lucide-react';

export const SiteManagementPage = () => {
  const [sites, setSites] = useState([]);

  const fetchSites = async () => {
    try {
      const res = await api.get('/sites');
      setSites(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 flex items-center gap-2">
            <Building2 className="w-5 h-5 sm:w-6 sm:h-6 text-cyan-400 shrink-0" />
            <span className="truncate">Multi-Site Directory & Configuration</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Regional Logistics Terminals & Station Setup</p>
        </div>
        <button onClick={fetchSites} className="btn-action btn-secondary-style btn-sm-size self-start sm:self-auto" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {sites.map((s) => (
          <div key={s.id} className="card space-y-3">
            <div className="flex-between">
              <div>
                <h3 className="font-bold text-slate-100 text-base">{s.name}</h3>
                <p className="text-xs text-slate-400 font-mono">Code: {s.code}</p>
              </div>
              <StatusBadge status={s.status} />
            </div>
            <p className="text-xs text-slate-300">Location: {s.location}</p>
            <p className="text-xs text-slate-400 font-mono">Max Queue Capacity: {s.max_queue_capacity} vehicles</p>
          </div>
        ))}
      </div>
    </div>
  );
};

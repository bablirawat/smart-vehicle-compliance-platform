import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';
import { KPICard } from '../components/KPICard';
import { StatusBadge } from '../components/StatusBadge';
import { Globe, Building2, Truck, ListOrdered, ShieldAlert, Activity, RefreshCw } from 'lucide-react';

export const CentralCommandDashboard = () => {
  const [data, setData] = useState(null);
  const [timeframe, setTimeframe] = useState('TODAY');
  const [loading, setLoading] = useState(true);
  const { lastEvent } = useWebSocket();

  const loadCentralData = async () => {
    try {
      const res = await api.get('/dashboard/central', { params: { timeframe } });
      setData(res.data);
    } catch (err) {
      console.error('Failed to load central command data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCentralData();
  }, [timeframe]);

  useEffect(() => {
    if (lastEvent) {
      loadCentralData();
    }
  }, [lastEvent]);

  if (loading || !data) {
    return <div className="p-8 text-slate-400 font-mono text-sm">Loading Central Command Overview...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Globe className="w-6 h-6 text-indigo-400" />
            <span>Central Command Dashboard</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Multi-Site Network Compliance Monitoring & Resource Aggregation</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="form-select text-xs py-1.5"
          >
            <option value="TODAY">Today</option>
            <option value="LAST 24 HOURS">Last 24 Hours</option>
            <option value="LAST 7 DAYS">Last 7 Days</option>
          </select>
          <button onClick={loadCentralData} className="btn btn-secondary btn-sm">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Network KPIs */}
      <div className="kpi-grid">
        <KPICard title="Total Sites Network" value={`${data.online_sites} / ${data.total_sites}`} icon={Building2} color="emerald" subtext={`${data.sites_with_alerts} sites with alerts`} />
        <KPICard title="Network Active Vehicles" value={data.total_active_vehicles} icon={Truck} color="blue" subtext="Across all stations" />
        <KPICard title="Network Queue Length" value={data.network_queue_length} icon={ListOrdered} color="amber" subtext="Waiting in queue" />
        <KPICard title="Avg Network Wait" value={`${data.avg_network_wait_time_minutes} min`} icon={Activity} color="cyan" subtext="Average waiting time" />
        <KPICard title="Network Utilization" value={`${data.network_resource_utilization_percent}%`} icon={Activity} color="purple" subtext="Total bay capacity" />
        <KPICard title="Critical Alerts" value={data.critical_alerts_count} icon={ShieldAlert} color="rose" subtext="Requires executive review" />
      </div>

      {/* Multi-Site Comparison Grid */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Building2 className="w-5 h-5 text-cyan-400" />
            <span>Multi-Site Operational Overview & Comparison</span>
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.site_summaries.map((site) => (
            <div
              key={site.site_id}
              className="p-4 bg-slate-800/60 rounded-lg border border-slate-700/80 space-y-3 hover:border-slate-600 transition-all"
            >
              <div className="flex-between">
                <div>
                  <h4 className="font-bold text-slate-100 text-sm">{site.site_name}</h4>
                  <p className="text-xs text-slate-400 font-mono">{site.site_code} • {site.location}</p>
                </div>
                <StatusBadge status={site.status} />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-700/60">
                <div className="bg-slate-900/60 p-2 rounded">
                  <div className="text-slate-400">Active Vehicles</div>
                  <div className="text-base font-bold text-blue-400 mt-0.5">{site.active_vehicles}</div>
                </div>
                <div className="bg-slate-900/60 p-2 rounded">
                  <div className="text-slate-400">Queue Length</div>
                  <div className="text-base font-bold text-amber-400 mt-0.5">{site.queue_length}</div>
                </div>
                <div className="bg-slate-900/60 p-2 rounded">
                  <div className="text-slate-400">Bay Occupancy</div>
                  <div className="text-base font-bold text-emerald-400 mt-0.5">{site.occupied_bays} / {site.total_bays}</div>
                </div>
                <div className="bg-slate-900/60 p-2 rounded">
                  <div className="text-slate-400">Open Alerts</div>
                  <div className={`text-base font-bold mt-0.5 ${site.open_alerts > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                    {site.open_alerts}
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-700/60 text-xs flex-between text-slate-400">
                <span>Resource Utilization:</span>
                <span className="font-semibold text-slate-200">{site.resource_utilization}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

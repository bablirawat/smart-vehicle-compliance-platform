import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { StatusBadge } from '../components/StatusBadge';
import { Grid, RefreshCw, CheckCircle2, ShieldAlert } from 'lucide-react';

export const BaysPage = () => {
  const { selectedSite, selectedSiteId } = useSite();
  const { lastEvent } = useWebSocket();
  const [bays, setBays] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBays = async () => {
    if (!selectedSiteId) return;
    try {
      const res = await api.get('/bays', { params: { site_id: selectedSiteId } });
      setBays(res.data);
    } catch (err) {
      console.error('Failed to fetch bays:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBays();
  }, [selectedSiteId]);

  useEffect(() => {
    if (lastEvent) fetchBays();
  }, [lastEvent]);

  const handleReleaseBay = async (bayId) => {
    try {
      await api.post(`/bays/${bayId}/release`);
      fetchBays();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to release bay');
    }
  };

  const handleUpdateStatus = async (bayId, status) => {
    try {
      await api.post(`/bays/${bayId}/status`, { status });
      fetchBays();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update bay status');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Grid className="w-6 h-6 text-emerald-400" />
            <span>Inspection Bay Management - {selectedSite?.name}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time Bay Allocation, Capability Matching, and Maintenance Controls</p>
        </div>
        <button onClick={fetchBays} className="btn btn-secondary btn-sm">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {bays.map((bay) => (
          <div
            key={bay.id}
            className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4 shadow-lg hover:border-slate-700 transition-all"
          >
            <div className="flex-between">
              <div>
                <h3 className="font-bold text-slate-100 text-base">{bay.bay_name}</h3>
                <p className="text-xs text-slate-400 font-mono">{bay.bay_type}</p>
              </div>
              <StatusBadge status={bay.status} />
            </div>

            <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60 text-xs">
              <span className="text-slate-400 block">Current Occupant Vehicle:</span>
              <span className="font-mono text-sm font-bold text-cyan-300">
                {bay.current_vehicle_number || 'No Vehicle Assigned'}
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
              {bay.status !== 'AVAILABLE' && (
                <button
                  onClick={() => handleReleaseBay(bay.id)}
                  className="btn btn-secondary btn-sm flex-1 text-xs justify-center"
                >
                  Force Release
                </button>
              )}
              {bay.status === 'AVAILABLE' ? (
                <button
                  onClick={() => handleUpdateStatus(bay.id, 'MAINTENANCE')}
                  className="btn btn-secondary btn-sm flex-1 text-xs text-amber-400 justify-center"
                >
                  Maintenance Mode
                </button>
              ) : bay.status === 'MAINTENANCE' ? (
                <button
                  onClick={() => handleUpdateStatus(bay.id, 'AVAILABLE')}
                  className="btn btn-success btn-sm flex-1 text-xs justify-center"
                >
                  Mark Available
                </button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

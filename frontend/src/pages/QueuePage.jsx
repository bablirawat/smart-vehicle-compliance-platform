import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { StatusBadge } from '../components/StatusBadge';
import { ListOrdered, Clock, RefreshCw } from 'lucide-react';

export const QueuePage = () => {
  const { selectedSite, selectedSiteId } = useSite();
  const { lastEvent } = useWebSocket();
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    if (!selectedSiteId) return;
    try {
      const res = await api.get('/queues', { params: { site_id: selectedSiteId } });
      setQueueItems(res.data);
    } catch (err) {
      console.error('Failed to fetch queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [selectedSiteId]);

  useEffect(() => {
    if (lastEvent) fetchQueue();
  }, [lastEvent]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 flex items-center gap-2">
            <ListOrdered className="w-5 h-5 sm:w-6 sm:h-6 text-amber-400 shrink-0" />
            <span className="truncate">Live Site Queue - {selectedSite?.name}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time Queue Positions, Waiting Durations, and Priorities</p>
        </div>
        <button onClick={fetchQueue} className="btn-action btn-secondary-style btn-sm-size self-start sm:self-auto" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Queue Position</th>
                <th>Vehicle Number</th>
                <th>Entry Time</th>
                <th>Wait Time</th>
                <th>Priority</th>
                <th>Eligibility</th>
              </tr>
            </thead>
            <tbody>
              {queueItems.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-slate-500 text-xs">
                    Queue is currently empty.
                  </td>
                </tr>
              ) : (
                queueItems.map((item) => (
                  <tr key={item.id}>
                    <td className="font-bold text-base text-amber-400 font-mono">
                      #{item.position}
                    </td>
                    <td className="font-mono font-bold text-slate-100">
                      {item.vehicle_number}
                    </td>
                    <td className="text-xs text-slate-400 font-mono">
                      {new Date(item.entry_time).toLocaleTimeString()}
                    </td>
                    <td className="text-xs font-mono text-cyan-400">
                      {Math.floor(item.wait_time_seconds / 60)}m {item.wait_time_seconds % 60}s
                    </td>
                    <td>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {item.priority === 2 ? 'HIGH' : 'NORMAL'}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={item.eligibility_status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

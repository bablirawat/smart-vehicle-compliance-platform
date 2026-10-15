import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { StatusBadge } from '../components/StatusBadge';
import { Bell, ShieldAlert, CheckCircle2, Eye, RefreshCw } from 'lucide-react';

export const AlertsPage = () => {
  const { selectedSite, selectedSiteId } = useSite();
  const { lastEvent } = useWebSocket();
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    if (!selectedSiteId) return;
    try {
      const params = { site_id: selectedSiteId };
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;
      const res = await api.get('/alerts', { params });
      setAlerts(res.data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedSiteId, statusFilter, severityFilter]);

  useEffect(() => {
    if (lastEvent) fetchAlerts();
  }, [lastEvent]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.post(`/alerts/${alertId}/acknowledge`);
      fetchAlerts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to acknowledge alert');
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await api.post(`/alerts/${alertId}/resolve`);
      fetchAlerts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to resolve alert');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bell className="w-6 h-6 text-rose-400" />
            <span>Alerts & Incident Management Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time Exception Tracking, Operational Warnings & Operator Resolution</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="form-select text-xs py-1.5"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="form-select text-xs py-1.5"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <button onClick={fetchAlerts} className="btn btn-secondary btn-sm">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Created</th>
                <th>Alert Type</th>
                <th>Severity</th>
                <th>Message</th>
                <th>Vehicle</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">
                    No open alerts found.
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="text-xs text-slate-400 font-mono">
                      {new Date(alert.created_at).toLocaleTimeString()}
                    </td>
                    <td className="font-mono text-xs font-semibold text-slate-200">
                      {alert.alert_type}
                    </td>
                    <td>
                      <StatusBadge status={alert.severity} />
                    </td>
                    <td className="text-xs text-slate-300">
                      {alert.message}
                    </td>
                    <td className="font-mono text-xs text-cyan-300">
                      {alert.vehicle_number || '-'}
                    </td>
                    <td>
                      <StatusBadge status={alert.status} />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {alert.status === 'OPEN' && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="btn btn-secondary btn-sm text-xs"
                          >
                            Acknowledge
                          </button>
                        )}
                        {alert.status !== 'RESOLVED' && (
                          <button
                            onClick={() => handleResolve(alert.id)}
                            className="btn btn-success btn-sm text-xs"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
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

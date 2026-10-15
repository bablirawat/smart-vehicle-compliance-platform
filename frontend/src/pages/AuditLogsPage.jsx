import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { FileCheck2, Download, Search, RefreshCw } from 'lucide-react';

export const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [vehicleFilter, setVehicleFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [userEmailFilter, setUserEmailFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAuditLogs = async () => {
    try {
      const params = {};
      if (vehicleFilter) params.vehicle_number = vehicleFilter;
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      if (userEmailFilter) params.user_email = userEmailFilter;
      const res = await api.get('/audit', { params });
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [vehicleFilter, eventTypeFilter, userEmailFilter]);

  const handleExportCSV = async () => {
    try {
      const response = await api.get('/audit/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to export CSV');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-indigo-400" />
            <span>Immutable Audit Logs & Compliance Traceability</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Complete Historical Audit Trail of User Actions, Overrides, and State Changes</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleExportCSV} className="btn btn-secondary btn-sm text-emerald-400 border-emerald-500/30">
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
          <button onClick={fetchAuditLogs} className="btn btn-secondary btn-sm">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="card grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="form-label">Filter by Vehicle Number</label>
          <input
            type="text"
            placeholder="e.g. DL01AB1234"
            value={vehicleFilter}
            onChange={(e) => setVehicleFilter(e.target.value)}
            className="form-input text-xs"
          />
        </div>
        <div>
          <label className="form-label">Filter by Event Type</label>
          <input
            type="text"
            placeholder="e.g. STATE_CHANGE, OPERATOR_OVERRIDE"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="form-input text-xs"
          />
        </div>
        <div>
          <label className="form-label">Filter by User Email</label>
          <input
            type="text"
            placeholder="e.g. operator@sitea.com"
            value={userEmailFilter}
            onChange={(e) => setUserEmailFilter(e.target.value)}
            className="form-input text-xs"
          />
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Role</th>
                <th>Action</th>
                <th>Vehicle</th>
                <th>Prev State → New State</th>
                <th>Reason / Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">
                    No matching audit records found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-xs text-slate-400 font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="text-xs font-medium text-slate-200">
                      {log.user_email || 'SYSTEM'}
                    </td>
                    <td className="text-[11px] font-semibold text-indigo-400 font-mono">
                      {log.role || 'SYSTEM'}
                    </td>
                    <td className="font-mono text-xs font-semibold text-slate-300">
                      {log.action}
                    </td>
                    <td className="font-mono text-xs text-cyan-300">
                      {log.vehicle_number || '-'}
                    </td>
                    <td className="text-xs font-mono">
                      {log.previous_state ? (
                        <span>
                          <span className="text-slate-400">{log.previous_state}</span> → <span className="text-blue-400">{log.new_state}</span>
                        </span>
                      ) : (
                        <span className="text-blue-400">{log.new_state}</span>
                      )}
                    </td>
                    <td className="text-xs text-amber-300/90 italic">
                      {log.reason || '-'}
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

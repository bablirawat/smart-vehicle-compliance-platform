import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { StatusBadge } from '../components/StatusBadge';
import { Truck, Eye, RefreshCw } from 'lucide-react';

export const VehiclesPage = () => {
  const { selectedSiteId } = useSite();
  const [journeys, setJourneys] = useState([]);
  const navigate = useNavigate();

  const fetchJourneys = async () => {
    try {
      const res = await api.get('/journeys', { params: { site_id: selectedSiteId } });
      setJourneys(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchJourneys();
  }, [selectedSiteId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 flex items-center gap-2">
            <Truck className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400 shrink-0" />
            <span className="truncate">Active Site Vehicle Journeys</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Historical & Live Vehicle Lifecycle Records</p>
        </div>
        <button onClick={fetchJourneys} className="btn-action btn-secondary-style btn-sm-size self-start sm:self-auto" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Vehicle Number</th>
                <th>Current State</th>
                <th>Entry Time</th>
                <th>ANPR Confidence</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {journeys.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center py-8 text-slate-500 text-xs">
                    No vehicle journeys recorded for this site yet.
                  </td>
                </tr>
              ) : (
                journeys.map((j) => (
                  <tr key={j.id}>
                    <td className="font-mono font-bold text-slate-100">{j.vehicle_number}</td>
                    <td><StatusBadge status={j.current_state} /></td>
                    <td className="text-xs text-slate-400 font-mono whitespace-nowrap">{new Date(j.entry_time).toLocaleString()}</td>
                    <td className="text-xs font-mono text-emerald-400">{(j.anpr_confidence * 100).toFixed(0)}%</td>
                    <td className="whitespace-nowrap">
                      <button onClick={() => navigate(`/journeys/${j.id}`)} className="btn-action btn-secondary-style btn-sm-size text-xs">
                        <Eye className="w-3.5 h-3.5" />
                        <span>Timeline</span>
                      </button>
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

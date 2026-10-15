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
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Truck className="w-6 h-6 text-blue-400" />
            <span>Active Site Vehicle Journeys</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Historical & Live Vehicle Lifecycle Records</p>
        </div>
        <button onClick={fetchJourneys} className="btn btn-secondary btn-sm">
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
              {journeys.map((j) => (
                <tr key={j.id}>
                  <td className="font-mono font-bold text-slate-100">{j.vehicle_number}</td>
                  <td><StatusBadge status={j.current_state} /></td>
                  <td className="text-xs text-slate-400 font-mono">{new Date(j.entry_time).toLocaleString()}</td>
                  <td className="text-xs font-mono text-emerald-400">{(j.anpr_confidence * 100).toFixed(0)}%</td>
                  <td>
                    <button onClick={() => navigate(`/journeys/${j.id}`)} className="btn btn-secondary btn-sm text-xs">
                      <Eye className="w-3.5 h-3.5" />
                      <span>Timeline</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

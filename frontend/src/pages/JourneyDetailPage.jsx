import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { Timeline } from '../components/Timeline';
import { ArrowLeft, Truck, ShieldCheck, FileText, Clock, RefreshCw, CheckCircle2, ChevronRight, AlertTriangle } from 'lucide-react';

export const JourneyDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [journey, setJourney] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchJourneyDetail = async () => {
    try {
      const res = await api.get(`/journeys/${id}`);
      setJourney(res.data);
    } catch (err) {
      console.error('Failed to fetch journey detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJourneyDetail();
  }, [id]);

  if (loading || !journey) {
    return <div className="p-8 text-slate-400 font-mono text-sm">Loading Journey #{id} details...</div>;
  }

  const steps = [
    'ENTERED',
    'IDENTIFIED',
    'VERIFIED',
    journey.current_state === 'HOLD' ? 'HOLD' : 'ELIGIBLE',
    'QUEUED',
    'BAY_ASSIGNED',
    'IN_SERVICE',
    'SERVICE_COMPLETED',
    'EXITED'
  ];

  const stateOrder = {
    'ENTERED': 1,
    'IDENTIFIED': 2,
    'VERIFIED': 3,
    'ELIGIBLE': 4,
    'HOLD': 4,
    'QUEUED': 5,
    'BAY_ASSIGNED': 6,
    'IN_SERVICE': 7,
    'SERVICE_COMPLETED': 8,
    'EXITED': 9
  };

  const currentOrder = stateOrder[journey.current_state] || 1;

  // Calculate turnaround duration if exited
  let turnaroundMinutes = '-';
  if (journey.entry_time && journey.exit_time) {
    const start = new Date(journey.entry_time);
    const end = new Date(journey.exit_time);
    turnaroundMinutes = `${((end - start) / 60000).toFixed(1)} mins`;
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button onClick={() => navigate(-1)} className="btn-action btn-secondary-style btn-sm-size">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Operations</span>
      </button>

      {/* Header Info */}
      <div className="panel-card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="bg-blue-600/20 p-2.5 sm:p-3 rounded-xl border border-blue-500/30 text-blue-400 shrink-0">
              <Truck className="w-6 h-6 sm:w-8 sm:h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                <h2 className="text-xl sm:text-2xl font-bold font-mono text-slate-100">{journey.vehicle_number}</h2>
                <StatusBadge status={journey.current_state} />
              </div>
              <p className="text-xs text-slate-400 mt-1 break-words">
                Journey #{journey.id} • Station: <span className="text-slate-200 font-semibold">{journey.site_name}</span> • ANPR: <span className="font-mono text-emerald-400 font-bold">{(journey.anpr_confidence * 100).toFixed(0)}%</span>
              </p>
            </div>
          </div>
          <button onClick={fetchJourneyDetail} className="btn-action btn-secondary-style btn-sm-size self-start sm:self-auto" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Visual Lifecycle Progress Tracker */}
        <div className="mt-6 pt-4 border-t border-slate-800">
          <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            Vehicle Lifecycle Progress
          </div>
          <div className="lifecycle-flow">
            {steps.map((st, idx) => {
              const stepNum = stateOrder[st];
              let stepClass = 'lifecycle-step';
              if (stepNum < currentOrder) stepClass += ' lifecycle-step-done';
              else if (stepNum === currentOrder) stepClass += ' lifecycle-step-active';

              return (
                <React.Fragment key={st}>
                  <div className={stepClass}>
                    {stepNum < currentOrder ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : st === 'HOLD' ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    ) : (
                      <span className="font-mono text-[10px]">0{stepNum}</span>
                    )}
                    <span>{st.replace(/_/g, ' ')}</span>
                  </div>
                  {idx < steps.length - 1 && (
                    <ChevronRight className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Grid: Verifications & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Col: Verification Cards & Metadata */}
        <div className="space-y-6">
          {/* External Verification Results */}
          <div className="panel-card">
            <div className="panel-header">
              <h3 className="panel-title">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>Simulated Verification Results</span>
              </h3>
            </div>

            <div className="space-y-3">
              {journey.verifications.map((v) => (
                <div key={v.id} className="p-3 bg-slate-850 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex-between">
                    <span className="font-semibold text-xs text-slate-200 uppercase tracking-wide">
                      {v.verification_type} VERIFICATION
                    </span>
                    <StatusBadge status={v.status} />
                  </div>
                  <div className="text-xs text-slate-400 font-mono">
                    Source: {v.source} • Timestamp: {new Date(v.timestamp).toLocaleTimeString()}
                  </div>
                  {v.details && (
                    <div className="p-2.5 bg-slate-950 rounded font-mono text-[11px] text-slate-300 break-words">
                      {v.details}
                    </div>
                  )}
                  {v.error_message && (
                    <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded text-[11px] text-rose-400 break-words">
                      Error: {v.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Metadata & Timestamps */}
          <div className="panel-card space-y-4">
            <div className="panel-header">
              <h3 className="panel-title">
                <FileText className="w-5 h-5 text-cyan-400" />
                <span>Journey Timestamps & Durations</span>
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-slate-850 rounded border border-slate-800">
                <span className="text-slate-400 block">Entry Time:</span>
                <span className="font-semibold font-mono text-slate-200">{new Date(journey.entry_time).toLocaleString()}</span>
              </div>
              <div className="p-2.5 bg-slate-850 rounded border border-slate-800">
                <span className="text-slate-400 block">Exit Time:</span>
                <span className="font-semibold font-mono text-slate-200">{journey.exit_time ? new Date(journey.exit_time).toLocaleString() : 'Not Exited'}</span>
              </div>
              <div className="p-2.5 bg-slate-850 rounded border border-slate-800">
                <span className="text-slate-400 block">Assigned Bay:</span>
                <span className="font-semibold text-slate-200">{journey.assigned_bay_name || 'None'}</span>
              </div>
              <div className="p-2.5 bg-slate-850 rounded border border-slate-800">
                <span className="text-slate-400 block">Total Turnaround Time:</span>
                <span className="font-semibold font-mono text-emerald-400">{turnaroundMinutes}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Chronological Timeline */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">
              <Clock className="w-5 h-5 text-indigo-400" />
              <span>Chronological State Timeline</span>
            </h3>
          </div>
          <Timeline events={journey.events} />
        </div>
      </div>
    </div>
  );
};

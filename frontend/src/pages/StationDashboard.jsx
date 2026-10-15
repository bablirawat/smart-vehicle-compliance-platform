import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';
import { KPICard } from '../components/KPICard';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';
import {
  Truck,
  ListOrdered,
  Grid,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Play,
  LogOut,
  Eye,
  RefreshCw,
  Sliders,
  Sparkles,
  Camera,
  Activity,
  ArrowRight
} from 'lucide-react';

export const StationDashboard = () => {
  const { selectedSite, selectedSiteId } = useSite();
  const { lastEvent } = useWebSocket();
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();

  const [kpis, setKpis] = useState(null);
  const [journeys, setJourneys] = useState([]);
  const [bays, setBays] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [eventFeed, setEventFeed] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [activeModal, setActiveModal] = useState(null); // 'hold' | 'release' | 'override' | 'start_service'
  const [selectedJourney, setSelectedJourney] = useState(null);
  const [modalReason, setModalReason] = useState('');
  const [overrideState, setOverrideState] = useState('QUEUED');
  const [selectedBayId, setSelectedBayId] = useState('');

  const getVerificationStatus = (j) => {
    if (!j) return { label: 'PENDING', className: 'text-amber-400 font-semibold' };

    // Check if verification results array is attached
    if (Array.isArray(j.verifications) && j.verifications.length > 0) {
      const anyFailed = j.verifications.some((v) => ['INVALID', 'EXPIRED', 'NOT_FOUND', 'TIMEOUT'].includes(v.status));
      if (anyFailed) return { label: 'FAILED', className: 'text-rose-400 font-semibold' };
      const allValid = j.verifications.every((v) => v.status === 'VALID');
      if (allValid) return { label: 'PASSED', className: 'text-emerald-400 font-semibold' };
    }

    if (j.verification_status) {
      const vs = String(j.verification_status).toUpperCase();
      if (vs === 'VALID' || vs === 'PASSED') return { label: 'PASSED', className: 'text-emerald-400 font-semibold' };
      if (vs === 'INVALID' || vs === 'FAILED' || vs === 'EXPIRED') return { label: 'FAILED', className: 'text-rose-400 font-semibold' };
      if (vs === 'HOLD') return { label: 'HOLD', className: 'text-amber-400 font-semibold' };
      return { label: 'PENDING', className: 'text-amber-400 font-semibold' };
    }

    // Check if an open alert exists for this journey regarding verification or non-compliance
    const hasVerificationAlert = alerts?.some(
      (a) => a.journey_id === j.id && (a.alert_type === 'NON_ELIGIBLE_VEHICLE' || a.alert_type === 'VERIFICATION_FAILED')
    );
    if (hasVerificationAlert || j.current_state === 'NOT_ELIGIBLE') {
      return { label: 'FAILED', className: 'text-rose-400 font-semibold' };
    }

    // Pre-verification lifecycle states
    if (j.current_state === 'ENTERED' || j.current_state === 'IDENTIFIED') {
      return { label: 'PENDING', className: 'text-amber-400 font-semibold' };
    }

    // Held during or after verification
    if (j.current_state === 'HOLD') {
      return { label: 'HOLD', className: 'text-amber-400 font-semibold' };
    }

    // In state machine, states from VERIFIED onwards have successfully passed verification
    if (['VERIFIED', 'ELIGIBLE', 'QUEUED', 'BAY_ASSIGNED', 'IN_SERVICE', 'SERVICE_COMPLETED', 'EXITED'].includes(j.current_state)) {
      return { label: 'PASSED', className: 'text-emerald-400 font-semibold' };
    }

    return { label: 'PENDING', className: 'text-slate-400 font-semibold' };
  };

  const loadDashboardData = async () => {
    if (!selectedSiteId) return;
    try {
      const [kpiRes, jRes, bayRes, alertRes, siteRes] = await Promise.all([
        api.get('/dashboard/kpis', { params: { site_id: selectedSiteId } }),
        api.get('/journeys', { params: { site_id: selectedSiteId } }),
        api.get('/bays', { params: { site_id: selectedSiteId } }),
        api.get('/alerts', { params: { site_id: selectedSiteId, status: 'OPEN' } }),
        api.get(`/sites/${selectedSiteId}`)
      ]);

      setKpis(kpiRes.data);
      setJourneys(jRes.data);
      setBays(bayRes.data);
      setAlerts(alertRes.data);
      if (siteRes.data.cameras) setCameras(siteRes.data.cameras);
    } catch (err) {
      console.error('Failed to refresh station dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [selectedSiteId]);

  // Auto-refresh when WebSocket event arrives & push to event feed
  useEffect(() => {
    if (lastEvent) {
      setEventFeed((prev) => [
        { time: new Date().toLocaleTimeString(), type: lastEvent.type, detail: JSON.stringify(lastEvent) },
        ...prev.slice(0, 19)
      ]);
      loadDashboardData();
    }
  }, [lastEvent]);

  // Actions
  const handleStartService = async (journey, bayId) => {
    try {
      await api.post('/service/start', { journey_id: journey.id, bay_id: bayId });
      loadDashboardData();
      setActiveModal(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start service');
    }
  };

  const handleCompleteService = async (journeyId) => {
    try {
      await api.post('/service/complete', { journey_id: journeyId });
      loadDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to complete service');
    }
  };

  const handleExitVehicle = async (journeyId) => {
    try {
      const camera = cameras.find((c) => c.type === 'EXIT') || { id: 2 };
      await api.post('/events/vehicle-exit', {
        site_id: selectedSiteId,
        camera_id: camera.id,
        journey_id: journeyId
      });
      loadDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to exit vehicle');
    }
  };

  const handleHoldRelease = async (isHold) => {
    if (!selectedJourney) return;
    try {
      const endpoint = isHold ? `/journeys/${selectedJourney.id}/hold` : `/journeys/${selectedJourney.id}/release`;
      await api.post(endpoint, { reason: modalReason || (isHold ? 'Put on hold by operator' : 'Released by operator') });
      loadDashboardData();
      setActiveModal(null);
      setModalReason('');
    } catch (err) {
      alert(err.response?.data?.detail?.message || err.response?.data?.detail || 'Operation failed');
    }
  };

  const handleOverride = async () => {
    if (!selectedJourney || !modalReason) {
      alert('A detailed override reason is required');
      return;
    }
    try {
      await api.post(`/journeys/${selectedJourney.id}/override`, {
        target_state: overrideState,
        reason: modalReason
      });
      loadDashboardData();
      setActiveModal(null);
      setModalReason('');
    } catch (err) {
      alert(err.response?.data?.detail?.message || err.response?.data?.detail || 'Override failed');
    }
  };

  const completedJourneysToday = journeys.filter(j => j.current_state === 'EXITED').length;
  const cameraOnlineCount = cameras.filter(c => c.status === 'ONLINE').length;

  if (loading && !kpis) {
    return <div className="p-8 text-slate-400 font-mono text-sm">Loading Station Dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Top Action Header */}
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>{selectedSite?.name || 'Station Operations Console'}</span>
            <span className="text-xs px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono font-bold border border-blue-500/30">
              {selectedSite?.code}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time Terminal Operations & Inspection Lifecycle</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/simulator')}
            className="btn-action btn-primary-style btn-sm-size bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg"
          >
            <Sparkles className="w-4 h-4" />
            <span>Launch Simulator</span>
          </button>
          <button onClick={loadDashboardData} className="btn-action btn-secondary-style btn-sm-size" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 8 Required KPI Cards */}
      {kpis && (
        <div className="kpi-container">
          <KPICard title="Active Vehicles" value={kpis.current_vehicles} icon={Truck} color="blue" subtext="In station journey" />
          <KPICard title="Queue Length" value={kpis.queue_length} icon={ListOrdered} color="amber" subtext="Waiting for bay" />
          <KPICard title="Available Bays" value={`${kpis.available_bays} / ${kpis.available_bays + kpis.occupied_bays}`} icon={Grid} color="emerald" subtext={`${kpis.resource_utilization_percent}% utilization`} />
          <KPICard title="Open Alerts" value={kpis.open_alerts} icon={ShieldAlert} color="rose" subtext="Requires attention" />
          <KPICard title="Average Wait Time" value={`${kpis.avg_wait_time_minutes} min`} icon={Clock} color="cyan" subtext="Entry to bay assignment" />
          <KPICard title="Average Service Time" value={`${kpis.avg_service_time_minutes} min`} icon={CheckCircle2} color="purple" subtext="Service start to completion" />
          <KPICard title="Today's Completed" value={completedJourneysToday} icon={Activity} color="emerald" subtext="Fully exited vehicles" />
          <KPICard title="Camera Status" value={`${cameraOnlineCount} / ${cameras.length}`} icon={Camera} color={cameraOnlineCount === cameras.length ? 'emerald' : 'rose'} subtext="ANPR optical health" />
        </div>
      )}

      {/* Main Grid: Journeys Table & Sidebar Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Operational Journeys Table (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="panel-card">
            <div className="panel-header">
              <h3 className="panel-title">
                <Truck className="w-5 h-5 text-blue-400" />
                <span>Live Vehicle Operations</span>
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {journeys.filter(j => j.current_state !== 'EXITED').length} Active Journeys
              </span>
            </div>

            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Vehicle Number</th>
                    <th>Entry Time</th>
                    <th>Verification</th>
                    <th>Eligibility</th>
                    <th>Queue</th>
                    <th>Bay</th>
                    <th>Journey Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {journeys.filter(j => j.current_state !== 'EXITED').length === 0 ? (
                    <tr>
                      <td colSpan="8" className="text-center py-8 text-slate-500 text-xs">
                        No active vehicles currently on site. Use the Event Simulator to trigger entry events!
                      </td>
                    </tr>
                  ) : (
                    journeys.filter(j => j.current_state !== 'EXITED').map((j) => (
                      <tr key={j.id}>
                        <td className="font-mono font-bold text-slate-100 text-sm">
                          {j.vehicle_number}
                        </td>
                        <td className="text-xs text-slate-400 font-mono">
                          {new Date(j.entry_time).toLocaleTimeString()}
                        </td>
                        <td>
                          {(() => {
                            const v = getVerificationStatus(j);
                            return (
                              <span className={`text-xs font-mono ${v.className}`}>
                                {v.label}
                              </span>
                            );
                          })()}
                        </td>
                        <td>
                          <StatusBadge status={j.current_state === 'HOLD' ? 'NOT_ELIGIBLE' : 'ELIGIBLE'} />
                        </td>
                        <td className="text-xs font-mono text-amber-400 font-bold">
                          {j.queue_position ? `#${j.queue_position}` : '-'}
                        </td>
                        <td className="text-xs font-medium text-slate-300">
                          {j.assigned_bay_name || bays.find((b) => b.current_journey_id === j.id)?.bay_name || '-'}
                        </td>
                        <td>
                          <StatusBadge status={j.current_state} />
                        </td>
                        <td>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => navigate(`/journeys/${j.id}`)}
                              className="btn-action btn-secondary-style btn-sm-size p-1.5"
                              title="View Details & Timeline"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>

                            {j.current_state === 'BAY_ASSIGNED' && (
                              <button
                                onClick={() => {
                                  setSelectedJourney(j);
                                  const avail = bays.find((b) => b.status === 'RESERVED' && b.current_journey_id === j.id) || bays.find((b) => b.status === 'AVAILABLE');
                                  setSelectedBayId(avail ? avail.id : '');
                                  setActiveModal('start_service');
                                }}
                                className="btn-action btn-success-style btn-sm-size p-1.5"
                                title="Start Inspection Service"
                              >
                                <Play className="w-3.5 h-3.5" />
                              </button>
                            )}

                            {j.current_state === 'IN_SERVICE' && (
                              <button
                                onClick={() => handleCompleteService(j.id)}
                                className="btn-action btn-primary-style btn-sm-size p-1.5"
                                title="Complete Inspection Service"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5" />
                              </button>
                            )}

                            {(j.current_state === 'SERVICE_COMPLETED' || j.current_state === 'HOLD') && (
                              <button
                                onClick={() => handleExitVehicle(j.id)}
                                className="btn-action btn-danger-style btn-sm-size p-1.5"
                                title="Exit Vehicle from Site"
                              >
                                <LogOut className="w-3.5 h-3.5" />
                              </button>
                            )}

                            {j.current_state === 'HOLD' ? (
                              <button
                                onClick={() => {
                                  setSelectedJourney(j);
                                  setActiveModal('release');
                                }}
                                className="btn-action btn-secondary-style btn-sm-size text-amber-400"
                                title="Release from HOLD"
                              >
                                Release
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  setSelectedJourney(j);
                                  setActiveModal('hold');
                                }}
                                className="btn-action btn-secondary-style btn-sm-size text-rose-400"
                                title="Place on HOLD"
                              >
                                Hold
                              </button>
                            )}

                            {hasRole(['Site Manager', 'Regional Manager', 'Admin']) && (
                              <button
                                onClick={() => {
                                  setSelectedJourney(j);
                                  setActiveModal('override');
                                }}
                                className="btn-action btn-secondary-style btn-sm-size text-indigo-400"
                                title="Manager Override"
                              >
                                <Sliders className="w-3.5 h-3.5" />
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

        {/* Right Sidebar Widgets: Bays, Alerts & Live Event Feed (1 col) */}
        <div className="space-y-6">
          {/* Service Bays Status */}
          <div className="panel-card">
            <div className="panel-header">
              <h3 className="panel-title">
                <Grid className="w-4 h-4 text-emerald-400" />
                <span>Service Bays</span>
              </h3>
              <button onClick={() => navigate('/bays')} className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                <span>All Bays</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-2">
              {bays.map((bay) => (
                <div key={bay.id} className="p-2.5 bg-slate-850 rounded-lg border border-slate-800 flex-between">
                  <div>
                    <div className="text-xs font-bold text-slate-200">{bay.bay_name}</div>
                    <div className="text-[11px] text-slate-400">{bay.bay_type}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {bay.current_vehicle_number && (
                      <span className="text-xs font-mono text-cyan-300 font-bold">{bay.current_vehicle_number}</span>
                    )}
                    <StatusBadge status={bay.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Open Alerts */}
          <div className="panel-card">
            <div className="panel-header">
              <h3 className="panel-title">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span>Recent Open Alerts</span>
              </h3>
              <button onClick={() => navigate('/alerts')} className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                <span>View All</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-2">
              {alerts.length === 0 ? (
                <div className="text-xs text-slate-500 py-3 text-center">No open alerts for this station.</div>
              ) : (
                alerts.slice(0, 3).map((a) => (
                  <div key={a.id} className="p-2.5 bg-slate-850 rounded-lg border border-slate-800 space-y-1">
                    <div className="flex-between">
                      <span className="text-xs font-bold text-slate-200 font-mono">{a.alert_type}</span>
                      <StatusBadge status={a.severity} />
                    </div>
                    <p className="text-[11px] text-slate-400">{a.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Live Real-time WebSocket Event Feed Ticker */}
          <div className="panel-card">
            <div className="panel-header">
              <h3 className="panel-title">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span>Live Event Feed Ticker</span>
              </h3>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1.5 max-h-48 overflow-y-auto">
              {eventFeed.length === 0 ? (
                <div className="text-slate-600">Waiting for live WebSocket events...</div>
              ) : (
                eventFeed.map((evt, idx) => (
                  <div key={idx} className="text-emerald-400">
                    [{evt.time}] <span className="text-cyan-300 font-bold">{evt.type}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Start Service Modal */}
      <Modal
        isOpen={activeModal === 'start_service'}
        onClose={() => setActiveModal(null)}
        title={`Start Inspection Service for ${selectedJourney?.vehicle_number}`}
      >
        <div className="space-y-4">
          <div className="form-group">
            <label className="form-field-label">Select Inspection Bay</label>
            <select
              value={selectedBayId}
              onChange={(e) => setSelectedBayId(e.target.value)}
              className="form-control-select"
            >
              <option value="">Select Bay...</option>
              {bays.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.bay_name} ({b.status})
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => handleStartService(selectedJourney, selectedBayId)}
            className="w-full btn-action btn-success-style justify-center"
            disabled={!selectedBayId}
          >
            Start Service Session
          </button>
        </div>
      </Modal>

      {/* Hold / Release Modal */}
      <Modal
        isOpen={activeModal === 'hold' || activeModal === 'release'}
        onClose={() => setActiveModal(null)}
        title={activeModal === 'hold' ? `Hold Vehicle ${selectedJourney?.vehicle_number}` : `Release Vehicle ${selectedJourney?.vehicle_number}`}
      >
        <div className="space-y-4">
          <div className="form-group">
            <label className="form-field-label">Operator Reason / Note</label>
            <textarea
              rows="3"
              value={modalReason}
              onChange={(e) => setModalReason(e.target.value)}
              placeholder="Provide justification..."
              className="form-control-textarea"
            />
          </div>
          <button
            onClick={() => handleHoldRelease(activeModal === 'hold')}
            className={`w-full btn-action justify-center ${activeModal === 'hold' ? 'btn-danger-style' : 'btn-success-style'}`}
          >
            Confirm {activeModal === 'hold' ? 'HOLD' : 'RELEASE'}
          </button>
        </div>
      </Modal>

      {/* Manager Override Modal */}
      <Modal
        isOpen={activeModal === 'override'}
        onClose={() => setActiveModal(null)}
        title={`Authorized Manager Override - ${selectedJourney?.vehicle_number}`}
      >
        <div className="space-y-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded text-amber-300 text-xs">
            Notice: Manager overrides bypass default state rules and generate mandatory audit records.
          </div>
          <div className="form-group">
            <label className="form-field-label">Target State</label>
            <select
              value={overrideState}
              onChange={(e) => setOverrideState(e.target.value)}
              className="form-control-select"
            >
              <option value="QUEUED">QUEUED</option>
              <option value="ELIGIBLE">ELIGIBLE</option>
              <option value="HOLD">HOLD</option>
              <option value="EXITED">EXITED</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-field-label">Detailed Override Reason (Required)</label>
            <textarea
              rows="3"
              value={modalReason}
              onChange={(e) => setModalReason(e.target.value)}
              placeholder="Minimum 5 characters requirement..."
              className="form-control-textarea"
              required
            />
          </div>
          <button
            onClick={handleOverride}
            className="w-full btn-action btn-primary-style justify-center"
            disabled={!modalReason || modalReason.length < 5}
          >
            Execute Authorized Override
          </button>
        </div>
      </Modal>
    </div>
  );
};

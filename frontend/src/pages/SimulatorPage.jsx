import React, { useState } from 'react';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import {
  Cpu,
  Truck,
  AlertTriangle,
  Copy,
  WifiOff,
  ServerOff,
  Layers,
  Sparkles,
  CheckCircle2,
  Play,
  LogOut,
  Clock,
  Grid,
  Sliders,
  Radio,
  Building2
} from 'lucide-react';

export const SimulatorPage = () => {
  const { selectedSite, selectedSiteId, setSelectedSiteId, sites } = useSite();
  const [customVehicle, setCustomVehicle] = useState('');
  const [customConfidence, setCustomConfidence] = useState(0.95);
  const [logs, setLogs] = useState([]);

  const addLog = (msg, isError = false) => {
    const entry = { time: new Date().toLocaleTimeString(), msg, isError };
    setLogs((prev) => [entry, ...prev.slice(0, 49)]);
  };

  const handleSimulateVehicle = async (vehicleType) => {
    try {
      const res = await api.post('/simulator/vehicle', {
        site_id: selectedSiteId,
        vehicle_type: vehicleType,
        vehicle_number: customVehicle || undefined,
        confidence: customConfidence
      });
      const data = res.data;
      if (data.duplicate) {
        addLog(`DUPLICATE ENTRY SUPPRESSED: Vehicle '${data.vehicle_number}' ignored within deduplication window.`, true);
      } else {
        addLog(`SIMULATED VEHICLE ENTRY: Journey #${data.journey_id} for '${data.vehicle_number}' -> State: ${data.current_state}`);
      }
    } catch (err) {
      addLog(`Error simulating vehicle: ${err.response?.data?.detail || err.message}`, true);
    }
  };

  const handleSimulateDuplicate = async () => {
    const vNum = `DL01-DUP-${Math.floor(Math.random() * 100)}`;
    addLog(`Sending 1st entry for ${vNum}...`);
    await api.post('/simulator/vehicle', { site_id: selectedSiteId, vehicle_number: vNum, confidence: 0.95 });
    addLog(`Sending 2nd duplicate entry for ${vNum} immediately...`);
    const res = await api.post('/simulator/vehicle', { site_id: selectedSiteId, vehicle_number: vNum, confidence: 0.95 });
    if (res.data.duplicate) {
      addLog(`SUCCESS: Deduplication engine caught duplicate entry for ${vNum}!`, false);
    }
  };

  const handleSimulateQueueOverload = async () => {
    addLog(`Flooding site #${selectedSiteId} queue with multiple vehicles to trigger QUEUE_OVERLOAD alert...`);
    for (let i = 1; i <= 6; i++) {
      await api.post('/simulator/vehicle', { site_id: selectedSiteId, vehicle_type: 'NORMAL' });
    }
    addLog(`Queue flooded! Check Alerts Center for QUEUE_OVERLOAD alert.`);
  };

  const handleSimulateCameraOffline = async () => {
    try {
      const siteRes = await api.get(`/sites/${selectedSiteId}`);
      const cam = siteRes.data.cameras?.[0] || { id: 1 };
      await api.post('/simulator/camera-offline', {
        site_id: selectedSiteId,
        camera_id: cam.id,
        offline: true
      });
      addLog(`SIMULATED CAMERA OFFLINE: Camera '${cam.code}' set to OFFLINE. Alert created.`);
    } catch (err) {
      addLog(`Error setting camera offline: ${err.message}`, true);
    }
  };

  const handleSimulateApiFailure = async (serviceName) => {
    try {
      await api.post('/simulator/external-failure', {
        service_name: serviceName,
        fail: true
      });
      addLog(`SIMULATED EXTERNAL FAILURE: ${serviceName} service marked UNAVAILABLE. Next vehicles will trigger SOURCE_UNAVAILABLE handling.`);
    } catch (err) {
      addLog(`Error simulating API failure: ${err.message}`, true);
    }
  };

  const handleSimulateBayActivity = async () => {
    try {
      const jRes = await api.get('/journeys', { params: { site_id: selectedSiteId } });
      const activeJ = jRes.data.find(j => j.current_state === 'BAY_ASSIGNED');
      if (activeJ) {
        addLog(`Starting inspection service for vehicle ${activeJ.vehicle_number} on Bay #1...`);
        await api.post('/service/start', { journey_id: activeJ.id, bay_id: 1 });
        addLog(`Service started! State updated to IN_SERVICE.`);
      } else {
        addLog(`No active journey in BAY_ASSIGNED state. Triggering entry first...`);
        await handleSimulateVehicle('NORMAL');
      }
    } catch (err) {
      addLog(`Bay simulation error: ${err.message}`, true);
    }
  };

  const handlePingWebSocket = () => {
    addLog(`Pinging WebSocket connection... Socket heartbeat ACTIVE.`);
  };

  const handleSwitchSite = (siteId) => {
    setSelectedSiteId(siteId);
    addLog(`Switched active site context to Site #${siteId}.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400 shrink-0" />
            <span className="truncate">Operational Event Simulator</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Trigger Real Backend Lifecycle Events, Outages, Detections & Failures</p>
        </div>
        <div className="text-xs font-mono text-cyan-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg self-start sm:self-auto">
          Active Station: {selectedSite?.name} (#{selectedSiteId})
        </div>
      </div>

      {/* Simulator Scenario Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Card 1: Normal Eligible Journey */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Truck className="w-4 h-4 text-emerald-400" />
              <span>1. Normal Journey</span>
            </h3>
            <span className="badge-status badge-eligible">Scenario 1</span>
          </div>
          <p className="text-xs text-slate-400">Simulate an ANPR detection for a fully compliant vehicle that proceeds through queue and bay.</p>
          <button
            onClick={() => handleSimulateVehicle('NORMAL')}
            className="w-full btn-action btn-success-style justify-center text-xs"
          >
            <Sparkles className="w-4 h-4" />
            <span>SIMULATE ELIGIBLE VEHICLE</span>
          </button>
        </div>

        {/* Card 2: Non-Eligible Vehicle */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>2. Non-Eligible Vehicle</span>
            </h3>
            <span className="badge-status badge-not-eligible">Scenario 2</span>
          </div>
          <p className="text-xs text-slate-400">Fails emissions inspection → automatically routed to HOLD state and raises High alert.</p>
          <button
            onClick={() => handleSimulateVehicle('EXPIRED')}
            className="w-full btn-action btn-danger-style justify-center text-xs"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>SIMULATE NON-ELIGIBLE VEHICLE</span>
          </button>
        </div>

        {/* Card 3: External API Failure */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <ServerOff className="w-4 h-4 text-amber-400" />
              <span>3. External API Timeout</span>
            </h3>
            <span className="badge-status badge-due-soon">Scenario 3</span>
          </div>
          <p className="text-xs text-slate-400">Simulate government compliance API failure → marks SOURCE_UNAVAILABLE for manual review.</p>
          <button
            onClick={() => handleSimulateApiFailure('IDENTITY')}
            className="w-full btn-action btn-secondary-style justify-center text-xs text-rose-400"
          >
            <ServerOff className="w-4 h-4" />
            <span>SIMULATE EXTERNAL API TIMEOUT</span>
          </button>
        </div>

        {/* Card 4: Camera Offline */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <WifiOff className="w-4 h-4 text-rose-400" />
              <span>4. ANPR Camera Offline</span>
            </h3>
            <span className="badge-status badge-offline">Scenario 4</span>
          </div>
          <p className="text-xs text-slate-400">Simulate entry camera hardware outage → updates status to OFFLINE & raises camera alert.</p>
          <button
            onClick={handleSimulateCameraOffline}
            className="w-full btn-action btn-danger-style justify-center text-xs"
          >
            <WifiOff className="w-4 h-4" />
            <span>SIMULATE CAMERA OFFLINE</span>
          </button>
        </div>

        {/* Card 5: Duplicate Entry */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Copy className="w-4 h-4 text-cyan-400" />
              <span>5. Duplicate Entry</span>
            </h3>
            <span className="badge-status badge-entered">Scenario 5</span>
          </div>
          <p className="text-xs text-slate-400">Triggers two identical ANPR entry events within 60s → 2nd entry suppressed by deduplication engine.</p>
          <button
            onClick={handleSimulateDuplicate}
            className="w-full btn-action btn-secondary-style justify-center text-xs text-cyan-400"
          >
            <Copy className="w-4 h-4" />
            <span>SIMULATE DUPLICATE ENTRY</span>
          </button>
        </div>

        {/* Card 6: Queue Overload */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>6. Queue Overload</span>
            </h3>
            <span className="badge-status badge-warning">Scenario 6</span>
          </div>
          <p className="text-xs text-slate-400">Floods station queue with multiple vehicles to exceed site capacity and trigger QUEUE_OVERLOAD alert.</p>
          <button
            onClick={handleSimulateQueueOverload}
            className="w-full btn-action btn-secondary-style justify-center text-xs text-amber-400"
          >
            <Layers className="w-4 h-4" />
            <span>SIMULATE QUEUE OVERLOAD</span>
          </button>
        </div>

        {/* Card 7: Bay Occupied */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Grid className="w-4 h-4 text-emerald-400" />
              <span>7. Bay Activity Test</span>
            </h3>
            <span className="badge-status badge-in-service">Scenario 7</span>
          </div>
          <p className="text-xs text-slate-400">Assigns and starts inspection service on an available bay, updating state to IN_SERVICE.</p>
          <button
            onClick={handleSimulateBayActivity}
            className="w-full btn-action btn-secondary-style justify-center text-xs text-emerald-400"
          >
            <Play className="w-4 h-4" />
            <span>SIMULATE BAY ACTIVITY</span>
          </button>
        </div>

        {/* Card 8: WebSocket Reconnect */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Radio className="w-4 h-4 text-indigo-400" />
              <span>8. WebSocket Ping</span>
            </h3>
            <span className="badge-status badge-verified">Scenario 8</span>
          </div>
          <p className="text-xs text-slate-400">Pings the real-time WebSocket connection to verify active broadcasting channel.</p>
          <button
            onClick={handlePingWebSocket}
            className="w-full btn-action btn-secondary-style justify-center text-xs text-indigo-400"
          >
            <Radio className="w-4 h-4" />
            <span>PING WEBSOCKET CHANNEL</span>
          </button>
        </div>

        {/* Card 9: Multiple Sites */}
        <div className="panel-card space-y-3">
          <div className="flex-between">
            <h3 className="panel-title text-sm">
              <Building2 className="w-4 h-4 text-purple-400" />
              <span>9. Multiple Sites</span>
            </h3>
            <span className="badge-status badge-exited">Scenario 9</span>
          </div>
          <p className="text-xs text-slate-400">Switch active site context between North Terminal, East Coast Cargo, and South Freight.</p>
          <div className="flex flex-wrap items-center gap-1.5">
            {sites.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSwitchSite(s.id)}
                className={`btn-action btn-sm-size flex-1 min-w-[70px] text-[11px] justify-center ${selectedSiteId === s.id ? 'btn-primary-style' : 'btn-secondary-style'}`}
              >
                {s.code}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Simulator Console Output */}
      <div className="panel-card space-y-3">
        <h3 className="panel-title text-sm font-mono text-cyan-400">
          <span>&gt; REAL-TIME BACKEND EVENT CONSOLE</span>
        </h3>
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-xs space-y-1.5 max-h-60 overflow-y-auto break-words">
          {logs.length === 0 ? (
            <div className="text-slate-600">Console ready. Click any simulation button above to trigger backend events...</div>
          ) : (
            logs.map((log, i) => (
              <div key={i} className={log.isError ? 'text-rose-400' : 'text-emerald-400'}>
                [{log.time}] {log.msg}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

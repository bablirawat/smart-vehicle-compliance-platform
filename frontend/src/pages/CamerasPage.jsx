import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useSite } from '../context/SiteContext';
import { StatusBadge } from '../components/StatusBadge';
import { Camera, AlertTriangle, RefreshCw, Power } from 'lucide-react';

export const CamerasPage = () => {
  const { selectedSite, selectedSiteId } = useSite();
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCameras = async () => {
    if (!selectedSiteId) return;
    try {
      const res = await api.get(`/sites/${selectedSiteId}`);
      if (res.data.cameras) setCameras(res.data.cameras);
    } catch (err) {
      console.error('Failed to fetch cameras:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, [selectedSiteId]);

  const handleToggleOffline = async (cam) => {
    try {
      const isCurrentlyOnline = cam.status === 'ONLINE';
      await api.post('/simulator/camera-offline', {
        site_id: selectedSiteId,
        camera_id: cam.id,
        offline: isCurrentlyOnline
      });
      fetchCameras();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to toggle camera status');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Camera className="w-6 h-6 text-cyan-400" />
            <span>ANPR Camera Network - {selectedSite?.name}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Optical Recognition Feed Health & Device Maintenance Control</p>
        </div>
        <button onClick={fetchCameras} className="btn btn-secondary btn-sm">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cameras.map((cam) => (
          <div key={cam.id} className="card space-y-4">
            <div className="flex-between">
              <div>
                <h3 className="font-bold text-slate-100 text-base font-mono">{cam.code}</h3>
                <p className="text-xs text-slate-400">Type: {cam.type} Optical Sensor</p>
              </div>
              <StatusBadge status={cam.status} />
            </div>

            {/* Simulated Video Placeholder */}
            <div className="aspect-video bg-slate-950 rounded-lg border border-slate-800 flex flex-col items-center justify-center p-4 text-center relative overflow-hidden">
              <div className="absolute top-2 left-2 text-[10px] font-mono bg-slate-900/80 px-2 py-0.5 rounded text-emerald-400 border border-slate-800">
                REC • 1080P 60FPS
              </div>
              <Camera className={`w-12 h-12 mb-2 ${cam.status === 'ONLINE' ? 'text-cyan-500/40' : 'text-rose-500/40'}`} />
              <p className="text-xs font-mono text-slate-400">
                {cam.status === 'ONLINE' ? 'ANPR Live Recognition Active' : 'CAMERA OFFLINE - FEED DISRUPTED'}
              </p>
            </div>

            <div className="flex-between pt-2 border-t border-slate-800 text-xs">
              <span className="text-slate-400">Simulate Camera State:</span>
              <button
                onClick={() => handleToggleOffline(cam)}
                className={`btn btn-sm ${cam.status === 'ONLINE' ? 'btn-danger' : 'btn-success'}`}
              >
                <Power className="w-3.5 h-3.5" />
                <span>{cam.status === 'ONLINE' ? 'Simulate OFFLINE' : 'Set ONLINE'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

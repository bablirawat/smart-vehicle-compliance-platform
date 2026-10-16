import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight, UserCheck, Lock, Mail, Radio, Building2 } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('operator@sitea.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState(null);
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email.trim(), password);
      navigate('/station-dashboard');
    } catch (err) {
      if (!err.response) {
        setError('Unable to reach backend server. Please check your network connection or verify the backend is running.');
      } else {
        setError(err.response?.data?.detail || 'Invalid email or password');
      }
    }
  };

  const handleDemoLogin = async (demoEmail) => {
    setEmail(demoEmail);
    setPassword('password123');
    setError(null);
    try {
      await login(demoEmail.trim(), 'password123');
      navigate('/station-dashboard');
    } catch (err) {
      if (!err.response) {
        setError('Unable to reach backend server. Please check your network connection or verify the backend is running.');
      } else {
        setError(err.response?.data?.detail || 'Login failed');
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col lg:flex-row">
      {/* Left Hero Section (Split Screen) */}
      <div className="lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 p-6 sm:p-8 lg:p-12 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />

        <div className="flex items-center gap-3 relative z-10">
          <div className="bg-blue-600/20 p-2 sm:p-2.5 rounded-xl border border-blue-500/30 text-blue-400 shrink-0">
            <ShieldCheck className="w-7 h-7 sm:w-8 sm:h-8" />
          </div>
          <div>
            <h1 className="font-bold text-lg sm:text-xl text-slate-100 tracking-wide">SMART VEHICLE PLATFORM</h1>
            <p className="text-xs text-slate-400 font-mono">Enterprise Journey Management System</p>
          </div>
        </div>

        <div className="my-6 sm:my-8 lg:my-12 space-y-4 sm:space-y-6 relative z-10">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-100 leading-tight">
            Automated Terminal Compliance & Operational Control
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm leading-relaxed max-w-lg">
            Real-time ANPR vehicle recognition, automated external identity & compliance verification, state machine validation, queue optimization, and multi-site regional management.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 sm:pt-4">
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-mono">
                <Radio className="w-3.5 h-3.5 live-pulse" />
                <span>REAL-TIME WEBSOCKETS</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Instant dashboard synchronization without page refresh.</p>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold font-mono">
                <Building2 className="w-3.5 h-3.5" />
                <span>MULTI-SITE RBAC</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Granular role permissions & station command control.</p>
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-500 font-mono relative z-10 hidden sm:block">
          System Build v1.0 • Enterprise Operations Ready
        </div>
      </div>

      {/* Right Login Form Section */}
      <div className="lg:w-1/2 p-6 sm:p-8 lg:p-16 flex items-center justify-center bg-slate-950">
        <div className="w-full max-w-md space-y-8">
          <div>
            <h3 className="text-2xl font-bold text-slate-100">Sign In to Command Center</h3>
            <p className="text-xs text-slate-400 mt-1">Enter your operational credentials to access station controls</p>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="form-group">
              <label className="form-field-label flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-blue-400" />
                <span>Email Address</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-control-input py-2.5"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-field-label flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-blue-400" />
                <span>Password</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-control-input py-2.5"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-action btn-primary-style justify-center py-3 text-sm font-bold shadow-lg"
            >
              <span>{loading ? 'Authenticating Credentials...' : 'Sign In to Operations Console'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* One-Click Role Selector */}
          <div className="pt-6 border-t border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-3 justify-center">
              <UserCheck className="w-4 h-4 text-blue-400" />
              <span>ONE-CLICK DEMO ACCOUNTS</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => handleDemoLogin('operator@sitea.com')}
                className="p-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-left transition-all"
              >
                <div className="text-blue-400 font-bold text-xs">Operator</div>
                <div className="text-[10px] text-slate-400">sitea@operator</div>
              </button>
              <button
                onClick={() => handleDemoLogin('sitemanager@sitea.com')}
                className="p-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-left transition-all"
              >
                <div className="text-emerald-400 font-bold text-xs">Site Manager</div>
                <div className="text-[10px] text-slate-400">sitea@manager</div>
              </button>
              <button
                onClick={() => handleDemoLogin('regional@system.com')}
                className="p-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-left transition-all"
              >
                <div className="text-purple-400 font-bold text-xs">Regional Mgr</div>
                <div className="text-[10px] text-slate-400">all-sites</div>
              </button>
              <button
                onClick={() => handleDemoLogin('admin@system.com')}
                className="p-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-left transition-all"
              >
                <div className="text-amber-400 font-bold text-xs">System Admin</div>
                <div className="text-[10px] text-slate-400">full-access</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

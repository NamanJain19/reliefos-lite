import React, { useState, useEffect, Suspense } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { api } from '../../services/api';

const UserProfileModal = React.lazy(() =>
  import('./UserProfileModal').then((m) => ({ default: m.UserProfileModal }))
);

interface NavItem {
  name: string;
  path: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Operations Overview', path: '/dashboard', icon: 'dashboard' },
  { name: 'Live Flood Map', path: '/flood-map', icon: 'map' },
  { name: 'Zones & Risk', path: '/zones', icon: 'warning' },
  { name: 'Resource Inventory', path: '/inventory', icon: 'inventory_2' },
  { name: 'Demand Management', path: '/demand', icon: 'order_approve' },
  { name: 'Relief Allocation', path: '/allocation', icon: 'emergency' },
  { name: 'Route Optimization', path: '/routes', icon: 'alt_route' },
  { name: 'Simulation & Reports', path: '/simulation', icon: 'monitoring' },
  { name: 'Data Sources', path: '/data-sources', icon: 'sensors' },
  { name: 'Settings', path: '/settings', icon: 'settings' },
];

interface Props {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<Props> = ({ isOpen = false, onClose }) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ name: string; role: string; agency: string; avatar_url?: string }>({
    name: 'Insp. S. Sharma',
    role: 'OPERATOR',
    agency: 'Disaster Ops, ASDMA',
    avatar_url: '/officer_sharma.png',
  });
  const [systemMode, setSystemMode] = useState<string>('OPERATIONAL_LIVE');
  const [telemetryStatus, setTelemetryStatus] = useState<string>('ONLINE • TELEMETRY OK');
  const [providerStats, setProviderStats] = useState({
    live: 2,
    manual: 4,
    simulated: 1,
    total: 7
  });
  const [showProvenanceModal, setShowProvenanceModal] = useState<boolean>(false);
  const [providersList, setProvidersList] = useState<any[]>([]);

  const fetchStatus = async () => {
    try {
      const [modeRes, healthRes, providersRes] = await Promise.allSettled([
        api.getSystemMode(),
        api.getHealth(),
        api.getProvidersHealth()
      ]);

      if (modeRes.status === 'fulfilled' && modeRes.value?.mode) {
        setSystemMode(modeRes.value.mode);
      } else if (healthRes.status === 'fulfilled' && healthRes.value?.mode) {
        setSystemMode(healthRes.value.mode);
      }

      if (healthRes.status === 'fulfilled' && healthRes.value?.telemetry) {
        setTelemetryStatus(healthRes.value.telemetry);
      } else {
        setTelemetryStatus('ONLINE • TELEMETRY OK');
      }

      if (providersRes.status === 'fulfilled' && providersRes.value?.providers) {
        const list = providersRes.value.providers;
        setProvidersList(list);
        const live = list.filter((p: any) => p.state === 'LIVE').length;
        const manual = list.filter((p: any) => p.state === 'MANUAL' || p.state === 'LAST_KNOWN').length;
        const sim = list.filter((p: any) => p.state === 'SIMULATED').length;
        setProviderStats({
          live,
          manual,
          simulated: sim,
          total: list.length
        });
      }
    } catch {
      // Graceful offline degradation indicator
      setTelemetryStatus('OFFLINE • UNREACHABLE');
    }
  };

  useEffect(() => {
    fetchStatus();

    // Fetch authenticated profile if session active
    if (api.isAuthenticated()) {
      api.getAuthMe()
        .then((u) => {
          if (u) {
            setCurrentUser({
              name: u.name,
              role: u.role,
              agency: u.agency || 'Disaster Ops, ASDMA',
              avatar_url: u.avatar_url,
            });
          }
        })
        .catch(() => {});
    } else {
      setCurrentUser({
        name: 'Shift Inactive',
        role: 'AUTH REQUIRED',
        agency: 'Click to Authenticate',
        avatar_url: undefined,
      });
    }

    // Listen for custom mode change events dispatched by Topbar
    const handleModeEvent = (e: any) => {
      if (e.detail?.mode) {
        setSystemMode(e.detail.mode);
      }
      fetchStatus();
    };

    // Listen for profile update events
    const handleProfileUpdated = (e: any) => {
      if (e.detail) {
        setCurrentUser({
          name: e.detail.name,
          role: e.detail.role,
          agency: e.detail.agency || 'Disaster Ops, ASDMA',
          avatar_url: e.detail.avatar_url,
        });
      }
    };

    const handleAuthExpired = () => {
      setCurrentUser({
        name: 'Shift Inactive',
        role: 'AUTH REQUIRED',
        agency: 'Click to Authenticate',
        avatar_url: undefined,
      });
    };

    window.addEventListener('reliefos-mode-changed', handleModeEvent);
    window.addEventListener('reliefos-profile-updated', handleProfileUpdated);
    window.addEventListener('reliefos-auth-expired', handleAuthExpired);
    const interval = setInterval(fetchStatus, 25000);

    return () => {
      window.removeEventListener('reliefos-mode-changed', handleModeEvent);
      window.removeEventListener('reliefos-profile-updated', handleProfileUpdated);
      window.removeEventListener('reliefos-auth-expired', handleAuthExpired);
      clearInterval(interval);
    };
  }, []);

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 lg:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Data Source Provenance Modal */}
      {showProvenanceModal && (
        <div className="fixed inset-0 z-[1200] bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-[#0e1d2c] border border-outline-variant/50 rounded-xl max-w-lg w-full p-space-md shadow-2xl flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">verified</span>
                <span className="font-headline-sm font-bold text-on-surface text-[15px]">
                  Operational Data Provenance
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowProvenanceModal(false)}
                className="p-1 rounded hover:bg-surface-container text-outline hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <div className="flex items-center justify-between bg-surface-container p-2.5 rounded-lg border border-outline-variant/30 text-[11px] font-mono-data">
              <span className="text-outline">ACTIVE SYSTEM MODE:</span>
              <span className={`px-2 py-0.5 rounded font-bold ${
                systemMode === 'OPERATIONAL_LIVE'
                  ? 'bg-primary/20 text-primary border border-primary/40'
                  : systemMode === 'HISTORICAL_EVENT'
                  ? 'bg-secondary/20 text-secondary border border-secondary/40'
                  : 'bg-tertiary/20 text-tertiary border border-tertiary/40'
              }`}>
                {systemMode}
              </span>
            </div>

            <p className="text-[12px] text-on-surface-variant leading-relaxed">
              RELIEFOS Lite operates as a hybrid decision-support system distinguishing verified real-world telemetry from certified baselines and sandboxed academic drills:
            </p>

            <div className="space-y-1.5 text-[11px] max-h-56 overflow-y-auto pr-1">
              <div className="p-2 rounded bg-surface-container border-l-2 border-primary flex items-start justify-between">
                <div>
                  <span className="font-bold text-on-surface block">Open-Meteo Weather Model</span>
                  <span className="text-outline text-[10px]">Kamrup Metro (26.14°N, 91.73°E) • CC-BY 4.0</span>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-primary/20 text-primary border border-primary/30">
                  LIVE
                </span>
              </div>

              <div className="p-2 rounded bg-surface-container border-l-2 border-primary flex items-start justify-between">
                <div>
                  <span className="font-bold text-on-surface block">OSRM Road Routing Graph</span>
                  <span className="text-outline text-[10px]">OpenStreetMap Highway Topology • ODbL 1.0</span>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-primary/20 text-primary border border-primary/30">
                  LIVE
                </span>
              </div>

              <div className="p-2 rounded bg-surface-container border-l-2 border-secondary flex items-start justify-between">
                <div>
                  <span className="font-bold text-on-surface block">CWC Assam River Gauges (10 Stations)</span>
                  <span className="text-outline text-[10px]">Brahmaputra & Barak Basins • CWC / WRD Baseline + Manual Entry</span>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-secondary/20 text-secondary border border-secondary/30">
                  LAST_KNOWN
                </span>
              </div>

              <div className="p-2 rounded bg-surface-container border-l-2 border-secondary flex items-start justify-between">
                <div>
                  <span className="font-bold text-on-surface block">ASDMA & PWD Emergency Ledgers</span>
                  <span className="text-outline text-[10px]">Road Closures, Shelters, and Incident Streams</span>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-secondary/20 text-secondary border border-secondary/30">
                  MANUAL
                </span>
              </div>

              <div className="p-2 rounded bg-surface-container border-l-2 border-outline flex items-start justify-between">
                <div>
                  <span className="font-bold text-on-surface block">Synthetic Drill Generator</span>
                  <span className="text-outline text-[10px]">Scenarios A–J • Isolated In-Memory Sandbox</span>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-surface-container-high text-outline">
                  SIMULATED
                </span>
              </div>
            </div>

            <div className="pt-2 border-t border-outline-variant/30 flex items-center justify-between text-[11px]">
              <span className="text-[10px] text-outline">Decision-support only • Human review required</span>
              <Link
                to="/data-sources"
                onClick={() => setShowProvenanceModal(false)}
                className="px-3 py-1 rounded bg-primary-container text-on-primary-container font-semibold hover:brightness-110 flex items-center gap-1"
              >
                <span>View Full Registry</span>
                <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      <aside
        className={`fixed left-0 top-0 h-screen w-[250px] bg-surface-container-low border-r border-outline-variant/30 z-50 flex flex-col justify-between overflow-y-auto select-none transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col">
          {/* Brand Header */}
          <div className="h-16 px-space-md border-b border-outline-variant/30 flex items-center justify-between bg-surface-container-lowest">
            <div className="flex items-center gap-space-sm min-w-0">
              <img
                alt="RELIEFOS Lite Logo"
                className="h-8 w-8 object-contain flex-shrink-0"
                src="/reliefos_logo.svg"
              />
              <div className="flex flex-col min-w-0 leading-tight">
                <span className="font-headline-sm text-[15px] font-bold text-on-surface tracking-tight truncate">
                  RELIEFOS Lite
                </span>
                <span className="font-label-sm text-[11px] text-on-surface-variant truncate">
                  Flood Ops • Kamrup Metro
                </span>
              </div>
            </div>
            {/* Mobile close button */}
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden p-1 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface"
              aria-label="Close Navigation"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>

          {/* Operational Matrix Section Label */}
          <div className="px-space-md py-space-xs mt-1">
            <span className="font-label-sm text-[10px] uppercase tracking-wider text-outline font-semibold px-space-xs py-space-xs block">
              Operational Matrix
            </span>
          </div>

          {/* Navigation List */}
          <nav className="flex flex-col space-y-0.5 px-space-xs">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-space-sm px-space-md py-2 rounded transition-colors text-[13px] ${
                    isActive
                      ? 'bg-surface-container text-on-surface font-semibold border-l-2 border-primary-container'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  }`
                }
              >
                <span className="material-symbols-outlined text-[18px]">
                  {item.icon}
                </span>
                <span className="font-body-md truncate">{item.name}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Bottom Status & Operator Card */}
        <div className="flex flex-col border-t border-outline-variant/30 bg-surface-container-lowest p-space-md space-y-2">
          {/* Telemetry Health Ping */}
          <div className="flex items-center justify-between px-space-xs">
            <div className="flex items-center gap-space-xs">
              <span className={`w-2 h-2 rounded-full ${
                telemetryStatus.includes('ONLINE') ? 'bg-primary animate-pulse' : 'bg-error'
              }`}></span>
              <span className={`font-mono-data text-[10px] uppercase font-bold tracking-wider ${
                telemetryStatus.includes('ONLINE') ? 'text-primary' : 'text-error'
              }`}>
                {telemetryStatus}
              </span>
            </div>
          </div>

          {/* Grounded Dynamic Operational Mode & Source Breakdown */}
          <div className="flex flex-col gap-1.5">
            <button
              type="button"
              onClick={() => setShowProvenanceModal(true)}
              className={`w-full px-2.5 py-1.5 rounded border transition-all flex items-center justify-between text-left cursor-pointer shadow-xs ${
                systemMode === 'OPERATIONAL_LIVE'
                  ? 'bg-primary/10 border-primary/30 text-primary hover:bg-primary/15'
                  : systemMode === 'HISTORICAL_EVENT'
                  ? 'bg-secondary/10 border-secondary/30 text-secondary hover:bg-secondary/15'
                  : systemMode === 'SIMULATION_DRILL'
                  ? 'bg-tertiary/10 border-tertiary/30 text-tertiary hover:bg-tertiary/15'
                  : 'bg-surface-container border-outline-variant/40 text-on-surface'
              }`}
              title="Click to view verified Data Source Registry & Provenance"
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  systemMode === 'OPERATIONAL_LIVE'
                    ? 'bg-primary animate-pulse'
                    : systemMode === 'HISTORICAL_EVENT'
                    ? 'bg-secondary'
                    : 'bg-tertiary'
                }`}></span>
                <span className="font-mono-data text-[10.5px] uppercase tracking-wider font-bold truncate">
                  {systemMode === 'OPERATIONAL_LIVE'
                    ? 'OPERATIONAL LIVE'
                    : systemMode === 'HISTORICAL_EVENT'
                    ? 'HISTORICAL ARCHIVE'
                    : systemMode === 'SIMULATION_DRILL'
                    ? 'SIMULATION DRILL'
                    : 'STANDBY'}
                </span>
              </div>
              <span className="material-symbols-outlined text-[14px] text-outline">info</span>
            </button>

            {/* Granular Source Registry Tally */}
            <div className="flex items-center justify-between px-1 text-[9.5px] font-mono-data text-outline">
              <span className="flex items-center gap-1 text-primary font-semibold" title="2 Live Sources: Open-Meteo Weather & OSRM Routing">
                <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                {providerStats.live} LIVE
              </span>
              <span className="text-outline-variant">•</span>
              <span className="flex items-center gap-1 text-secondary font-semibold" title="4 Verified Manual/Baseline: CWC Gauges, ASDMA Alerts, PWD Closures, Shelters">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                {providerStats.manual} MANUAL
              </span>
              <span className="text-outline-variant">•</span>
              <span className="flex items-center gap-1 text-outline font-semibold" title="1 Sandboxed: Academic Scenario Stress Drill Engine">
                <span className="w-1.5 h-1.5 rounded-full bg-outline"></span>
                {providerStats.simulated} DRILL
              </span>
            </div>
          </div>

          {/* User Profile Section (Clickable) */}
          <button
            type="button"
            onClick={() => setIsProfileOpen(true)}
            className="w-full flex items-center gap-space-sm pt-space-xs border-t border-outline-variant/20 hover:bg-surface-container/60 p-1.5 rounded-lg transition-colors text-left group cursor-pointer"
            title="Open Operator Profile & Duty Dossier"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden border border-outline-variant group-hover:border-primary flex items-center justify-center flex-shrink-0 bg-surface-container-high relative">
              {currentUser.avatar_url ? (
                <img
                  src={currentUser.avatar_url}
                  alt={currentUser.name}
                  className="w-full h-full object-cover object-center"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              ) : null}
              <span className="font-mono-data font-bold text-[11px] text-primary absolute pointer-events-none">
                {(currentUser.name || 'OP').slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex flex-col min-w-0 leading-tight flex-1">
              <span className="font-label-md text-[12px] font-semibold text-on-surface truncate group-hover:text-primary transition-colors">
                {currentUser.name}
              </span>
              <span className="font-label-sm text-[10px] text-on-surface-variant truncate">
                {currentUser.agency}
              </span>
            </div>
            <span className="material-symbols-outlined text-[16px] text-outline group-hover:text-primary transition-colors">
              tune
            </span>
          </button>
        </div>
      </aside>

      {/* User Profile Dossier Modal */}
      {isProfileOpen && (
        <Suspense fallback={null}>
          <UserProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
        </Suspense>
      )}
    </>
  );
};

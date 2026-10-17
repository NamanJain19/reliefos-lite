import React, { useState, useEffect, useRef, Suspense } from 'react';
import { getDrillStatus, api } from '../../services/api';
import { useLocationContext } from '../../context/LocationContext';
import { LocationConfig } from '../../config/locationsRegistry';

const UserProfileModal = React.lazy(() =>
  import('./UserProfileModal').then((m) => ({ default: m.UserProfileModal }))
);
const DemoDrillModal = React.lazy(() =>
  import('./DemoDrillModal').then((m) => ({ default: m.DemoDrillModal }))
);

interface Props {
  pageTitle: string;
  onToggleMobileMenu?: () => void;
  onOpenCopilot?: () => void;
}

export const Topbar: React.FC<Props> = ({ pageTitle, onToggleMobileMenu, onOpenCopilot }) => {
  const { selectedLocation, allLocations, setSelectedLocation } = useLocationContext();
  const [locationDropdownOpen, setLocationDropdownOpen] = useState(false);
  const locationRef = useRef<HTMLDivElement>(null);
  const modeRef = useRef<HTMLDivElement>(null);

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isDrillOpen, setIsDrillOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [isDrillLoaded, setIsDrillLoaded] = useState(false);
  const [isDrillExecuted, setIsDrillExecuted] = useState(false);
  const [systemMode, setSystemMode] = useState<string>('OPERATIONAL_LIVE');
  const [modeDropdownOpen, setModeDropdownOpen] = useState(false);
  const [modeLoading, setModeLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ name: string; role: string; avatar_url?: string }>({
    name: 'Insp. S. Sharma',
    role: 'OPERATOR',
    avatar_url: '/officer_sharma.png',
  });

  useEffect(() => {
    getDrillStatus()
      .then((res) => {
        if (res.data && res.data.success) {
          setIsDrillLoaded(Boolean(res.data.is_loaded));
          setIsDrillExecuted(Boolean(res.data.is_executed));
        }
      })
      .catch(() => {});

    api.getSystemMode()
      .then((res) => {
        if (res && res.mode) {
          setSystemMode(res.mode);
        }
      })
      .catch(() => {});

    // Fetch authenticated profile if session active
    if (api.isAuthenticated()) {
      api.getAuthMe()
        .then((u) => {
          if (u) {
            setCurrentUser({ name: u.name, role: u.role, avatar_url: u.avatar_url });
          }
        })
        .catch(() => {});
    } else {
      setCurrentUser({ name: 'Shift Inactive', role: 'LOGIN', avatar_url: undefined });
    }

    const handleProfileUpdated = (e: any) => {
      if (e.detail) {
        setCurrentUser({ name: e.detail.name, role: e.detail.role, avatar_url: e.detail.avatar_url });
      }
    };

    const handleAuthExpired = () => {
      setCurrentUser({ name: 'Shift Inactive', role: 'LOGIN', avatar_url: undefined });
    };

    window.addEventListener('reliefos-profile-updated', handleProfileUpdated);
    window.addEventListener('reliefos-auth-expired', handleAuthExpired);

    // Global outside-click and Escape listeners for location and mode dropdowns
    const handleClickOutside = (e: MouseEvent) => {
      if (locationRef.current && !locationRef.current.contains(e.target as Node)) {
        setLocationDropdownOpen(false);
      }
      if (modeRef.current && !modeRef.current.contains(e.target as Node)) {
        setModeDropdownOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setLocationDropdownOpen(false);
        setModeDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('reliefos-profile-updated', handleProfileUpdated);
      window.removeEventListener('reliefos-auth-expired', handleAuthExpired);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleSwitchMode = async (newMode: string, eventId?: string) => {
    setModeLoading(true);
    try {
      const res = await api.switchSystemMode({ mode: newMode, historical_event_id: eventId });
      const targetMode = res?.current_mode || res?.mode_status?.mode || newMode;
      setSystemMode(targetMode);
      window.dispatchEvent(new CustomEvent('reliefos-mode-changed', { detail: { mode: targetMode } }));
    } catch (err) {
      console.error('Failed to switch system mode:', err);
    } finally {
      setModeLoading(false);
      setModeDropdownOpen(false);
    }
  };

  return (
    <>
      <header className="fixed top-0 lg:left-[250px] left-0 right-0 h-16 bg-surface-container-low/95 backdrop-blur border-b border-outline-variant/30 z-[1100] px-space-md lg:px-space-lg flex items-center justify-between transition-all">
        {/* Left Section: Breadcrumbs and Location Indicator */}
        <div className="flex items-center gap-space-sm sm:gap-space-md">
          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={onToggleMobileMenu}
            className="lg:hidden p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
            aria-label="Open Navigation Menu"
          >
            <span className="material-symbols-outlined text-[22px]">menu</span>
          </button>

          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-md text-[13px]">
            <span className="font-mono-data text-outline">RELIEFOS</span>
            <span className="text-outline">/</span>
            <span className="text-on-surface font-semibold truncate max-w-[110px] sm:max-w-none">{pageTitle}</span>
          </div>
          <div className="h-4 w-px bg-outline-variant/50 hidden md:block"></div>

          {/* Interactive Location Selector Dropdown */}
          <div className="relative" ref={locationRef}>
            <button
              type="button"
              id="navbar-location-selector-btn"
              onClick={() => setLocationDropdownOpen((prev) => !prev)}
              aria-haspopup="listbox"
              aria-expanded={locationDropdownOpen}
              title={`Active Sector: ${selectedLocation.displayName} — Click to select from 9 configured Assam districts`}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition-all cursor-pointer text-left select-none ${
                locationDropdownOpen
                  ? 'bg-surface-container-high border-secondary text-on-surface shadow-md ring-1 ring-secondary/50'
                  : 'bg-surface-container hover:bg-surface-container-high border-outline-variant/40 hover:border-outline-variant text-on-surface'
              }`}
            >
              <span className={`material-symbols-outlined text-[17px] ${
                selectedLocation.operationalTier === 'FULL_OPERATIONAL' ? 'text-primary' : 'text-secondary'
              }`}>
                location_on
              </span>
              <div className="flex items-center gap-1.5">
                <span className="font-label-md text-[12px] text-on-surface font-medium truncate max-w-[130px] sm:max-w-[210px] md:max-w-none">
                  {/* Compact on mobile, full label on desktop */}
                  <span className="sm:hidden">{selectedLocation.shortName}</span>
                  <span className="hidden sm:inline">{selectedLocation.displayName}</span>
                </span>
                <span className={`hidden lg:inline-flex text-[9px] font-mono-data px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                  selectedLocation.operationalTier === 'FULL_OPERATIONAL'
                    ? 'bg-primary/15 text-primary border border-primary/30'
                    : selectedLocation.operationalTier === 'TELEMETRY_MONITORED'
                    ? 'bg-secondary/15 text-secondary border border-secondary/30'
                    : 'bg-surface-container-highest text-outline border border-outline-variant/40'
                }`}>
                  {selectedLocation.tierBadgeText}
                </span>
              </div>
              <span className={`material-symbols-outlined text-[16px] text-on-surface-variant transition-transform duration-200 ${
                locationDropdownOpen ? 'rotate-180 text-secondary' : ''
              }`}>
                arrow_drop_down
              </span>
            </button>

            {/* Dropdown Menu Overlay */}
            {locationDropdownOpen && (
              <div
                role="listbox"
                aria-label="Supported operational districts across Assam"
                className="absolute -right-10 sm:right-auto sm:left-0 mt-2 w-[300px] sm:w-[380px] rounded-lg bg-surface-container-high border border-outline-variant shadow-2xl py-2 z-[1150] animate-fadeIn text-[12px] max-h-[80vh] overflow-y-auto"
              >
                <div className="px-3 py-2 border-b border-outline-variant/30 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-on-surface font-label-md block">ASDMA Operational Sectors</span>
                    <span className="text-[10px] text-outline font-mono-data">Assam River Basins • 9 Monitored Districts</span>
                  </div>
                  <span className="text-[9px] px-2 py-0.5 rounded-full bg-surface-container text-primary font-mono-data font-bold border border-primary/30">
                    {allLocations.length} DISTRICTS
                  </span>
                </div>

                <div className="divide-y divide-outline-variant/10 py-1">
                  {allLocations.map((loc) => {
                    const isSelected = loc.id === selectedLocation.id;
                    return (
                      <button
                        key={loc.id}
                        role="option"
                        aria-selected={isSelected}
                        type="button"
                        onClick={() => {
                          setSelectedLocation(loc);
                          setLocationDropdownOpen(false);
                        }}
                        className={`w-full p-2.5 text-left hover:bg-surface-container transition-all flex items-start gap-2.5 cursor-pointer ${
                          isSelected
                            ? 'bg-surface-container border-l-2 border-secondary font-medium'
                            : 'hover:bg-surface-container/60'
                        }`}
                      >
                        <span className={`material-symbols-outlined text-[18px] mt-0.5 shrink-0 ${
                          isSelected
                            ? 'text-secondary'
                            : loc.operationalTier === 'FULL_OPERATIONAL'
                            ? 'text-primary'
                            : 'text-outline'
                        }`}>
                          {isSelected ? 'check_circle' : 'location_on'}
                        </span>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1 mb-0.5">
                            <span className={`text-[12px] font-semibold truncate ${
                              isSelected ? 'text-secondary' : 'text-on-surface'
                            }`}>
                              {loc.displayName}
                            </span>
                            <span className={`text-[9px] font-mono-data px-1.5 py-0.2 rounded font-bold uppercase shrink-0 ${
                              loc.operationalTier === 'FULL_OPERATIONAL'
                                ? 'bg-primary/15 text-primary border border-primary/30'
                                : loc.operationalTier === 'TELEMETRY_MONITORED'
                                ? 'bg-secondary/15 text-secondary border border-secondary/30'
                                : 'bg-surface-container-highest text-outline border border-outline-variant/40'
                            }`}>
                              {loc.tierBadgeText}
                            </span>
                          </div>

                          <div className="text-[11px] text-on-surface-variant/80 line-clamp-1 mb-1">
                            {loc.description}
                          </div>

                          <div className="flex items-center gap-2 text-[10px] font-mono-data text-outline">
                            <span className="flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                              {loc.stationCount} River {loc.stationCount === 1 ? 'Station' : 'Stations'}
                            </span>
                            <span>•</span>
                            <span className={loc.dataAvailability.zones ? 'text-primary font-semibold' : 'text-outline'}>
                              {loc.dataAvailability.zones ? `${loc.revenueCirclesCount} Revenue Circles` : 'Circles Pending Survey'}
                            </span>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>

                <div className="px-3 pt-2 pb-1 border-t border-outline-variant/30 text-[10px] text-outline flex items-center justify-between">
                  <span>Press <kbd className="font-mono-data bg-surface-container px-1 rounded text-on-surface">Esc</kbd> to dismiss</span>
                  <span className="text-[9px] text-primary/80 font-mono-data">RFC 7946 EPSG:4326</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Section: System Mode Selector, Telemetry, Drill Badge, Alerts, User Profile */}
        <div className="flex items-center gap-space-sm sm:gap-space-md">
          {/* System Mode Selector Dropdown */}
          <div className="relative" ref={modeRef}>
            <button
              type="button"
              onClick={() => setModeDropdownOpen(!modeDropdownOpen)}
              disabled={modeLoading}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition-all cursor-pointer text-[11px] font-mono-data font-bold ${
                systemMode === 'OPERATIONAL_LIVE'
                  ? 'border-primary/50 bg-primary/10 text-primary hover:bg-primary/20'
                  : systemMode === 'HISTORICAL_EVENT'
                  ? 'border-tertiary/50 bg-tertiary/10 text-tertiary hover:bg-tertiary/20'
                  : 'border-secondary/50 bg-secondary/10 text-secondary hover:bg-secondary/20'
              }`}
              title="Switch Operational Mode (Live vs Historical vs Simulation)"
            >
              <span className={`w-2 h-2 rounded-full ${
                systemMode === 'OPERATIONAL_LIVE' ? 'bg-primary animate-pulse' : systemMode === 'HISTORICAL_EVENT' ? 'bg-tertiary' : 'bg-secondary'
              }`}></span>
              <span>
                {systemMode === 'OPERATIONAL_LIVE'
                  ? 'OPERATIONAL LIVE'
                  : systemMode === 'HISTORICAL_EVENT'
                  ? 'HISTORICAL ARCHIVE'
                  : 'SIMULATION DRILL'}
              </span>
              <span className="material-symbols-outlined text-[14px]">expand_more</span>
            </button>

            {modeDropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-lg bg-surface-container-high border border-outline-variant shadow-2xl py-2 z-50 animate-fadeIn text-[12px]">
                <div className="px-3 py-1.5 border-b border-outline-variant/30 flex items-center justify-between">
                  <span className="font-bold text-on-surface font-label-md">System Operational Mode</span>
                  <span className="text-[10px] text-outline font-mono-data">RFC-821</span>
                </div>

                <button
                  type="button"
                  onClick={() => handleSwitchMode('OPERATIONAL_LIVE')}
                  className={`w-full p-2.5 text-left hover:bg-surface-container transition-colors flex flex-col gap-0.5 ${
                    systemMode === 'OPERATIONAL_LIVE' ? 'bg-surface-container border-l-2 border-primary' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-primary flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                      Operational Live Data
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-primary/15 text-primary font-mono-data">DEFAULT</span>
                  </div>
                  <span className="text-on-surface-variant text-[11px]">
                    Real-time Open-Meteo weather, CWC river gauge feeds & OSM road routing.
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleSwitchMode('HISTORICAL_EVENT', 'HIST-GHY-2022-06')}
                  className={`w-full p-2.5 text-left hover:bg-surface-container transition-colors flex flex-col gap-0.5 ${
                    systemMode === 'HISTORICAL_EVENT' ? 'bg-surface-container border-l-2 border-tertiary' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-tertiary flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                      Historical Disaster Archive
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-tertiary/15 text-tertiary font-mono-data">GHY 2022</span>
                  </div>
                  <span className="text-on-surface-variant text-[11px]">
                    Real archived June 2022 Brahmaputra flood with documented sensor outage gaps.
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleSwitchMode('SIMULATION_DRILL')}
                  className={`w-full p-2.5 text-left hover:bg-surface-container transition-colors flex flex-col gap-0.5 ${
                    systemMode === 'SIMULATION_DRILL' ? 'bg-surface-container border-l-2 border-secondary' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-secondary flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                      Controlled Simulation Drill
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-secondary/15 text-secondary font-mono-data">SANDBOX</span>
                  </div>
                  <span className="text-on-surface-variant text-[11px]">
                    Isolated synthetic scenario drill. No mutation of operational inventory or dispatch.
                  </span>
                </button>
              </div>
            )}
          </div>

          {/* Drill Modal Trigger */}
          <button
            type="button"
            onClick={() => setIsDrillOpen(true)}
            className={`hidden md:flex items-center gap-space-xs px-space-sm py-1 rounded border transition-all cursor-pointer ${
              isDrillExecuted
                ? 'border-secondary/60 bg-secondary/15 text-secondary hover:bg-secondary/25 shadow-sm'
                : isDrillLoaded
                ? 'border-primary/60 bg-primary/15 text-primary hover:bg-primary/25 shadow-sm'
                : 'border-tertiary-container/40 bg-surface-container text-tertiary hover:bg-surface-container-high'
            }`}
            title="Drill Scenarios & Injection Parameters"
          >
            <span className="material-symbols-outlined text-[14px]">
              {isDrillExecuted ? 'crisis_alert' : isDrillLoaded ? 'bolt' : 'tune'}
            </span>
            <span className="font-label-sm text-[10px] font-bold uppercase tracking-wider">
              {isDrillExecuted ? 'DRILL ACTIVE' : isDrillLoaded ? 'DRILL STAGED' : 'DRILL CONFIG'}
            </span>
          </button>

          <span className="font-mono-data text-[11px] text-outline hidden xl:inline-block">
            Last Sync: 14:42:10 IST
          </span>

          <div className="h-4 w-px bg-outline-variant/50 hidden lg:inline-block"></div>

          {/* AI Copilot Launch Button */}
          <button
            type="button"
            onClick={onOpenCopilot}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/40 text-primary transition-all cursor-pointer shadow-sm group"
            title="Open ASDMA AI Disaster Copilot (Ctrl+J)"
          >
            <span className="material-symbols-outlined text-[18px] group-hover:rotate-12 transition-transform">
              smart_toy
            </span>
            <span className="text-[12px] font-bold tracking-wide hidden sm:inline">
              AI Copilot
            </span>
            <span className="hidden xl:inline font-mono-data text-[9px] px-1 py-0.5 bg-primary/20 text-primary rounded border border-primary/30">
              Ctrl+J
            </span>
          </button>

          {/* Notifications Button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
              title="Tactical Alerts"
            >
              <span className="material-symbols-outlined text-[20px]">notifications</span>
              <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-error text-on-error rounded-full font-label-sm text-[9px] flex items-center justify-center font-bold">
                4
              </span>
            </button>

            {/* Notifications Dropdown */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-lg bg-surface-container-high border border-outline-variant shadow-2xl py-2 z-50 animate-fadeIn">
                <div className="px-3 py-1.5 border-b border-outline-variant/30 flex items-center justify-between">
                  <span className="font-headline-sm text-[12px] font-bold text-on-surface">Active Operational Alerts</span>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-error text-on-error">4 Unread</span>
                </div>
                <div className="max-h-60 overflow-y-auto divide-y divide-outline-variant/20 text-[12px]">
                  <div className="p-2.5 hover:bg-surface-container transition-colors">
                    <span className="text-tertiary font-bold block">Critical: Zone 01 Embankment Breach</span>
                    <span className="text-on-surface-variant text-[11px]">Brahmaputra stage +0.42m above danger level.</span>
                  </div>
                  <div className="p-2.5 hover:bg-surface-container transition-colors">
                    <span className="text-[#F5B84B] font-bold block">Detour: MG Road Submerged (0.40m)</span>
                    <span className="text-on-surface-variant text-[11px]">Enforce AT Road bypass route for VH-02.</span>
                  </div>
                  <div className="p-2.5 hover:bg-surface-container transition-colors">
                    <span className="text-secondary font-bold block">Shelter Update: Kamrup Girls Camp</span>
                    <span className="text-on-surface-variant text-[11px]">140 / 350 occupied. Potable water can delivery staged.</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Help Button */}
          <button
            type="button"
            className="p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
            title="Operational Manual & System Info"
          >
            <span className="material-symbols-outlined text-[20px]">help</span>
          </button>

          {/* User Profile Button */}
          <button
            type="button"
            onClick={() => setIsProfileOpen(true)}
            className="flex items-center gap-space-xs pl-space-xs p-1 rounded-lg hover:bg-surface-container transition-colors group cursor-pointer"
            title="Open Operator Profile Dossier"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden border border-primary flex items-center justify-center bg-surface-container-high relative">
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
            <div className="flex flex-col text-left leading-none">
              <span className="font-label-sm text-[10px] text-primary font-bold group-hover:text-primary-fixed uppercase tracking-wider">
                {currentUser.role}
              </span>
              <span className="font-label-sm text-[10.5px] text-on-surface truncate max-w-[90px]">
                {currentUser.name}
              </span>
            </div>
          </button>
        </div>
      </header>

      {/* User Profile Dossier Modal */}
      {isProfileOpen && (
        <Suspense fallback={null}>
          <UserProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
        </Suspense>
      )}

      {/* Demonstration Drill Control Modal */}
      {isDrillOpen && (
        <Suspense fallback={null}>
          <DemoDrillModal
            isOpen={isDrillOpen}
            onClose={() => setIsDrillOpen(false)}
            onStatusChange={(loaded, executed) => {
              setIsDrillLoaded(loaded);
              setIsDrillExecuted(executed);
            }}
          />
        </Suspense>
      )}
    </>
  );
};

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'planning' | 'resources' | 'optimization' | 'governance' | 'audit'>('general');
  const [workspaceName, setWorkspaceName] = useState<string>('RELIEFOS Lite');
  const [workspaceSubtitle, setWorkspaceSubtitle] = useState<string>('Flood Monitoring & Disaster Relief Decision Support');
  const [jurisdiction, setJurisdiction] = useState<string>('Assam State Disaster Management Authority (ASDMA) - Kamrup Metro DDMA');
  const [compactTables, setCompactTables] = useState<boolean>(true);
  const [provenanceBadges, setProvenanceBadges] = useState<boolean>(true);
  const [safetyPrompts, setSafetyPrompts] = useState<boolean>(true);
  const [systemMode, setSystemMode] = useState<string>('OPERATIONAL_LIVE');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.getSettings();
        if (data && data.workspace) {
          setWorkspaceName(data.workspace.name || 'RELIEFOS Lite');
          setWorkspaceSubtitle(data.workspace.subtitle || 'Flood Monitoring & Disaster Relief Decision Support');
          setJurisdiction(data.workspace.authorizing_agency || 'Assam State Disaster Management Authority (ASDMA) - Kamrup Metro DDMA');
        }
      } catch (err) {
        console.warn('Using baseline settings', err);
      }
      try {
        const modeData = await api.getSystemMode();
        if (modeData && modeData.mode) {
          setSystemMode(modeData.mode);
        }
      } catch {
        // Fallback
      }
    };
    fetchSettings();
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleExportConfig = () => {
    const configData = {
      system_name: workspaceName,
      subtitle: workspaceSubtitle,
      jurisdiction: jurisdiction,
      region: "Kamrup Metropolitan, Guwahati, Assam",
      center: [26.1445, 91.7362],
      depots: [{ id: "DEPOT-01", name: "Sarusajai Sports Complex Logistics Hub", capacity_kg: 20000 }],
      vehicles: 3,
      zones: 5,
      shelters: 2,
      solver: {
        engine: "Google OR-Tools CP-SAT v9.8",
        stage1_objective: "min_priority_weighted_unmet_demand",
        stage2_objective: "min_fleet_transit_distance",
        epsilon_tolerance: 0.00,
        severance_threshold_m: 0.35
      },
      governance: {
        human_in_the_loop_mandatory: true,
        statutory_form: "Form 8B ASDMA"
      }
    };
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(configData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `RELIEFOS_System_Config_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('System configuration JSON exported successfully.');
  };

  const handleSave = () => {
    showToast('System settings persisted to workspace configuration cache.');
  };

  const handleReset = () => {
    setWorkspaceName('RELIEFOS Lite');
    setWorkspaceSubtitle('Flood Monitoring & Disaster Relief Decision Support');
    setJurisdiction('Assam State Disaster Management Authority (ASDMA) - Kamrup Metro DDMA');
    setCompactTables(true);
    setProvenanceBadges(true);
    setSafetyPrompts(true);
    showToast('Settings reset to ASDMA default operational baseline.');
  };

  return (
    <div className="p-space-md lg:p-space-lg flex flex-col gap-y-space-md max-w-[1920px] mx-auto w-full select-none">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-surface-container-highest border border-primary/40 text-on-surface px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 font-mono-data text-body-sm animate-fade-in">
          <span className="material-symbols-outlined text-primary text-[18px]">verified</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* PAGE HEADER */}
      <header className="bg-surface-container-low rounded-xl p-space-md lg:px-space-lg lg:py-space-md shadow-md border border-outline-variant/30 flex flex-col gap-space-md">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-space-sm flex-wrap">
              <h1 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">System Settings</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-surface-container-high text-secondary border border-secondary/30">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                PROTOTYPE CONFIGURATION MODE
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-4xl">
              Configure workspace preferences, regional planning bounds, optimization objectives, and operational governance across Kamrup Metropolitan.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleExportConfig}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-secondary">file_download</span>
              <span>Export Config (JSON)</span>
            </button>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">restart_alt</span>
              <span>Reset Defaults</span>
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 shadow-sm transition-all"
            >
              <span className="material-symbols-outlined text-[16px]">save</span>
              <span>Save Configuration</span>
            </button>
          </div>
        </div>

        {/* CONTEXT BANNER STRIP */}
        <div className="p-space-sm rounded bg-surface-container-lowest border border-outline-variant/30 flex items-center justify-between flex-wrap gap-y-2 text-[11px] font-mono-data">
          <div className="flex items-center gap-x-4 gap-y-1 flex-wrap text-on-surface-variant">
            <span className="flex items-center gap-1 text-primary">
              <span className="material-symbols-outlined text-[15px]">warehouse</span>
              1 Depot (Sarusajai)
            </span>
            <span className="text-outline-variant">•</span>
            <span className="flex items-center gap-1 text-on-surface">
              <span className="material-symbols-outlined text-[15px] text-secondary">grid_view</span>
              5 Operational Zones
            </span>
            <span className="text-outline-variant">•</span>
            <span className="flex items-center gap-1 text-on-surface">
              <span className="material-symbols-outlined text-[15px] text-primary">local_shipping</span>
              3 Logistics Vehicles
            </span>
            <span className="text-outline-variant">•</span>
            <span className="flex items-center gap-1 text-on-surface">
              <span className="material-symbols-outlined text-[15px] text-tertiary">night_shelter</span>
              2 Shelters
            </span>
          </div>
          <span className="flex items-center gap-1 text-primary font-semibold">
            <span className="material-symbols-outlined text-[15px]">verified_user</span>
            Human-in-the-Loop Decision Support
          </span>
        </div>
      </header>

      {/* TWO-COLUMN WORKSPACE */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-md items-start">
        {/* LEFT COLUMN: CATEGORY NAVIGATION */}
        <div className="xl:col-span-3 flex flex-col gap-space-sm bg-surface-container-low p-space-sm rounded-xl shadow-md sticky top-20">
          <div className="px-space-xs py-1">
            <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">Configuration Subsystems</span>
          </div>
          <nav className="flex flex-col gap-1">
            <button
              onClick={() => setActiveTab('general')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'general'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">tune</span>
                <span>General & UI</span>
              </div>
              {activeTab === 'general' && <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>}
            </button>

            <button
              onClick={() => setActiveTab('planning')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'planning'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">map</span>
                <span>Region & Planning</span>
              </div>
              <span className="font-mono-data text-[10px] text-on-surface-variant">5 ZONES</span>
            </button>

            <button
              onClick={() => setActiveTab('resources')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'resources'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">inventory_2</span>
                <span>Resources & Units</span>
              </div>
              <span className="font-mono-data text-[10px] text-primary">ACTIVE</span>
            </button>

            <button
              onClick={() => setActiveTab('optimization')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'optimization'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">flowsheet</span>
                <span>Optimization (OR-Tools)</span>
              </div>
              <span className="font-mono-data text-[10px] text-secondary">CP-SAT</span>
            </button>

            <button
              onClick={() => setActiveTab('governance')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'governance'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">admin_panel_settings</span>
                <span>Users & Governance</span>
              </div>
              <span className="font-mono-data text-[10px] text-on-surface-variant">ASDMA</span>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`flex items-center justify-between px-space-sm py-2 rounded-lg text-left font-label-md text-label-md transition-colors ${
                activeTab === 'audit'
                  ? 'bg-surface-container text-primary font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">history_toggle_off</span>
                <span>Audit Logs & Integrity</span>
              </div>
              <span className="font-mono-data text-[10px] text-on-surface-variant">SHA256</span>
            </button>
          </nav>

          {/* SYSTEM ENVIRONMENT INDICATOR WIDGET */}
          <div className="mt-4 p-space-sm rounded-lg bg-surface-container space-y-1.5 shadow-inner">
            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="font-label-sm text-label-sm uppercase tracking-wider font-semibold">Instance Topology</span>
              <span className="material-symbols-outlined text-[14px]">dns</span>
            </div>
            <div className="font-mono-data text-mono-data text-on-surface font-semibold">
              {systemMode === 'OPERATIONAL_LIVE' ? 'OPERATIONAL_LIVE_NODE' : systemMode}
            </div>
            <div className="text-[11px] font-mono-data text-on-surface-variant flex flex-col gap-0.5">
              <span>NODE: NODE-GHY-04 (Assam DDMA)</span>
              <span>STORAGE: In-Memory Spatially Partitioned</span>
              <span className="text-primary flex items-center gap-1 mt-1 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                GIS Telemetry Bridge: OK
              </span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: MAIN SETTINGS CANVAS */}
        <div className="xl:col-span-9 flex flex-col gap-space-md">
          {/* A. GENERAL SETTINGS GROUP */}
          {(activeTab === 'general' || activeTab === 'audit') && (
            <section className="flex flex-col gap-space-md bg-surface-container-low p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between border-b pb-2 border-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">tune</span>
                  <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">General Settings & Tactical Workspace</h2>
                </div>
                <span className="font-label-sm text-label-sm text-on-surface-variant font-mono-data">SYS.SCOPE: WORKSPACE_BASE</span>
              </div>

              {/* Workspace Information Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                <div className="flex flex-col gap-1.5">
                  <label className="font-label-md text-label-md text-on-surface-variant">Workspace System Name</label>
                  <input
                    className="h-9 px-3 rounded-lg bg-surface-container text-on-surface font-mono-data text-body-md focus:outline-none focus:ring-1 focus:ring-primary shadow-inner"
                    type="text"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="font-label-md text-label-md text-on-surface-variant">Application Operational Subtitle</label>
                  <input
                    className="h-9 px-3 rounded-lg bg-surface-container text-on-surface font-body-md focus:outline-none focus:ring-1 focus:ring-primary shadow-inner"
                    type="text"
                    value={workspaceSubtitle}
                    onChange={(e) => setWorkspaceSubtitle(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1.5 md:col-span-2">
                  <label className="font-label-md text-label-md text-on-surface-variant">Authorizing Jurisdiction / Lead Organization</label>
                  <input
                    className="h-9 px-3 rounded-lg bg-surface-container text-on-surface font-body-md focus:outline-none focus:ring-1 focus:ring-primary shadow-inner"
                    type="text"
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                  />
                </div>
              </div>

              {/* Localization and Units Matrix */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-space-sm bg-surface-container p-space-sm rounded-lg">
                <div className="flex flex-col gap-1">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">Language</span>
                  <select className="h-8 px-2 rounded-lg bg-surface-container-high text-on-surface font-body-sm text-body-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>English (IN)</option>
                    <option>Assamese (অসমীয়া - Planned)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">Timezone</span>
                  <select className="h-8 px-2 rounded-lg bg-surface-container-high text-on-surface font-body-sm text-body-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>Asia/Kolkata (IST, +05:30)</option>
                    <option>UTC (Coordinated Universal)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">Date Format</span>
                  <div className="h-8 px-2 rounded-lg bg-surface-container-high text-on-surface flex items-center font-mono-data text-body-sm">
                    DD MMM YYYY
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">Time Format</span>
                  <div className="h-8 px-2 rounded-lg bg-surface-container-high text-on-surface flex items-center font-mono-data text-body-sm">
                    24-Hour (HH:mm IST)
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">Standard Units</span>
                  <div className="h-8 px-2 rounded-lg bg-surface-container-high text-primary flex items-center font-mono-data text-body-sm font-semibold">
                    Metric (kg, km, m, L)
                  </div>
                </div>
              </div>

              {/* Display & Tactical UI Preferences */}
              <div className="flex flex-col gap-space-sm">
                <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">Display & Tactical UI Preferences</span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-space-sm">
                  <div className="flex items-center justify-between p-space-sm rounded-lg bg-surface-container">
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md text-on-surface font-semibold">Theme Mode</span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">Optimized for low-light Emergency Operations Centers (EOC)</span>
                    </div>
                    <span className="px-2 py-1 rounded bg-surface-bright text-primary font-mono-data text-label-sm font-semibold">TACTICAL DARK</span>
                  </div>
                  <div className="flex items-center justify-between p-space-sm rounded-lg bg-surface-container">
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md text-on-surface font-semibold">Default Landing View</span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">Immediate operational triage post-authentication</span>
                    </div>
                    <select className="h-8 px-2 rounded-lg bg-surface-container-high text-on-surface font-body-sm text-body-sm focus:outline-none">
                      <option>Operations Overview</option>
                      <option>Live Flood Map (GIS Fullscreen)</option>
                      <option>Demand & Allocation Workbench</option>
                    </select>
                  </div>
                </div>

                {/* Toggles Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-sm mt-1">
                  <label className="flex items-start justify-between p-space-sm rounded-lg bg-surface-container hover:bg-surface-bright/50 cursor-pointer transition-colors">
                    <div className="flex flex-col pr-2">
                      <span className="font-label-md text-label-md text-on-surface font-medium">Compact Data Tables</span>
                      <span className="text-[11px] text-on-surface-variant">Higher data density for multi-zone tabular inspection</span>
                    </div>
                    <input
                      checked={compactTables}
                      onChange={(e) => setCompactTables(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded accent-primary cursor-pointer"
                      type="checkbox"
                    />
                  </label>

                  <label className="flex items-start justify-between p-space-sm rounded-lg bg-surface-container hover:bg-surface-bright/50 cursor-pointer transition-colors">
                    <div className="flex flex-col pr-2">
                      <span className="font-label-md text-label-md text-on-surface font-medium">Data Provenance Badges</span>
                      <span className="text-[11px] text-on-surface-variant">Display ISO-19115 observed/forecast/simulated flags</span>
                    </div>
                    <input
                      checked={provenanceBadges}
                      onChange={(e) => setProvenanceBadges(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded accent-primary cursor-pointer"
                      type="checkbox"
                    />
                  </label>

                  <label className="flex items-start justify-between p-space-sm rounded-lg bg-surface-container hover:bg-surface-bright/50 cursor-pointer transition-colors">
                    <div className="flex flex-col pr-2">
                      <span className="font-label-md text-label-md text-on-surface font-medium">Safety Confirmation Prompts</span>
                      <span className="text-[11px] text-on-surface-variant">Mandatory double-confirmation for solver dispatch</span>
                    </div>
                    <input
                      checked={safetyPrompts}
                      onChange={(e) => setSafetyPrompts(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded accent-primary cursor-pointer"
                      type="checkbox"
                    />
                  </label>
                </div>
              </div>
            </section>
          )}

          {/* B. REGION & PLANNING SCOPE PARAMETERS */}
          {(activeTab === 'planning' || activeTab === 'general') && (
            <section className="flex flex-col gap-space-md bg-surface-container-low p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between border-b pb-2 border-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-[20px]">travel_explore</span>
                  <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Region & Planning Scope Parameters</h2>
                </div>
                <span className="px-2 py-0.5 rounded bg-surface-container text-secondary font-mono-data text-label-sm font-semibold">KAMRUP_METRO_V2</span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
                {/* Left: Jurisdiction & Spatial Anchor */}
                <div className="lg:col-span-6 flex flex-col gap-space-sm bg-surface-container p-space-sm rounded-lg">
                  <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">Operational Spatial Anchor</span>
                  <div className="space-y-2 text-body-sm font-body-sm">
                    <div className="flex justify-between items-center py-1 border-b border-surface-container-high">
                      <span className="text-on-surface-variant">Administrative Region</span>
                      <span className="font-medium text-on-surface">Kamrup Metropolitan (Assam)</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-surface-container-high">
                      <span className="text-on-surface-variant">Primary Urban Center</span>
                      <span className="font-medium text-on-surface">Guwahati Urban Agglomeration</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-surface-container-high">
                      <span className="text-on-surface-variant">GIS Bounding Center</span>
                      <span className="font-mono-data text-primary">26.1445° N, 91.7362° E (EPSG:4326)</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-surface-container-high">
                      <span className="text-on-surface-variant">Default GIS Zoom Level</span>
                      <span className="font-mono-data text-secondary">12.5x (Tactical Basin Scale)</span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-on-surface-variant">Active Boundary Shapefile</span>
                      <span className="font-mono-data text-xs px-2 py-0.5 rounded bg-surface-bright text-on-surface">asdma_kamrup_metro_v2.geojson</span>
                    </div>
                  </div>
                </div>

                {/* Right: MVP Architecture Overview */}
                <div className="lg:col-span-6 flex flex-col justify-between gap-space-sm bg-surface-container p-space-sm rounded-lg">
                  <div>
                    <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">MVP Operational Footprint</span>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div className="p-2 rounded bg-surface-container-high">
                        <div className="font-label-sm text-label-sm text-on-surface-variant">Operational Zones</div>
                        <div className="font-mono-data text-headline-sm font-bold text-on-surface">05 Sectors</div>
                        <div className="text-[11px] text-on-surface-variant truncate">Z01 N-Ghy to Z05 Dispur</div>
                      </div>
                      <div className="p-2 rounded bg-surface-container-high">
                        <div className="font-label-sm text-label-sm text-on-surface-variant">Logistics Hub</div>
                        <div className="font-mono-data text-headline-sm font-bold text-primary">01 Primary</div>
                        <div className="text-[11px] text-on-surface-variant truncate">Sarusajai Depot (DEPOT-01)</div>
                      </div>
                      <div className="p-2 rounded bg-surface-container-high">
                        <div className="font-label-sm text-label-sm text-on-surface-variant">Relief Fleet</div>
                        <div className="font-mono-data text-headline-sm font-bold text-secondary">03 Vehicles</div>
                        <div className="text-[11px] text-on-surface-variant truncate">Tata 407, AL 4x4, Bolero</div>
                      </div>
                      <div className="p-2 rounded bg-surface-container-high">
                        <div className="font-label-sm text-label-sm text-on-surface-variant">Staging Shelters</div>
                        <div className="font-mono-data text-headline-sm font-bold text-tertiary">02 Active</div>
                        <div className="text-[11px] text-on-surface-variant truncate">Amingaon, Kamrup Girls HS</div>
                      </div>
                    </div>
                  </div>
                  <div className="p-2 rounded bg-surface-bright/40 text-[11px] text-on-surface-variant flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px] text-secondary">info</span>
                    <span>Multi-depot topology and cross-district scaling unlocked in ASDMA Enterprise Cluster v3.0.</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* C. RESOURCES & UNITS CONFIGURATION */}
          {(activeTab === 'resources' || activeTab === 'general') && (
            <section className="flex flex-col gap-space-md bg-surface-container-low p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between border-b pb-2 border-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">layers</span>
                  <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Resource Taxonomy & Physical Inventory Decoupling</h2>
                </div>
                <span className="px-2 py-0.5 rounded bg-surface-container text-primary font-mono-data text-label-sm font-semibold">LEDGER_ISOLATION_PASS</span>
              </div>

              {/* Resource Definitions Table */}
              <div className="overflow-x-auto rounded-lg bg-surface-container shadow-inner">
                <table className="w-full text-left font-body-sm text-body-sm">
                  <thead className="bg-surface-container-high font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                    <tr>
                      <th className="px-3 py-2">Resource Class</th>
                      <th className="px-3 py-2">Payload Unit</th>
                      <th className="px-3 py-2">Equivalence / Density Reference</th>
                      <th className="px-3 py-2">Allocation Scope</th>
                      <th className="px-3 py-2 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-variant font-mono-data text-body-sm">
                    <tr className="hover:bg-surface-bright/30 transition-colors">
                      <td className="px-3 py-2 font-medium text-on-surface flex items-center gap-2 font-sans">
                        <span className="material-symbols-outlined text-primary text-[18px]">rice_bowl</span>
                        Food Ration Kits (Dry Bulk)
                      </td>
                      <td className="px-3 py-2 text-primary font-bold">kg</td>
                      <td className="px-3 py-2 text-on-surface-variant">1 Standard Ration = 1.0 kg (Normalized)</td>
                      <td className="px-3 py-2 text-on-surface font-sans">Per-Capita Demand (Sphere Standards)</td>
                      <td className="px-3 py-2 text-right">
                        <span className="px-2 py-0.5 rounded bg-primary/20 text-primary font-label-sm font-semibold">ACTIVE</span>
                      </td>
                    </tr>
                    <tr className="hover:bg-surface-bright/30 transition-colors">
                      <td className="px-3 py-2 font-medium text-on-surface flex items-center gap-2 font-sans">
                        <span className="material-symbols-outlined text-secondary text-[18px]">water_drop</span>
                        Potable Drinking Water
                      </td>
                      <td className="px-3 py-2 text-secondary font-bold">kg (Weight Equivalent)</td>
                      <td className="px-3 py-2 text-on-surface-variant">1.0 L ≈ 1.0 kg (Water Density at 20°C)</td>
                      <td className="px-3 py-2 text-on-surface font-sans">3.0 L / person / day Base Threshold</td>
                      <td className="px-3 py-2 text-right">
                        <span className="px-2 py-0.5 rounded bg-secondary/20 text-secondary font-label-sm font-semibold">ACTIVE</span>
                      </td>
                    </tr>
                    <tr className="hover:bg-surface-bright/30 transition-colors opacity-60">
                      <td className="px-3 py-2 font-medium text-on-surface flex items-center gap-2 font-sans">
                        <span className="material-symbols-outlined text-on-surface-variant text-[18px]">medical_services</span>
                        Non-Food Items (Tarps, First-Aid Kits)
                      </td>
                      <td className="px-3 py-2 text-on-surface-variant">Units / Bundles</td>
                      <td className="px-3 py-2 text-on-surface-variant">Weight Varies (Not factored in MILP v2)</td>
                      <td className="px-3 py-2 text-on-surface font-sans">Shelter Staging Points Only</td>
                      <td className="px-3 py-2 text-right">
                        <span className="px-2 py-0.5 rounded bg-surface-variant text-on-surface-variant font-label-sm">PLANNED (LOCKED)</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Stepper Diagram */}
              <div className="flex flex-col gap-2 bg-surface-container p-space-sm rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">Human-in-the-Loop Safe Allocation Pipeline</span>
                  <span className="font-mono-data text-xs text-primary font-semibold">STATELESS IN-MEMORY SOLVER PIPELINE</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-5 gap-2 my-2">
                  <div className="flex flex-col p-2.5 rounded-lg bg-surface-container-high border-l-2 border-primary">
                    <span className="font-mono-data text-[10px] text-on-surface-variant">STAGE 01</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold mt-0.5">Physical Stock</span>
                    <span className="text-[11px] text-on-surface-variant">Sarusajai Depot Ledger</span>
                  </div>
                  <div className="flex flex-col p-2.5 rounded-lg bg-surface-container-high border-l-2 border-secondary">
                    <span className="font-mono-data text-[10px] text-on-surface-variant">STAGE 02</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold mt-0.5">Reserved Buffer</span>
                    <span className="text-[11px] text-on-surface-variant">15% Disaster Reserve</span>
                  </div>
                  <div className="flex flex-col p-2.5 rounded-lg bg-surface-container-high border-l-2 border-primary">
                    <span className="font-mono-data text-[10px] text-on-surface-variant">STAGE 03</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold mt-0.5">Solver Proposal</span>
                    <span className="text-[11px] text-on-surface-variant">In-Memory MILP Draft</span>
                  </div>
                  <div className="flex flex-col p-2.5 rounded-lg bg-surface-container-high border-l-2 border-tertiary">
                    <span className="font-mono-data text-[10px] text-on-surface-variant">STAGE 04</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold mt-0.5">Human Approval</span>
                    <span className="text-[11px] text-on-surface-variant">ASDMA Operator Sign-off</span>
                  </div>
                  <div className="flex flex-col p-2.5 rounded-lg bg-surface-container-high border-l-2 border-primary">
                    <span className="font-mono-data text-[10px] text-on-surface-variant">STAGE 05</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold mt-0.5">Dispatch Manifest</span>
                    <span className="text-[11px] text-on-surface-variant">Fleet Gate Pass Issued</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-surface-container-lowest text-[11px] text-on-surface-variant flex items-start gap-2">
                  <span className="material-symbols-outlined text-[16px] text-primary shrink-0 mt-0.5">verified</span>
                  <p>
                    <strong className="text-on-surface">Decision-Support Isolation Guarantee:</strong> Automated simulations and draft allocations operate strictly in memory cache. At no point does an algorithmic run modify authoritative warehouse inventory ledgers until explicit human validation is authenticated.
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* D. OPTIMIZATION ENGINE & SOLVER GUARDRAILS */}
          {(activeTab === 'optimization' || activeTab === 'general') && (
            <section className="flex flex-col gap-space-md bg-surface-container-low p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between border-b pb-2 border-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-[20px]">smart_toy</span>
                  <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Optimization Engine & Solver Guardrails (Google OR-Tools CP-SAT)</h2>
                </div>
                <span className="px-2 py-0.5 rounded bg-surface-container text-secondary font-mono-data text-label-sm font-semibold">LEXICOGRAPHIC_EPSILON_0.00</span>
              </div>

              {/* Objective Hierarchy Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                <div className="flex flex-col gap-2 p-space-sm rounded-lg bg-surface-container border-l-4 border-primary">
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm text-primary font-bold tracking-wider">PRIMARY OBJECTIVE (STAGE 1 MILP)</span>
                    <span className="font-mono-data text-[11px] text-on-surface-variant">DOMINANT GOAL</span>
                  </div>
                  <div className="font-headline-sm text-headline-sm text-on-surface font-semibold">Minimize Priority-Weighted Unmet Demand</div>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Zones categorized as Critical Risk (Z02 Bharalumukh & Z01 North Guwahati) receive disproportionately heavy penalty weightings. Solvers enforce maximum possible demand satisfaction before route length is considered.
                  </p>
                  <div className="mt-1 font-mono-data text-[11px] text-primary bg-surface-container-high p-1.5 rounded">
                    minimize ∑ (w_zone × unmet_ration_kg)
                  </div>
                </div>

                <div className="flex flex-col gap-2 p-space-sm rounded-lg bg-surface-container border-l-4 border-secondary">
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm text-secondary font-bold tracking-wider">SECONDARY OBJECTIVE (STAGE 2 LEXICOGRAPHIC)</span>
                    <span className="font-mono-data text-[11px] text-on-surface-variant">ε = 0.00% TOLERANCE</span>
                  </div>
                  <div className="font-headline-sm text-headline-sm text-on-surface font-semibold">Minimize Total Fleet Transit Distance</div>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Once maximum relief throughput is locked, the solver re-runs to optimize vehicle traversal distance across accessible road networks without conceding even 1 kg of allocated relief.
                  </p>
                  <div className="mt-1 font-mono-data text-[11px] text-secondary bg-surface-container-high p-1.5 rounded">
                    minimize ∑ (dist_km) subject to unmet ≤ unmet_optimal
                  </div>
                </div>
              </div>

              {/* Vehicle & Routing Constraints Form */}
              <div className="flex flex-col gap-space-sm bg-surface-container p-space-sm rounded-lg">
                <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">Vehicle & Hydro-Routing Constraints</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-sm">
                  <div className="p-2.5 rounded bg-surface-container-high flex flex-col gap-1">
                    <span className="text-on-surface-variant text-[11px]">Fleet Gross Capacity Limit</span>
                    <span className="font-mono-data text-body-lg font-bold text-on-surface">5,000 kg</span>
                    <span className="text-[10px] text-on-surface-variant">Combined Payload (3 Trucks)</span>
                  </div>
                  <div className="p-2.5 rounded bg-surface-container-high flex flex-col gap-1">
                    <span className="text-on-surface-variant text-[11px]">Severance Depth Threshold</span>
                    <span className="font-mono-data text-body-lg font-bold text-tertiary">0.35 m (35 cm)</span>
                    <span className="text-[10px] text-tertiary">Inundation Closes Road Edge</span>
                  </div>
                  <div className="p-2.5 rounded bg-surface-container-high flex flex-col gap-1">
                    <span className="text-on-surface-variant text-[11px]">Depot Loop Closure</span>
                    <span className="font-mono-data text-body-lg font-bold text-primary">Mandatory</span>
                    <span className="text-[10px] text-on-surface-variant">All routes return to Sarusajai</span>
                  </div>
                  <div className="p-2.5 rounded bg-surface-container-high flex flex-col gap-1">
                    <span className="text-on-surface-variant text-[11px]">Dispatch Wave Mode</span>
                    <span className="font-mono-data text-body-lg font-bold text-secondary">Single-Wave</span>
                    <span className="text-[10px] text-on-surface-variant">Multi-trip scheduled in v3</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* E. USERS & GOVERNANCE HIERARCHY */}
          {(activeTab === 'governance' || activeTab === 'audit') && (
            <section className="flex flex-col gap-space-md bg-surface-container-low p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between border-b pb-2 border-surface-variant">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">admin_panel_settings</span>
                  <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Operator Governance & RBAC Hierarchy</h2>
                </div>
                <span className="font-mono-data text-label-sm text-primary">ASDMA_CERTIFIED</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body-sm text-body-sm">
                  <thead className="bg-surface-container-high text-on-surface-variant font-label-sm uppercase tracking-wider">
                    <tr>
                      <th className="py-2 px-3 rounded-l">Role Tier</th>
                      <th className="py-2 px-3">Designation Title</th>
                      <th className="py-2 px-3">Execution Authority</th>
                      <th className="py-2 px-3">Active Assignee</th>
                      <th className="py-2 px-3 rounded-r text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-container-highest/30 font-mono-data text-body-sm">
                    <tr className="hover:bg-surface-container/50">
                      <td className="py-2.5 px-3 text-primary font-bold">TIER 1</td>
                      <td className="py-2.5 px-3 text-on-surface font-sans font-medium">District Incident Commander</td>
                      <td className="py-2.5 px-3 text-on-surface-variant font-sans">Full Dispatch Sign-off & Override</td>
                      <td className="py-2.5 px-3 text-on-surface">Shri P. Barua, IAS (DC Kamrup)</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className="px-2 py-0.5 rounded bg-primary/20 text-primary font-label-sm font-semibold">AUTHORIZED</span>
                      </td>
                    </tr>
                    <tr className="hover:bg-surface-container/50 bg-surface-container/30">
                      <td className="py-2.5 px-3 text-secondary font-bold">TIER 2</td>
                      <td className="py-2.5 px-3 text-on-surface font-sans font-medium">Disaster Operations Inspector</td>
                      <td className="py-2.5 px-3 text-on-surface-variant font-sans">Trigger Solver & Stage Form 8B</td>
                      <td className="py-2.5 px-3 text-primary font-bold">Insp. S. Sharma (ASDMA Ops)</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className="px-2 py-0.5 rounded bg-secondary/20 text-secondary font-label-sm font-semibold">ACTIVE SESSION</span>
                      </td>
                    </tr>
                    <tr className="hover:bg-surface-container/50">
                      <td className="py-2.5 px-3 text-on-surface-variant font-bold">TIER 3</td>
                      <td className="py-2.5 px-3 text-on-surface font-sans font-medium">Field Logistics Coordinator</td>
                      <td className="py-2.5 px-3 text-on-surface-variant font-sans">Warehouse Stock & Vehicle Check-in</td>
                      <td className="py-2.5 px-3 text-on-surface">H. Das (Sarusajai Hub)</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className="px-2 py-0.5 rounded bg-surface-variant text-on-surface-variant font-label-sm">STATIONED</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

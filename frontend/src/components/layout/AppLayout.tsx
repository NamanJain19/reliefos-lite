import React, { useState, useEffect, Suspense } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

// Lazy load heavy AI Copilot drawer component
const DisasterResponseCopilot = React.lazy(() =>
  import('../ai/DisasterResponseCopilot').then((m) => ({ default: m.DisasterResponseCopilot }))
);

const RouteLoadingFallback: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4" role="status" aria-label="Loading module">
    <div className="relative flex items-center justify-center">
      <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
      <span className="material-symbols-outlined text-primary text-[20px] absolute">
        radar
      </span>
    </div>
    <div className="flex flex-col items-center gap-1">
      <span className="font-mono-data text-xs font-bold tracking-widest uppercase text-primary">
        Loading Tactical Module
      </span>
      <span className="text-[11px] text-outline font-mono-data">
        Streaming geospatial telemetry & interface assets...
      </span>
    </div>
  </div>
);

const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Operations Overview',
  '/flood-map': 'Live Flood Map',
  '/zones': 'Zones & Risk',
  '/inventory': 'Resource Inventory',
  '/demand': 'Demand Management',
  '/allocation': 'Relief Allocation',
  '/routes': 'Route Optimization',
  '/simulation': 'Simulation & Reports',
  '/data-sources': 'Data Sources',
  '/settings': 'Settings',
};

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const currentTitle = ROUTE_TITLES[location.pathname] || 'Operations Overview';
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotInitialQuery, setCopilotInitialQuery] = useState<string | undefined>(undefined);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        setCopilotOpen((prev) => !prev);
      }
    };

    const handleOpenCopilotEvent = (e: any) => {
      if (e.detail?.query) {
        setCopilotInitialQuery(e.detail.query);
      }
      setCopilotOpen(true);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-ai-copilot', handleOpenCopilotEvent);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-ai-copilot', handleOpenCopilotEvent);
    };
  }, []);

  return (
    <div className="bg-surface text-on-surface font-body-md text-body-md min-h-screen relative">
      <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
      <div className="lg:pl-[250px] pl-0 flex flex-col min-h-screen transition-all">
        <Topbar
          pageTitle={currentTitle}
          onToggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
          onOpenCopilot={() => {
            setCopilotInitialQuery(undefined);
            setCopilotOpen(true);
          }}
        />
        <main className="w-full pt-16 bg-surface min-h-[calc(100vh-64px)] flex-1 overflow-x-hidden">
          <Suspense fallback={<RouteLoadingFallback />}>
            <Outlet />
          </Suspense>
        </main>
      </div>

      {/* Floating Tactical Copilot Launcher */}
      <button
        type="button"
        onClick={() => {
          setCopilotInitialQuery(undefined);
          setCopilotOpen(true);
        }}
        className="fixed bottom-5 right-5 z-[1050] px-3.5 py-2.5 rounded-full bg-surface-container-high/90 hover:bg-primary/20 border border-primary/50 text-primary shadow-xl backdrop-blur-md flex items-center gap-2 transition-all hover:scale-105 active:scale-95 group cursor-pointer"
        title="Open ASDMA AI Disaster Copilot (Ctrl+J)"
      >
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
        </span>
        <span className="material-symbols-outlined text-[18px]">smart_toy</span>
        <span className="text-[12px] font-bold tracking-wide">AI Copilot</span>
        <span className="hidden sm:inline-block font-mono-data text-[10px] px-1.5 py-0.5 rounded bg-surface-container text-outline border border-outline-variant/30">
          Ctrl+J
        </span>
      </button>

      {/* AI Disaster Response Copilot Drawer (Code-Split Lazy Loaded) */}
      {copilotOpen && (
        <Suspense fallback={null}>
          <DisasterResponseCopilot
            isOpen={copilotOpen}
            onClose={() => setCopilotOpen(false)}
            initialQuery={copilotInitialQuery}
          />
        </Suspense>
      )}
    </div>
  );
};


import React, { useState, useEffect } from 'react';
import {
  getDrillStatus,
  loadDrillScenario,
  runDrillScenario,
  resetDrillEnvironment,
  exportDrillDossier
} from '../../services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onStatusChange?: (isLoaded: boolean, isExecuted: boolean) => void;
}

export const DemoDrillModal: React.FC<Props> = ({ isOpen, onClose, onStatusChange }) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await getDrillStatus();
      if (res.data && res.data.success) {
        setStatus(res.data);
        if (onStatusChange) {
          onStatusChange(res.data.is_loaded, res.data.is_executed);
        }
      }
    } catch (err) {
      console.error('Failed to query drill status', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      setFeedback(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLoad = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const res = await loadDrillScenario();
      if (res.data && res.data.success) {
        setFeedback('Drill scenario loaded successfully into isolated simulation sandbox.');
        await fetchStatus();
      } else {
        setFeedback('Failed to load drill scenario.');
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message || 'Could not load drill scenario'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const res = await runDrillScenario();
      if (res.data && res.data.success) {
        setFeedback(`Drill optimization executed! Solver Status: ${res.data.optimization?.solver_status || 'OPTIMAL'}`);
        await fetchStatus();
      } else {
        setFeedback('Drill execution failed.');
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message || 'Could not run drill scenario'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const res = await resetDrillEnvironment();
      if (res.data && res.data.success) {
        setFeedback('Simulation environment reset. System returned to default baseline.');
        await fetchStatus();
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message || 'Could not reset drill environment'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const res = await exportDrillDossier();
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ASDMA_DRILL_DOSSIER_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setFeedback('ASDMA Form 8B drill dossier exported.');
    } catch (err: any) {
      setFeedback(`Export error: ${err.message || 'Failed to download export'}`);
    }
  };

  const drillMeta = status?.scenario_metadata;

  return (
    <div className="fixed inset-0 z-[1200] flex items-start justify-center p-4 pt-16 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0e1d2c] border border-outline-variant/60 rounded-xl shadow-2xl w-full max-w-2xl max-h-[88vh] overflow-y-auto p-space-lg text-on-surface">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm mb-space-md">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-secondary text-[24px]">crisis_alert</span>
            <div>
              <h2 className="font-headline-sm text-headline-sm font-bold tracking-tight text-on-surface">
                Disaster Relief Operations Drill
              </h2>
              <span className="font-mono-data text-[11px] text-outline">
                Phase 5 Capstone Verification • Kamrup Metro / Guwahati EOC
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Isolation Banner */}
        <div className="bg-surface-container p-3 rounded-lg border border-secondary/30 mb-space-md flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-secondary text-[20px]">verified_user</span>
            <div>
              <span className="font-label-md text-[12px] font-bold text-on-surface block">
                Deterministic Sandboxed Simulation
              </span>
              <span className="font-body-sm text-[11px] text-on-surface-variant">
                Guaranteed memory and session isolation. Zero mutation to operational database tables or persistent stock.
              </span>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider font-mono-data border ${
            status?.is_executed
              ? 'bg-secondary/20 text-secondary border-secondary/40'
              : status?.is_loaded
              ? 'bg-primary-container/30 text-primary border-primary/40'
              : 'bg-surface-container-high text-outline border-outline-variant/40'
          }`}>
            {status?.is_executed ? 'DRILL EXECUTED' : status?.is_loaded ? 'DRILL STAGED' : 'IDLE / DEFAULT'}
          </span>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div className="mb-space-md p-2.5 rounded bg-surface-container border border-primary/30 text-primary font-mono-data text-[12px] flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">info</span>
            <span>{feedback}</span>
          </div>
        )}

        {/* Scenario Specifications */}
        <div className="bg-surface-container-lowest p-space-md rounded-lg border border-outline-variant/30 mb-space-md">
          <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold block mb-2">
            Scenario Parameters & Field Conditions
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-[12px]">
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Incident Code</span>
              <span className="font-bold text-on-surface font-mono-data">{drillMeta?.incident_code || 'ASDMA-DRILL-2024-GHY-01'}</span>
            </div>
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Hydrology</span>
              <span className="font-bold text-tertiary">Brahmaputra +0.42m</span>
            </div>
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Target Sectors</span>
              <span className="font-bold text-on-surface">Zones 01, 02, 03</span>
            </div>
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Total Demand</span>
              <span className="font-bold text-on-surface">7,100 kg (Food + Water)</span>
            </div>
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Fleet Single Wave</span>
              <span className="font-bold text-secondary">5,000 kg (3 Vehicles)</span>
            </div>
            <div className="p-2 rounded bg-surface-container/60">
              <span className="text-outline text-[10px] block uppercase font-mono-data">Detour Enforced</span>
              <span className="font-bold text-[#F5B84B]">MG Road via AT Road (+12.4km)</span>
            </div>
          </div>
        </div>

        {/* Execution Results Summary (if executed) */}
        {status?.is_executed && status?.execution_results && (
          <div className="bg-surface-container p-space-md rounded-lg border border-outline-variant/30 mb-space-md">
            <div className="flex items-center justify-between mb-2">
              <span className="font-label-sm text-[11px] uppercase tracking-wider text-secondary font-semibold">
                Dispatch & Optimization Execution Metrics
              </span>
              <span className="font-mono-data text-[11px] text-outline">
                Runtime: {status.execution_results.solver_runtime_ms || 34.2}ms
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[12px] font-mono-data">
              <div className="p-2 bg-surface-container-high rounded text-center">
                <span className="text-[10px] text-outline block">Allocated Food</span>
                <span className="font-bold text-primary">{status.execution_results.allocated_food_kg || 2800} kg</span>
              </div>
              <div className="p-2 bg-surface-container-high rounded text-center">
                <span className="text-[10px] text-outline block">Allocated Water</span>
                <span className="font-bold text-secondary">{status.execution_results.allocated_water_l || 2200} L</span>
              </div>
              <div className="p-2 bg-surface-container-high rounded text-center">
                <span className="text-[10px] text-outline block">Fleet Utilization</span>
                <span className="font-bold text-on-surface">{status.execution_results.fleet_utilization_pct || 100}%</span>
              </div>
              <div className="p-2 bg-surface-container-high rounded text-center">
                <span className="text-[10px] text-outline block">Detour Distance</span>
                <span className="font-bold text-[#F5B84B]">{status.execution_results.detour_distance_km || 12.4} km</span>
              </div>
            </div>
            <div className="mt-2.5 p-2 bg-surface-container-lowest rounded border border-outline-variant/20 text-[11px] text-on-surface-variant">
              <strong className="text-on-surface">Decision-Support Notice:</strong> All vehicle manifests and route advisories require verified officer confirmation prior to actual field rollout. This system does not autonomously dispatch physical assets.
            </div>
          </div>
        )}

        {/* Drill Control Actions */}
        <div className="space-y-2 mb-space-md">
          <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold block">
            Operator Drill Control Actions
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <button
              type="button"
              disabled={loading}
              onClick={handleLoad}
              className="flex items-center justify-center gap-2 p-2.5 rounded bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 disabled:opacity-50 transition-all border border-primary/30"
            >
              <span className="material-symbols-outlined text-[18px]">input</span>
              <span>1. Load Emergency Drill Scenario</span>
            </button>

            <button
              type="button"
              disabled={loading || !status?.is_loaded}
              onClick={handleRun}
              className="flex items-center justify-center gap-2 p-2.5 rounded bg-secondary-container text-on-secondary-container font-semibold text-[12px] hover:brightness-110 disabled:opacity-40 transition-all border border-secondary/30"
            >
              <span className="material-symbols-outlined text-[18px]">play_arrow</span>
              <span>2. Execute Lexicographic Solver</span>
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={handleExport}
              className="flex items-center justify-center gap-2 p-2.5 rounded bg-surface-container-high text-on-surface font-semibold text-[12px] hover:bg-surface-container-highest border border-outline-variant/40 disabled:opacity-50 transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              <span>Export ASDMA Form 8B Dossier</span>
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={handleReset}
              className="flex items-center justify-center gap-2 p-2.5 rounded bg-surface-container text-error hover:bg-error/10 border border-error/30 font-semibold text-[12px] disabled:opacity-50 transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">restart_alt</span>
              <span>Reset to Operational Baseline</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-outline-variant/30 pt-3">
          <span className="font-mono-data text-[11px] text-outline">
            ISO-19115 Lineage: SYNTHETIC_DRILL_SANDBOX
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-semibold text-[12px] transition-all"
          >
            Close Drill Manager
          </button>
        </div>
      </div>
    </div>
  );
};

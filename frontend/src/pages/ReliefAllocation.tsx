import React, { useState, useEffect } from 'react';
import {
  api,
  getLogisticsPlan,
  getLogisticsStrategies,
  simulateWhatIfScenario,
  reviewLogisticsPlan,
  LogisticsAdvisorPlanResponse,
  AlternativeStrategyComparisonItem,
  ZoneLogisticsRecommendation,
  RouteSummaryInfo,
  WhatIfScenarioResponse
} from '../services/api';
import { TacticalGisMap } from '../components/map/TacticalGisMap';
import { getGisChokepointForLocation } from '../components/map/gisLayersData';
import { useLocationContext } from '../context/LocationContext';

export const ReliefAllocation: React.FC = () => {
  const { selectedLocation, isKamrupMetro } = useLocationContext();
  // Main Plan State
  const [activeStrategy, setActiveStrategy] = useState<string>('LEXICOGRAPHIC_SEVERITY_OPTIMAL');
  const [plan, setPlan] = useState<LogisticsAdvisorPlanResponse | null>(null);
  const [strategies, setStrategies] = useState<AlternativeStrategyComparisonItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingSolver, setLoadingSolver] = useState<boolean>(false);
  const [selectedZone, setSelectedZone] = useState<string>('ZONE 01');
  const [activeViewTab, setActiveViewTab] = useState<'plan' | 'strategies' | 'diagnostics'>('plan');

  // Modal States
  const [whatIfModalOpen, setWhatIfModalOpen] = useState<boolean>(false);
  const [reviewModalOpen, setReviewModalOpen] = useState<boolean>(false);

  // What-If Sandbox State
  const [whatIfTitle, setWhatIfTitle] = useState<string>('Brahmaputra Flood Surge Simulation');
  const [customFoodStock, setCustomFoodStock] = useState<number>(3500);
  const [customWaterStock, setCustomWaterStock] = useState<number>(3500);
  const [disabledVehicles, setDisabledVehicles] = useState<string[]>([]);
  const [severedZones, setSeveredZones] = useState<string[]>([]);
  const [demandMultiplier, setDemandMultiplier] = useState<number>(1.2);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfScenarioResponse | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState<boolean>(false);

  // Human Review & Sign-Off State
  const [reviewAction, setReviewAction] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [operatorName, setOperatorName] = useState<string>('Insp. S. Sharma (EOC Planner)');
  const [reviewNotes, setReviewNotes] = useState<string>(
    'Reviewed against CWC Pandu Gauge (49.68m) and ASDMA Form 8B. Priority allocations to North Guwahati and Bharalumukh verified for staging at Sarusajai Central Logistics Hub.'
  );
  const [form8bRef, setForm8bRef] = useState<string>('ASDMA-F8B-2026-10-04-LOG-01');
  const [reviewLoading, setReviewLoading] = useState<boolean>(false);
  const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);

  // Load logistics plan on strategy switch or location switch
  const fetchPlan = async (strategy: string) => {
    setLoading(true);
    try {
      const res = await getLogisticsPlan(strategy);
      if (res && res.data) {
        setPlan(res.data);
      }
    } catch (err) {
      console.error('Failed to load logistics plan:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load all strategy comparisons
  const fetchStrategies = async () => {
    try {
      const res = await getLogisticsStrategies();
      if (res && res.data) {
        setStrategies(res.data);
      }
    } catch (err) {
      console.error('Failed to load strategy comparisons:', err);
    }
  };

  useEffect(() => {
    fetchPlan(activeStrategy);
    fetchStrategies();
    setReviewNotes(
      isKamrupMetro
        ? 'Reviewed against CWC Pandu Gauge (49.68m) and ASDMA Form 8B. Priority allocations to North Guwahati and Bharalumukh verified for staging at Sarusajai Central Logistics Hub.'
        : `Reviewed against ${selectedLocation.primaryRiver} CWC gauge and ASDMA Form 8B. Priority allocations verified for staging at ${selectedLocation.primaryDepot}.`
    );
  }, [activeStrategy, selectedLocation.id, isKamrupMetro]);

  // Execute solver re-optimization
  const handleTriggerReoptimization = async () => {
    setLoadingSolver(true);
    try {
      await fetchPlan(activeStrategy);
      await fetchStrategies();
    } finally {
      setLoadingSolver(false);
    }
  };

  // Run What-If Simulation
  const handleExecuteWhatIf = async () => {
    setWhatIfLoading(true);
    try {
      const res = await simulateWhatIfScenario({
        scenario_title: whatIfTitle,
        location_id: selectedLocation.id,
        custom_stock_food_kg: customFoodStock,
        custom_stock_water_kg: customWaterStock,
        disabled_vehicles: disabledVehicles,
        severed_zones: severedZones,
        demand_multiplier: demandMultiplier,
        strategy: activeStrategy
      });
      if (res && res.data) {
        setWhatIfResult(res.data);
      }
    } catch (err) {
      console.error('What-If simulation failed:', err);
    } finally {
      setWhatIfLoading(false);
    }
  };

  // Submit Human Review & Sign-Off
  const handleSubmitReview = async () => {
    setReviewLoading(true);
    setReviewFeedback(null);
    try {
      const res = await reviewLogisticsPlan({
        action: reviewAction,
        operator_name: operatorName,
        review_notes: reviewNotes,
        form_8b_reference: form8bRef,
        disclaimer_acknowledged: true
      });
      if (res && res.data && res.data.success) {
        setReviewFeedback(`Plan successfully ${res.data.review_status}. Audit record logged (ID #${res.data.audit_log_id}).`);
        if (plan) {
          setPlan({ ...plan, review_status: res.data.review_status });
        }
        setTimeout(() => {
          setReviewModalOpen(false);
          setReviewFeedback(null);
        }, 1800);
      }
    } catch (err: any) {
      setReviewFeedback(`Review failed: ${err.message || err}`);
    } finally {
      setReviewLoading(false);
    }
  };

  // Export ASDMA Official Manifest
  const handleExportManifest = () => {
    if (!plan) return;
    const manifest = {
      system: 'RELIEFOS Lite — AI-Assisted Resource Allocation & Logistics Advisor',
      plan_id: plan.plan_id,
      plan_version: plan.plan_version,
      generated_at: plan.generated_at,
      active_strategy: plan.active_strategy,
      solver_engine: plan.solver_engine,
      planning_region: `${selectedLocation.displayName}, Assam`,
      depot: `${selectedLocation.primaryDepot} [DEPOT-${selectedLocation.shortName.toUpperCase()}]`,
      summary: {
        total_demand_kg: plan.total_demand_kg,
        total_allocated_kg: plan.total_allocated_kg,
        total_unmet_kg: plan.total_unmet_kg,
        coverage_ratio_pct: plan.coverage_ratio_pct,
        total_transit_distance_km: plan.total_transit_distance_km,
        est_fuel_burn_liters: plan.est_total_fuel_burn_liters,
        active_vehicles_count: plan.active_vehicles_count
      },
      zones: plan.zones,
      routes: plan.routes,
      diagnostics: plan.diagnostics,
      review_status: plan.review_status,
      review_details: plan.review_details,
      safety_disclaimer: plan.safety_disclaimer
    };

    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ASDMA_Logistics_Plan_${plan.plan_id}_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const selectedZoneData = plan?.zones.find((z) => z.zone_code === selectedZone) || plan?.zones[0];

  return (
    <div className="p-space-md lg:p-space-lg flex flex-col gap-y-space-md max-w-[1920px] mx-auto w-full select-none text-on-surface">
      {/* 1. Header & Operational Control Bar */}
      <header className="bg-surface-container-low rounded-xl p-space-md lg:px-space-lg lg:py-space-md shadow-md border border-outline-variant/30 flex flex-col gap-space-md">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-space-sm flex-wrap">
              <h1 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[28px]">hub</span>
                <span>Resource Allocation & Logistics Advisor</span>
              </h1>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-surface-container-high text-primary border border-primary/30 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <span>Google OR-Tools CP-SAT MILP</span>
              </span>
              <span
                className={`px-2.5 py-0.5 rounded text-[11px] font-bold uppercase border flex items-center gap-1 ${
                  plan?.review_status === 'APPROVED'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : plan?.review_status === 'REJECTED'
                    ? 'bg-error/20 text-error border-error/30'
                    : 'bg-[#f5b84b]/20 text-[#f5b84b] border-[#f5b84b]/30'
                }`}
              >
                <span className="material-symbols-outlined text-[14px]">
                  {plan?.review_status === 'APPROVED' ? 'verified' : 'pending_actions'}
                </span>
                <span>{plan?.review_status === 'APPROVED' ? 'Form 8B Authorized' : 'Awaiting Operational Review'}</span>
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-4xl">
              Mathematically optimal, two-stage lexicographic dispatch planning. Minimizes flood-hazard weighted unmet demand
              (Stage 1) while strictly minimizing fleet travel distance and detour fuel burn (Stage 2).
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setReviewModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 text-primary text-[12px] border border-primary/30 font-semibold transition-all shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">how_to_reg</span>
              <span>Human Review & Sign-Off</span>
            </button>
            <button
              onClick={() => setWhatIfModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-tertiary">science</span>
              <span>What-If Sandbox</span>
            </button>
            <button
              onClick={handleExportManifest}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">file_download</span>
              <span>Export Manifest</span>
            </button>
            <button
              onClick={handleTriggerReoptimization}
              disabled={loadingSolver}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 shadow-sm transition-all disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[16px] ${loadingSolver ? 'animate-spin' : ''}`}>
                {loadingSolver ? 'sync' : 'play_arrow'}
              </span>
              <span>{loadingSolver ? 'Solving...' : 'Re-Run Solver'}</span>
            </button>
          </div>
        </div>

        {/* Non-metro tactical sector banner */}
        {!isKamrupMetro && (
          <div className="p-3.5 my-2 rounded-xl bg-primary/5 border border-primary/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-primary">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[24px]">location_on</span>
              <div>
                <div className="font-bold text-[13px] tracking-wide uppercase">
                  OPERATIONAL SECTOR: {selectedLocation.displayName.toUpperCase()}
                </div>
                <div className="text-[12px] text-on-surface-variant mt-0.5">
                  Relief allocations for {selectedLocation.displayName} are staged via {selectedLocation.primaryDepot}. Multi-objective lexicographic MILP optimizes sector delivery and contingency buffer dispatch.
                </div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded text-[11px] font-bold uppercase bg-primary/15 border border-primary/30 shrink-0 self-start sm:self-auto">
              {selectedLocation.tierBadgeText}
            </span>
          </div>
        )}

        {/* Strategy Selector Strip */}
        <div className="pt-2 border-t border-outline-variant/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-center gap-1 bg-surface-container p-1 rounded-lg flex-wrap">
            <span className="text-[11px] font-bold uppercase tracking-wider text-outline px-2">STRATEGY:</span>
            {[
              { id: 'LEXICOGRAPHIC_SEVERITY_OPTIMAL', label: 'Lexicographic Severity (ASDMA Rec.)', icon: 'verified' },
              { id: 'PROPORTIONAL_EQUAL_SHARE', label: 'Uniform Equity (Equal Share)', icon: 'balance' },
              { id: 'DISTANCE_MINIMIZING_PROXIMITY', label: 'Proximity / Fast Turnaround', icon: 'speed' },
              { id: 'WATER_FIRST_SURVIVAL', label: 'Strict Hydration Survival', icon: 'water_drop' }
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setActiveStrategy(st.id)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-medium transition-all ${
                  activeStrategy === st.id
                    ? 'bg-primary-container text-on-primary-container font-bold shadow-sm'
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
                }`}
              >
                <span className="material-symbols-outlined text-[14px]">{st.icon}</span>
                <span>{st.label}</span>
              </button>
            ))}
          </div>

          {/* Navigation View Tabs */}
          <div className="flex items-center gap-1 bg-surface-container p-1 rounded-lg text-[11px]">
            <button
              onClick={() => setActiveViewTab('plan')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeViewTab === 'plan'
                  ? 'bg-surface-container-high text-primary font-bold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Recommended Plan
            </button>
            <button
              onClick={() => setActiveViewTab('strategies')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeViewTab === 'strategies'
                  ? 'bg-surface-container-high text-primary font-bold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Strategy Comparison ({strategies.length})
            </button>
            <button
              onClick={() => setActiveViewTab('diagnostics')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeViewTab === 'diagnostics'
                  ? 'bg-surface-container-high text-primary font-bold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Diagnostics & Constraints
            </button>
          </div>
        </div>

        {/* Telemetry & Provenance Breadcrumb */}
        <div className="p-2 rounded bg-surface-container-lowest border border-outline-variant/30 flex items-center justify-between flex-wrap gap-2 text-[11px] font-mono-data text-on-surface-variant">
          <div className="flex items-center gap-4 flex-wrap">
            <div>
              <span className="text-outline">Depot Hub:</span>{' '}
              <span className="text-secondary font-semibold">{selectedLocation.primaryDepot} (Local Fleet)</span>
            </div>
            <span>•</span>
            <div>
              <span className="text-outline">CWC Telemetry:</span>{' '}
              <span className="text-on-surface font-semibold">{selectedLocation.primaryRiver} Basin</span>
            </div>
            <span>•</span>
            <div>
              <span className="text-outline">Active Chokepoint:</span>{' '}
              <span className="text-[#f5b84b] font-semibold">
                {getGisChokepointForLocation(selectedLocation.id)?.label || 'Corridor Cleared (No active blockage)'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-outline">Plan ID:</span>
            <span className="text-primary font-bold">{plan?.plan_id || 'LOG-PLAN-2026-10-04-01'}</span>
          </div>
        </div>
      </header>

      {/* 2. KPI Summary Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-space-sm">
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>TOTAL VERIFIED DEMAND</span>
            <span className="material-symbols-outlined text-[18px]">demands</span>
          </div>
          <div className="text-kpi-lg font-bold text-on-surface font-mono-data mt-1 tabular-nums">
            {plan?.total_demand_kg.toLocaleString() || '8,350'} <span className="text-xs font-normal text-outline">kg/eq</span>
          </div>
          <span className="text-[11px] text-secondary font-medium">5 Kamrup Operational Zones</span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-primary text-[11px] uppercase font-bold">
            <span>PROPOSED ALLOCATION</span>
            <span className="material-symbols-outlined text-[18px]">verified</span>
          </div>
          <div className="text-kpi-lg font-bold text-primary font-mono-data mt-1 tabular-nums">
            {plan?.total_allocated_kg.toLocaleString() || '5,000'} <span className="text-xs font-normal text-outline">kg</span>
          </div>
          <span className="text-[11px] text-primary font-medium">
            {plan?.coverage_ratio_pct || 59.9}% Citywide Coverage Ratio
          </span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-error text-[11px] uppercase font-bold">
            <span>PROJECTED SHORTFALL</span>
            <span className="material-symbols-outlined text-[18px]">warning</span>
          </div>
          <div className="text-kpi-lg font-bold text-error font-mono-data mt-1 tabular-nums">
            {plan?.total_unmet_kg.toLocaleString() || '3,350'} <span className="text-xs font-normal text-outline">kg</span>
          </div>
          <span className="text-[11px] text-on-surface-variant">Wave 2 Logistics Queue</span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-tertiary text-[11px] uppercase font-bold">
            <span>TOTAL TRANSIT DISTANCE</span>
            <span className="material-symbols-outlined text-[18px]">route</span>
          </div>
          <div className="text-kpi-lg font-bold text-tertiary font-mono-data mt-1 tabular-nums">
            {plan?.total_transit_distance_km || 84.4} <span className="text-xs font-normal text-outline">km</span>
          </div>
          <span className="text-[11px] text-on-surface-variant font-mono-data">
            ~{plan?.est_total_fuel_burn_liters || 26.2} L Est. Diesel Burn
          </span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-secondary text-[11px] uppercase font-bold">
            <span>SOLVER PERFORMANCE</span>
            <span className="material-symbols-outlined text-[18px]">memory</span>
          </div>
          <div className="text-kpi-lg font-bold text-secondary font-mono-data mt-1 tabular-nums">
            {plan?.solver_runtime_ms || 125} <span className="text-xs font-normal text-outline">ms</span>
          </div>
          <span className="text-[11px] text-secondary font-medium uppercase">Status: {plan?.solver_status || 'OPTIMAL'}</span>
        </div>
      </section>

      {/* 3. Main View Switching */}
      {activeViewTab === 'plan' && (
        <>
          {/* AI Copilot Executive Briefing Card */}
          <div className="bg-gradient-to-r from-surface-container-low to-surface-container rounded-xl p-space-md border border-primary/30 shadow-sm flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">smart_toy</span>
                <span className="font-bold text-[13px] text-on-surface uppercase tracking-wider">
                  AI Logistics Advisor Executive Briefing
                </span>
              </div>
              <span className="text-[11px] text-outline font-mono-data">Evidence-Based Rationale</span>
            </div>
            <p className="text-[13px] text-on-surface-variant leading-relaxed">
              {plan?.ai_executive_briefing ||
                'Evaluating two-stage lexicographic distribution against real-time CWC river gauges and PWD road blockages.'}
            </p>
          </div>

          {/* Core Content Grid: Allocations Table + Route Map */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-md">
            {/* Left Column: Zone Logistics Table (7 Cols) */}
            <div className="xl:col-span-7 flex flex-col gap-space-md">
              <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 shadow-sm flex flex-col">
                <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-secondary text-[20px]">table_chart</span>
                    <h2 className="font-bold text-[14px] text-on-surface">Zonal Allocation & Shortfall Ledger</h2>
                  </div>
                  <span className="text-[11px] text-outline font-mono-data">Physical Separation of Food & Water</span>
                </div>

                <div className="overflow-x-auto mt-2">
                  <table className="w-full text-left text-[12px]">
                    <thead>
                      <tr className="border-b border-outline-variant/30 text-outline text-[11px] uppercase font-semibold">
                        <th className="py-2.5 px-3">Zone & Priority</th>
                        <th className="py-2.5 px-3">Demand (Food / Water)</th>
                        <th className="py-2.5 px-3">Allocated (kg / L)</th>
                        <th className="py-2.5 px-3">Shortfall</th>
                        <th className="py-2.5 px-3">Fulfillment</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/20 font-mono-data text-[11px]">
                      {plan?.zones.map((z) => {
                        const isSelected = selectedZone === z.zone_code;
                        return (
                          <tr
                            key={z.zone_code}
                            onClick={() => setSelectedZone(z.zone_code)}
                            className={`cursor-pointer transition-colors ${
                              isSelected ? 'bg-primary-container/20 font-semibold' : 'hover:bg-surface-container/50'
                            }`}
                          >
                            <td className="py-2.5 px-3">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`w-2 h-2 rounded-full ${
                                    z.risk_tier === 'CRITICAL'
                                      ? 'bg-error'
                                      : z.risk_tier === 'HIGH'
                                      ? 'bg-[#f5b84b]'
                                      : 'bg-primary'
                                  }`}
                                />
                                <div>
                                  <span className="font-bold text-on-surface block text-[12px]">{z.zone_code}</span>
                                  <span className="text-[10px] text-outline font-sans block">{z.zone_name}</span>
                                </div>
                              </div>
                            </td>
                            <td className="py-2.5 px-3 tabular-nums">
                              <div>
                                <span className="text-on-surface">{z.total_demand_kg.toLocaleString()} kg</span>
                                <span className="text-[10px] text-outline block">
                                  {z.food_demand_kg}F / {z.water_demand_kg}W
                                </span>
                              </div>
                            </td>
                            <td className="py-2.5 px-3 tabular-nums">
                              <span className="text-primary font-bold">{z.total_alloc_kg.toLocaleString()} kg</span>
                              <span className="text-[10px] text-outline block">
                                {z.alloc_food_kg}F / {z.alloc_water_kg}W
                              </span>
                            </td>
                            <td className="py-2.5 px-3 tabular-nums">
                              <span className={z.deficit_kg > 0 ? 'text-error font-medium' : 'text-emerald-400'}>
                                {z.deficit_kg > 0 ? `-${z.deficit_kg.toLocaleString()} kg` : '0 kg'}
                              </span>
                            </td>
                            <td className="py-2.5 px-3">
                              <div className="w-24 bg-surface-container rounded-full h-2 overflow-hidden border border-outline-variant/30">
                                <div
                                  className={`h-full rounded-full ${
                                    z.fulfillment_pct >= 90
                                      ? 'bg-emerald-400'
                                      : z.fulfillment_pct >= 50
                                      ? 'bg-primary'
                                      : z.fulfillment_pct > 0
                                      ? 'bg-[#f5b84b]'
                                      : 'bg-error'
                                  }`}
                                  style={{ width: `${z.fulfillment_pct}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-outline mt-0.5 block">{z.fulfillment_pct}%</span>
                            </td>
                            <td className="py-2.5 px-3 text-right font-sans">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedZone(z.zone_code);
                                }}
                                className="px-2 py-0.5 rounded text-[11px] bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface"
                              >
                                Details
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Selected Zone Deep Dive Card */}
                {selectedZoneData && (
                  <div className="mt-4 pt-4 border-t border-outline-variant/30 bg-surface-container/30 rounded-lg p-3 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[13px] text-on-surface">
                          {selectedZoneData.zone_code}: {selectedZoneData.zone_name}
                        </span>
                        <span
                          className={`px-2 py-0.2 rounded text-[10px] font-bold ${
                            selectedZoneData.risk_tier === 'CRITICAL'
                              ? 'bg-error/20 text-error'
                              : 'bg-primary/20 text-primary'
                          }`}
                        >
                          {selectedZoneData.risk_tier} PRIORITY
                        </span>
                      </div>
                      <span className="text-[11px] text-secondary font-mono-data">
                        Access: {selectedZoneData.access_status}
                      </span>
                    </div>

                    <p className="text-[12px] text-on-surface-variant italic bg-surface-container-lowest p-2.5 rounded border border-outline-variant/20">
                      "{selectedZoneData.ai_allocation_rationale}"
                    </p>

                    {/* Shelters in this zone */}
                    {selectedZoneData.shelters.length > 0 && (
                      <div className="mt-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-outline block mb-1">
                          Designated Relief Shelters in Zone:
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {selectedZoneData.shelters.map((s) => (
                            <div
                              key={s.shelter_code}
                              className="p-2 rounded bg-surface-container-low border border-outline-variant/30 text-[11px]"
                            >
                              <div className="font-bold text-on-surface">{s.shelter_name}</div>
                              <div className="text-[10px] text-outline">{s.location_desc}</div>
                              <div className="mt-1 flex items-center justify-between text-[10px] font-mono-data text-secondary">
                                <span>Occupancy: {s.occupancy} / {s.capacity}</span>
                                <span>Alloc: {s.allocated_food_kg}kg F / {s.allocated_water_l}L W</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Fleet Route Map & Vehicle Assignments (5 Cols) */}
            <div className="xl:col-span-5 flex flex-col gap-space-md">
              <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 shadow-sm flex flex-col gap-3">
                <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-[20px]">map</span>
                    <h2 className="font-bold text-[14px] text-on-surface">Tactical GIS Fleet Routes</h2>
                  </div>
                  <span className="text-[11px] text-outline font-mono-data">NetworkX & OSRM Detours</span>
                </div>

                {/* Embedded Tactical GIS Map */}
                <div className="rounded-lg overflow-hidden border border-outline-variant/40 shadow-inner">
                  <TacticalGisMap
                    compact={true}
                    height={320}
                    selectedZone={selectedZone.replace('ZONE ', '')}
                    showInspector={false}
                    showLegend={false}
                    activeLayers={{
                      floodRiskZones: true,
                      riverFlow: true,
                      gauges: true,
                      roadAccessibility: true,
                      shelters: true,
                      fleet: true
                    }}
                  />
                </div>

                {/* Vehicle Route Details */}
                <div className="flex flex-col gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-outline">
                    Assigned Fleet Dispatch Units:
                  </span>
                  {plan?.routes.map((r) => (
                    <div
                      key={r.vehicle_code}
                      className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/30 flex flex-col gap-1 text-[11px]"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-primary font-mono-data">{r.vehicle_code}</span>
                          <span className="font-semibold text-on-surface">{r.vehicle_name}</span>
                          <span className="text-[10px] text-outline">({r.vehicle_type})</span>
                        </div>
                        <span className="font-mono-data font-bold text-secondary">{r.total_distance_km} km</span>
                      </div>
                      <div className="text-[10px] text-on-surface-variant flex items-center justify-between">
                        <span>Crew: {r.assigned_crew} ({r.radio_channel})</span>
                        <span>Est: {r.est_duration}</span>
                      </div>
                      <div className="text-[10px] text-outline font-mono-data">{r.route_profile}</div>
                      {r.detour_enforced && (
                        <div className="text-[10px] font-semibold text-[#f5b84b] flex items-center gap-1 bg-[#f5b84b]/10 px-2 py-0.5 rounded border border-[#f5b84b]/20 mt-1">
                          <span className="material-symbols-outlined text-[12px]">alt_route</span>
                          <span>{r.detour_reason}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* 4. Strategy Comparison Matrix Tab */}
      {activeViewTab === 'strategies' && (
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 shadow-sm flex flex-col gap-space-md">
          <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
            <div>
              <h2 className="font-bold text-[16px] text-on-surface">Mathematical Strategy Comparison Matrix</h2>
              <p className="text-[12px] text-on-surface-variant">
                Side-by-side evaluation of 4 distinct Google OR-Tools CP-SAT formulations against the live Kamrup disaster context.
              </p>
            </div>
            <span className="text-[11px] text-primary font-mono-data">Constraint Satisfaction Solver</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-space-sm">
            {strategies.map((st) => (
              <div
                key={st.strategy_id}
                className={`p-space-md rounded-xl border flex flex-col justify-between transition-all ${
                  st.is_recommended
                    ? 'bg-primary-container/10 border-primary/50 shadow-md ring-1 ring-primary/30'
                    : 'bg-surface-container border-outline-variant/30'
                }`}
              >
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        st.is_recommended ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-outline'
                      }`}
                    >
                      {st.is_recommended ? 'RECOMMENDED' : 'ALTERNATIVE'}
                    </span>
                    <span className="text-[10px] font-mono-data text-secondary">{st.solver_runtime_ms} ms</span>
                  </div>

                  <h3 className="font-bold text-[14px] text-on-surface">{st.strategy_name}</h3>
                  <p className="text-[11px] text-on-surface-variant leading-relaxed">{st.priority_assumptions}</p>

                  <div className="mt-3 pt-3 border-t border-outline-variant/20 flex flex-col gap-2 font-mono-data text-[11px]">
                    <div className="flex items-center justify-between">
                      <span className="text-outline">Allocated:</span>
                      <span className="font-bold text-primary">{st.total_allocated_kg.toLocaleString()} kg</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-outline">Shortfall:</span>
                      <span className="font-bold text-error">{st.total_unmet_kg.toLocaleString()} kg</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-outline">Critical Need Covered:</span>
                      <span className="font-bold text-emerald-400">{st.critical_zone_coverage_pct}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-outline">Transit Distance:</span>
                      <span className="text-on-surface">{st.est_transit_distance_km} km</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-outline">Fuel Burn:</span>
                      <span className="text-on-surface">~{st.est_fuel_burn_liters} L</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-outline-variant/20 flex flex-col gap-2">
                  <div className="text-[11px] text-on-surface-variant italic bg-surface-container-lowest p-2 rounded border border-outline-variant/10">
                    <span className="font-bold text-outline uppercase block text-[9px]">Trade-off Analysis:</span>
                    {st.key_tradeoff}
                  </div>
                  <button
                    onClick={() => {
                      setActiveStrategy(st.strategy_id);
                      setActiveViewTab('plan');
                    }}
                    className={`w-full py-1.5 rounded-lg text-[11px] font-bold transition-all ${
                      activeStrategy === st.strategy_id
                        ? 'bg-primary text-on-primary'
                        : 'bg-surface-container-high hover:bg-surface-container-highest text-on-surface'
                    }`}
                  >
                    {activeStrategy === st.strategy_id ? 'Active Selected Strategy' : 'Select Strategy'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Diagnostics & Operational Constraints Tab */}
      {activeViewTab === 'diagnostics' && (
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 shadow-sm flex flex-col gap-space-md">
          <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
            <div>
              <h2 className="font-bold text-[16px] text-on-surface">Operational Diagnostics & Active Constraints</h2>
              <p className="text-[12px] text-on-surface-variant">
                Mathematical bottleneck identification, sensor telemetry freshness, and physical boundary enforcement.
              </p>
            </div>
            <span className="text-[11px] text-secondary font-mono-data">ISO-19115 Quality Ledger</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
            {/* Binding Constraints Card */}
            <div className="p-space-md rounded-xl bg-surface-container border border-outline-variant/30 flex flex-col gap-2">
              <div className="flex items-center gap-2 text-primary font-bold text-[13px]">
                <span className="material-symbols-outlined text-[18px]">lock</span>
                <span>Active Binding Constraints (Solver Limits)</span>
              </div>
              <div className="flex flex-col gap-2 mt-2">
                {plan?.diagnostics.binding_constraints.map((b, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-surface-container-low border border-outline-variant/20 flex flex-col gap-1 text-[11px]"
                  >
                    <div className="flex items-center justify-between font-mono-data font-bold">
                      <span className="text-secondary">{b.constraint}</span>
                      <span className="text-[10px] text-outline uppercase">{b.type}</span>
                    </div>
                    <p className="text-on-surface-variant text-[11px]">{b.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Inundated Routes & Chokepoints */}
            <div className="p-space-md rounded-xl bg-surface-container border border-outline-variant/30 flex flex-col gap-2">
              <div className="flex items-center gap-2 text-[#f5b84b] font-bold text-[13px]">
                <span className="material-symbols-outlined text-[18px]">warning</span>
                <span>Unavailable Corridors & Enforced Detours</span>
              </div>
              <div className="flex flex-col gap-2 mt-2">
                {plan?.diagnostics.unavailable_routes.map((u, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-surface-container-low border border-[#f5b84b]/30 flex flex-col gap-1 text-[11px]"
                  >
                    <div className="font-bold text-[#f5b84b] flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">alt_route</span>
                      <span>Chokepoint Active</span>
                    </div>
                    <p className="text-on-surface-variant text-[11px]">{u}</p>
                  </div>
                ))}

                <div className="mt-2 pt-2 border-t border-outline-variant/20">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-outline block mb-1">
                    Telemetry Ingest Timestamps:
                  </span>
                  <div className="flex flex-col gap-1 font-mono-data text-[10px] text-on-surface-variant">
                    {Object.entries(plan?.diagnostics.telemetry_freshness || {}).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between">
                        <span className="text-outline uppercase">{k.replace(/_/g, ' ')}:</span>
                        <span className="text-on-surface">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. What-If Simulation Sandbox Modal */}
      {whatIfModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-outline-variant/40 rounded-2xl max-w-2xl w-full p-space-lg shadow-2xl flex flex-col gap-space-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-[24px]">science</span>
                <div>
                  <h3 className="font-bold text-[16px] text-on-surface">Interactive What-If Logistics Sandbox</h3>
                  <span className="text-[11px] text-outline font-mono-data">
                    Isolated In-Memory Re-Optimization • Zero DB Mutations
                  </span>
                </div>
              </div>
              <button
                onClick={() => setWhatIfModalOpen(false)}
                className="text-outline hover:text-on-surface p-1 rounded-md"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md text-[12px]">
              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Scenario Title</label>
                <input
                  type="text"
                  value={whatIfTitle}
                  onChange={(e) => setWhatIfTitle(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px]"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Demand Multiplier</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="3.0"
                  value={demandMultiplier}
                  onChange={(e) => setDemandMultiplier(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px]"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">
                  Custom Depot Food Buffer (kg)
                </label>
                <input
                  type="number"
                  value={customFoodStock}
                  onChange={(e) => setCustomFoodStock(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px]"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">
                  Custom Depot Water Buffer (L)
                </label>
                <input
                  type="number"
                  value={customWaterStock}
                  onChange={(e) => setCustomWaterStock(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px]"
                />
              </div>
            </div>

            {/* Checkboxes for Fleet and Severed Zones */}
            <div className="flex flex-col gap-2 pt-2 border-t border-outline-variant/20 text-[11px]">
              <span className="font-bold text-outline uppercase">Simulate Vehicle Out-of-Service:</span>
              <div className="flex items-center gap-4 flex-wrap">
                {['VH-01', 'VH-02', 'VH-03'].map((vh) => (
                  <label key={vh} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={disabledVehicles.includes(vh)}
                      onChange={(e) => {
                        if (e.target.checked) setDisabledVehicles([...disabledVehicles, vh]);
                        else setDisabledVehicles(disabledVehicles.filter((v) => v !== vh));
                      }}
                      className="rounded bg-surface-container"
                    />
                    <span>Disable {vh}</span>
                  </label>
                ))}
              </div>

              <span className="font-bold text-outline uppercase mt-2">Simulate Road Severance (Bridge Collapse):</span>
              <div className="flex items-center gap-4 flex-wrap">
                {['ZONE 01', 'ZONE 02'].map((z) => (
                  <label key={z} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={severedZones.includes(z)}
                      onChange={(e) => {
                        if (e.target.checked) setSeveredZones([...severedZones, z]);
                        else setSeveredZones(severedZones.filter((v) => v !== z));
                      }}
                      className="rounded bg-surface-container"
                    />
                    <span>Sever {z} Access</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Simulation Results Display */}
            {whatIfResult && (
              <div className="p-3 rounded-xl bg-surface-container border border-primary/30 flex flex-col gap-2 text-[11px] font-mono-data">
                <div className="flex items-center justify-between font-bold text-primary">
                  <span>Simulation Results vs Baseline</span>
                  <span>{whatIfResult.feasibility_status}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center pt-1">
                  <div className="p-2 rounded bg-surface-container-low">
                    <div className="text-[10px] text-outline">Allocated Delta</div>
                    <div className="font-bold text-[13px] text-primary">
                      {whatIfResult.allocated_delta_kg > 0 ? `+${whatIfResult.allocated_delta_kg}` : whatIfResult.allocated_delta_kg} kg
                    </div>
                  </div>
                  <div className="p-2 rounded bg-surface-container-low">
                    <div className="text-[10px] text-outline">Unmet Delta</div>
                    <div className="font-bold text-[13px] text-error">
                      {whatIfResult.unmet_delta_kg > 0 ? `+${whatIfResult.unmet_delta_kg}` : whatIfResult.unmet_delta_kg} kg
                    </div>
                  </div>
                  <div className="p-2 rounded bg-surface-container-low">
                    <div className="text-[10px] text-outline">Distance Delta</div>
                    <div className="font-bold text-[13px] text-tertiary">
                      {whatIfResult.distance_delta_km > 0 ? `+${whatIfResult.distance_delta_km}` : whatIfResult.distance_delta_km} km
                    </div>
                  </div>
                </div>
                <p className="text-[11px] font-sans text-on-surface-variant italic mt-1 bg-surface-container-lowest p-2 rounded">
                  {whatIfResult.ai_impact_analysis}
                </p>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/30">
              <button
                onClick={() => setWhatIfModalOpen(false)}
                className="px-3 py-1.5 rounded-lg text-[12px] text-on-surface hover:bg-surface-container"
              >
                Close
              </button>
              <button
                onClick={handleExecuteWhatIf}
                disabled={whatIfLoading}
                className="px-4 py-1.5 rounded-lg bg-tertiary text-on-tertiary font-bold text-[12px] hover:brightness-110 shadow-sm flex items-center gap-1.5"
              >
                <span className={`material-symbols-outlined text-[16px] ${whatIfLoading ? 'animate-spin' : ''}`}>
                  {whatIfLoading ? 'sync' : 'play_arrow'}
                </span>
                <span>{whatIfLoading ? 'Simulating...' : 'Run Simulation'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Human Review & Authorization Modal (Form 8B) */}
      {reviewModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-outline-variant/40 rounded-2xl max-w-lg w-full p-space-lg shadow-2xl flex flex-col gap-space-md">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[24px]">verified_user</span>
                <div>
                  <h3 className="font-bold text-[16px] text-on-surface">ASDMA Form 8B Operational Sign-Off</h3>
                  <span className="text-[11px] text-outline font-mono-data">Statutory Human-in-the-Loop Audit</span>
                </div>
              </div>
              <button
                onClick={() => setReviewModalOpen(false)}
                className="text-outline hover:text-on-surface p-1 rounded-md"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="flex flex-col gap-3 text-[12px]">
              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Authorizing Officer</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px]"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Form 8B Reference ID</label>
                <input
                  type="text"
                  value={form8bRef}
                  onChange={(e) => setForm8bRef(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px] font-mono-data"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Decision</label>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={reviewAction === 'APPROVE'}
                      onChange={() => setReviewAction('APPROVE')}
                    />
                    <span className="font-bold text-emerald-400">APPROVE FOR FLEET STAGING</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={reviewAction === 'REJECT'}
                      onChange={() => setReviewAction('REJECT')}
                    />
                    <span className="font-bold text-error">REJECT (REVISE PLAN)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-outline uppercase block mb-1">Operational Justification</label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-container border border-outline-variant/40 text-on-surface text-[12px] leading-relaxed"
                />
              </div>

              <div className="p-2.5 rounded bg-surface-container-lowest border border-outline-variant/30 text-[10px] text-on-surface-variant">
                <span className="font-bold text-outline block mb-0.5">STATUTORY SAFETY GUARANTEE:</span>
                This action authorizes the physical staging manifest at {selectedLocation.primaryDepot} and commits an immutable record into
                SQLite audit logs. It does NOT autonomously trigger vehicle movement or inventory deduction.
              </div>

              {reviewFeedback && (
                <div
                  className={`p-2 rounded text-[11px] font-bold text-center ${
                    reviewFeedback.includes('successfully') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-error/20 text-error'
                  }`}
                >
                  {reviewFeedback}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/30">
              <button
                onClick={() => setReviewModalOpen(false)}
                className="px-3 py-1.5 rounded-lg text-[12px] text-on-surface hover:bg-surface-container"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitReview}
                disabled={reviewLoading}
                className={`px-4 py-1.5 rounded-lg font-bold text-[12px] shadow-sm flex items-center gap-1.5 ${
                  reviewAction === 'APPROVE'
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    : 'bg-error hover:bg-error/90 text-white'
                }`}
              >
                <span className={`material-symbols-outlined text-[16px] ${reviewLoading ? 'animate-spin' : ''}`}>
                  {reviewLoading ? 'sync' : 'check'}
                </span>
                <span>{reviewAction === 'APPROVE' ? 'Authorize Plan (Form 8B)' : 'Confirm Rejection'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

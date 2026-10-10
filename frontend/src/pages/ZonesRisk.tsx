import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  api,
  getFloodRiskAnalysis,
  recalculateFloodRisk,
  getRiskDatasetAudit,
  getRiskModelMetadata,
  FloodRiskAnalysisResponse,
  ZoneRiskAssessment,
  DatasetAuditResponse,
  MLModelMetadataResponse,
  RiskEngineWeights,
} from '../services/api';
import { useLocationContext } from '../context/LocationContext';

export const ZonesRisk: React.FC = () => {
  const { selectedLocation, isKamrupMetro } = useLocationContext();
  const [selectedZone, setSelectedZone] = useState('ZONE 02');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [riskAnalysis, setRiskAnalysis] = useState<FloodRiskAnalysisResponse | null>(null);
  const [forceBaseline, setForceBaseline] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [auditData, setAuditData] = useState<DatasetAuditResponse | null>(null);
  const [showModelModal, setShowModelModal] = useState(false);
  const [modelMetadata, setModelMetadata] = useState<MLModelMetadataResponse | null>(null);
  const [showWeightsConfig, setShowWeightsConfig] = useState(false);

  // Configurable weights state
  const [weights, setWeights] = useState<RiskEngineWeights>({
    weight_rainfall: 0.30,
    weight_hydrology: 0.30,
    weight_terrain: 0.25,
    weight_drainage: 0.15,
  });

  const fetchRiskData = async (baselineOverride: boolean) => {
    setLoading(true);
    try {
      const res = await getFloodRiskAnalysis(baselineOverride);
      setRiskAnalysis(res.data);
    } catch (err) {
      console.warn('Could not load live flood risk analysis', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData(forceBaseline);
  }, [forceBaseline, selectedLocation.id]);

  useEffect(() => {
    if (riskAnalysis?.zone_assessments && riskAnalysis.zone_assessments.length > 0) {
      setSelectedZone(riskAnalysis.zone_assessments[0].zone_code);
    }
  }, [riskAnalysis]);

  const handleRecalculateWithWeights = async () => {
    setLoading(true);
    try {
      const res = await recalculateFloodRisk({
        weights,
        force_baseline: forceBaseline,
        operator_name: 'Insp. S. Sharma (EOC Planner)',
      });
      setRiskAnalysis(res.data);
    } catch (err) {
      console.error('Failed to recalculate risk', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAuditModal = async () => {
    try {
      const res = await getRiskDatasetAudit();
      setAuditData(res.data);
      setShowAuditModal(true);
    } catch (err) {
      console.error('Failed to load dataset audit', err);
    }
  };

  const handleOpenModelModal = async () => {
    try {
      const res = await getRiskModelMetadata();
      setModelMetadata(res.data);
      setShowModelModal(true);
    } catch (err) {
      console.error('Failed to load model metadata', err);
    }
  };

  const handleExportDossier = () => {
    if (!riskAnalysis) return;
    const blob = new Blob([JSON.stringify(riskAnalysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ASDMA_Evidence_Based_Flood_Risk_Dossier_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return 'text-error bg-error/15 border-error/40';
      case 'HIGH':
        return 'text-tertiary bg-tertiary/15 border-tertiary/40';
      case 'MODERATE':
        return 'text-[#F5B84B] bg-[#F5B84B]/15 border-[#F5B84B]/40';
      default:
        return 'text-primary bg-primary/15 border-primary/40';
    }
  };

  const filteredZones = (riskAnalysis?.zone_assessments || []).filter(
    (z) =>
      z.zone_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      z.zone_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedAssessment = (riskAnalysis?.zone_assessments || []).find(
    (z) => z.zone_code === selectedZone
  ) || riskAnalysis?.zone_assessments[0];

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-[1600px] mx-auto animate-fadeIn">
      {/* 1. Header & Engine Mode Control */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
        <div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[28px]">water_damage</span>
            <h1 className="font-headline-md text-xl lg:text-2xl font-bold text-on-surface">
              Flood Risk Analysis & Classification
            </h1>
            <span className="px-2.5 py-0.5 rounded text-[11px] font-mono-data font-bold bg-surface-container-high border border-outline-variant text-primary">
              {riskAnalysis?.system_mode || 'OPERATIONAL_LIVE'}
            </span>
          </div>
          <p className="text-[13px] text-on-surface-variant mt-1">
            {selectedLocation.displayName} multi-source relative risk estimation • Non-hydrodynamic triage index • Form 8B Human-in-the-Loop
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Method Indicator Pill */}
          <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-xl border border-outline-variant/40 text-[12px] font-mono-data">
            <span className="text-outline">Engine:</span>
            {riskAnalysis?.active_method === 'ML_RANDOM_FOREST' ? (
              <span className="text-primary font-bold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                Random Forest ML (Calibrated)
              </span>
            ) : (
              <span className="text-[#F5B84B] font-bold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-[#F5B84B]"></span>
                Transparent Baseline (MCDA)
              </span>
            )}
          </div>

          {/* Toggle Baseline Override */}
          <button
            type="button"
            onClick={() => setForceBaseline(!forceBaseline)}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-medium border transition-colors cursor-pointer flex items-center gap-1.5 ${
              forceBaseline
                ? 'bg-tertiary/20 border-tertiary/40 text-tertiary'
                : 'bg-surface-container hover:bg-surface-container-high border-outline-variant text-on-surface-variant hover:text-on-surface'
            }`}
            title="Toggle between ML model inference and transparent rule-based MCDA scoring"
          >
            <span className="material-symbols-outlined text-[16px]">tune</span>
            <span>{forceBaseline ? 'Baseline Active' : 'Force Baseline'}</span>
          </button>

          {/* Dataset Audit Button */}
          <button
            type="button"
            onClick={handleOpenAuditModal}
            className="px-3 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant text-[12px] font-medium text-on-surface flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Audit input datasets, sensors, gaps, and quality"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">fact_check</span>
            <span>Dataset Audit</span>
          </button>

          {/* ML Model Metadata Button */}
          <button
            type="button"
            onClick={handleOpenModelModal}
            className="px-3 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant text-[12px] font-medium text-on-surface flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Inspect Random Forest architecture, evaluation metrics, and data roadmap"
          >
            <span className="material-symbols-outlined text-[16px] text-secondary">model_training</span>
            <span>ML Architecture</span>
          </button>

          {/* Export Dossier */}
          <button
            type="button"
            onClick={handleExportDossier}
            className="px-3 py-1.5 rounded-xl bg-primary hover:bg-primary/90 text-on-primary text-[12px] font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Export Dossier</span>
          </button>
        </div>
      </div>

      {/* District Staging Notice for non-Kamrup Metro districts */}
      {!isKamrupMetro && (
        <div className="bg-secondary/10 border border-secondary/40 rounded-xl p-3.5 flex items-start gap-3 text-secondary text-[12px]">
          <span className="material-symbols-outlined text-[20px] shrink-0 mt-0.5">info</span>
          <div>
            <span className="font-bold block text-[13px]">
              {selectedLocation.displayName} — Multi-Sector Operational Risk Assessment
            </span>
            <span className="text-on-surface-variant">
              Relative flood risk scores below reflect {selectedLocation.displayName} operational revenue circles. Hydrology stations on {selectedLocation.primaryRiver} provide active CWC stage correlation.
            </span>
          </div>
        </div>
      )}

      {/* 2. Citywide Summary Ribbon */}
      {riskAnalysis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-[11px] font-mono-data uppercase tracking-wider text-outline">
              Critical / High Sectors
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono-data text-error">
                {riskAnalysis.citywide_summary.critical_risk_sectors + riskAnalysis.citywide_summary.high_risk_sectors}
              </span>
              <span className="text-[12px] text-on-surface-variant font-mono-data">
                / {riskAnalysis.citywide_summary.total_monitored_sectors} Monitored
              </span>
            </div>
            <span className="text-[10px] text-outline mt-1">Requires immediate emergency staging</span>
          </div>

          <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-[11px] font-mono-data uppercase tracking-wider text-outline">
              Citywide Peak Vulnerability
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono-data text-tertiary">
                {riskAnalysis.citywide_summary.citywide_max_risk_score.toFixed(1)}
              </span>
              <span className="text-[11px] text-outline font-mono-data">/ 10.0 Index</span>
            </div>
            <span className="text-[10px] text-on-surface-variant truncate mt-1">
              Sector: {riskAnalysis.citywide_summary.highest_priority_sector.code} ({riskAnalysis.citywide_summary.highest_priority_sector.name})
            </span>
          </div>

          <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-[11px] font-mono-data uppercase tracking-wider text-outline">
              Controlling Hydrology Stage
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono-data text-primary">
                {riskAnalysis.citywide_summary.hydrometeorological_drivers.current_river_stage_m.toFixed(2)}m
              </span>
              <span className={`text-[11px] font-mono-data font-bold ${
                riskAnalysis.citywide_summary.hydrometeorological_drivers.stage_margin_m >= 0 ? 'text-error' : 'text-primary'
              }`}>
                {riskAnalysis.citywide_summary.hydrometeorological_drivers.stage_margin_m >= 0
                  ? `+${riskAnalysis.citywide_summary.hydrometeorological_drivers.stage_margin_m.toFixed(2)}m (Danger)`
                  : `${riskAnalysis.citywide_summary.hydrometeorological_drivers.stage_margin_m.toFixed(2)}m`}
              </span>
            </div>
            <span className="text-[10px] text-outline truncate mt-1">
              {riskAnalysis.citywide_summary.hydrometeorological_drivers.controlling_gauge} • {riskAnalysis.citywide_summary.hydrometeorological_drivers.river_trend}
            </span>
          </div>

          <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-[11px] font-mono-data uppercase tracking-wider text-outline">
              Precipitation Telemetry
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono-data text-on-surface">
                {riskAnalysis.citywide_summary.hydrometeorological_drivers.precipitation_rate_mm_h.toFixed(1)}
              </span>
              <span className="text-[12px] text-outline font-mono-data">mm/h rate</span>
            </div>
            <span className="text-[10px] text-outline truncate mt-1">
              Open-Meteo ECMWF • {riskAnalysis.citywide_summary.hydrometeorological_drivers.weather_condition}
            </span>
          </div>
        </div>
      )}

      {/* Statutory Disclaimer Alert */}
      <div className="bg-surface-container-low border border-outline-variant/30 px-4 py-3 rounded-xl flex items-center justify-between text-[12px] text-on-surface-variant">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[#F5B84B] text-[20px]">verified_user</span>
          <span>
            <strong>ASDMA Statutory Advisory:</strong> Relative flood risk classification reflects multi-criteria vulnerability.
            No automated alerts or vehicle dispatches occur autonomously. Official Form 8B physical sign-off required.
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowWeightsConfig(!showWeightsConfig)}
          className="text-primary hover:text-primary-fixed text-[11px] font-semibold flex items-center gap-1 cursor-pointer"
        >
          <span>{showWeightsConfig ? 'Hide Weight Tuning' : 'Tune Weights'}</span>
          <span className="material-symbols-outlined text-[14px]">
            {showWeightsConfig ? 'expand_less' : 'expand_more'}
          </span>
        </button>
      </div>

      {/* Configurable Planner Weights Drawer */}
      {showWeightsConfig && (
        <div className="bg-surface-container border border-outline-variant/40 rounded-xl p-4 space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-[14px] text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">tune</span>
              Configurable Multi-Criteria Decision Weights (MCDA Planner Simulation)
            </h3>
            <span className="text-[11px] font-mono-data text-outline">
              Total Weight: {((weights.weight_rainfall + weights.weight_hydrology + weights.weight_terrain + weights.weight_drainage) * 100).toFixed(0)}%
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="flex justify-between text-[11px] text-on-surface mb-1">
                <span>Rainfall & Forecast Hazard:</span>
                <span className="font-mono-data font-bold">{(weights.weight_rainfall * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={weights.weight_rainfall}
                onChange={(e) => setWeights({ ...weights, weight_rainfall: parseFloat(e.target.value) })}
                className="w-full accent-primary cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-on-surface mb-1">
                <span>River Stage & Surcharge:</span>
                <span className="font-mono-data font-bold">{(weights.weight_hydrology * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={weights.weight_hydrology}
                onChange={(e) => setWeights({ ...weights, weight_hydrology: parseFloat(e.target.value) })}
                className="w-full accent-primary cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-on-surface mb-1">
                <span>Terrain & Population Exposure:</span>
                <span className="font-mono-data font-bold">{(weights.weight_terrain * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.50"
                step="0.05"
                value={weights.weight_terrain}
                onChange={(e) => setWeights({ ...weights, weight_terrain: parseFloat(e.target.value) })}
                className="w-full accent-primary cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-on-surface mb-1">
                <span>Drainage & Chokepoint Impedance:</span>
                <span className="font-mono-data font-bold">{(weights.weight_drainage * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.40"
                step="0.05"
                value={weights.weight_drainage}
                onChange={(e) => setWeights({ ...weights, weight_drainage: parseFloat(e.target.value) })}
                className="w-full accent-primary cursor-pointer"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-outline-variant/20">
            <button
              type="button"
              onClick={() => {
                setWeights({
                  weight_rainfall: 0.30,
                  weight_hydrology: 0.30,
                  weight_terrain: 0.25,
                  weight_drainage: 0.15,
                });
              }}
              className="px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container text-on-surface-variant text-[11px] cursor-pointer"
            >
              Reset to Standard Defaults
            </button>
            <button
              type="button"
              onClick={handleRecalculateWithWeights}
              disabled={loading}
              className="px-4 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-on-primary text-[11px] font-bold cursor-pointer transition-all shadow-sm"
            >
              Apply Weights & Recalculate
            </button>
          </div>
        </div>
      )}

      {/* 3. Main Workspace: Zone Cards Grid & Selected Zone Detail Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Sector Cards List */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-1">
            <h3 className="font-bold text-[14px] text-on-surface">
              Operational Zones ({filteredZones.length})
            </h3>
            <input
              type="text"
              placeholder="Filter zone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-surface-container border border-outline-variant/40 rounded-lg px-2.5 py-1 text-[11px] text-on-surface placeholder:text-outline focus:outline-none focus:border-primary w-36"
            />
          </div>

          <div className="space-y-2.5">
            {filteredZones.map((z) => {
              const isSelected = z.zone_code === selectedZone;
              return (
                <div
                  key={z.zone_code}
                  onClick={() => setSelectedZone(z.zone_code)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-surface-container-high border-primary shadow-md'
                      : 'bg-surface-container-low hover:bg-surface-container border-outline-variant/30'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono-data text-[12px] font-bold text-on-surface">
                          {z.zone_code}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono-data font-bold border ${getTierColor(z.risk_tier)}`}>
                          {z.risk_tier}
                        </span>
                      </div>
                      <h4 className="font-semibold text-[13px] text-on-surface mt-1">{z.zone_name}</h4>
                    </div>

                    <div className="text-right">
                      <div className="text-2xl font-bold font-mono-data text-on-surface">
                        {z.risk_score.toFixed(1)}
                      </div>
                      <span className="text-[10px] text-outline font-mono-data">Score / 10.0</span>
                    </div>
                  </div>

                  {/* Primary driver & confidence */}
                  <div className="mt-3 pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[11px]">
                    <span className="text-on-surface-variant truncate max-w-[200px]" title={z.primary_driver}>
                      {z.primary_driver}
                    </span>
                    {z.is_machine_learning && z.prediction_confidence !== null && (
                      <span className="text-primary font-mono-data text-[10px] font-semibold bg-primary/10 px-1.5 py-0.5 rounded">
                        {(z.prediction_confidence! * 100).toFixed(0)}% Conf
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Deep-Dive Risk Factor Dossier */}
        <div className="lg:col-span-7">
          {selectedAssessment ? (
            <div className="bg-surface-container-low border border-outline-variant/30 rounded-2xl p-5 space-y-5">
              
              {/* Dossier Header */}
              <div className="flex items-start justify-between pb-3 border-b border-outline-variant/20">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-headline-sm text-lg font-bold text-on-surface">
                      {selectedAssessment.zone_code}: {selectedAssessment.zone_name}
                    </h2>
                    <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono-data font-bold border ${getTierColor(selectedAssessment.risk_tier)}`}>
                      {selectedAssessment.risk_tier} RISK
                    </span>
                  </div>
                  <p className="text-[12px] text-on-surface-variant mt-0.5">
                    Affected Population: {selectedAssessment.affected_population.toLocaleString()} • Inundation Footprint: {selectedAssessment.inundation_area_ha} ha
                  </p>
                </div>

                <div className="text-right">
                  <div className="text-3xl font-bold font-mono-data text-primary">
                    {selectedAssessment.risk_score.toFixed(2)}
                  </div>
                  <span className="text-[11px] text-outline font-mono-data">Relative Severity</span>
                </div>
              </div>

              {/* Primary Risk Driver Callout */}
              <div className="bg-surface-container border border-outline-variant/30 p-3.5 rounded-xl">
                <div className="text-[10px] font-mono-data font-bold text-outline uppercase tracking-wider mb-1">
                  Primary Empirical Risk Driver
                </div>
                <div className="text-[13px] font-semibold text-on-surface">
                  {selectedAssessment.primary_driver}
                </div>
              </div>

              {/* Contributing Factors Breakdown Table */}
              <div>
                <h4 className="font-bold text-[13px] text-on-surface mb-2.5 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[18px]">analytics</span>
                  Contributing Risk Sub-Indices & Weights
                </h4>

                <div className="space-y-2">
                  {selectedAssessment.contributing_factors.map((f, i) => (
                    <div
                      key={i}
                      className="bg-surface-container/70 border border-outline-variant/20 rounded-xl p-3 text-[12px]"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-on-surface">{f.factor_name}</span>
                        <div className="flex items-center gap-2 font-mono-data">
                          <span className="text-outline">{(f.weight_applied * 100).toFixed(0)}% Wt</span>
                          <span className="font-bold text-primary">+{f.weighted_contribution.toFixed(2)} pts</span>
                        </div>
                      </div>
                      <div className="text-on-surface-variant font-mono-data text-[11px]">{f.raw_value}</div>
                      <div className="text-[10px] text-outline mt-1">Source: {f.provenance}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Calibrated Class Probabilities (if ML mode active) */}
              {selectedAssessment.class_probabilities && (
                <div className="bg-surface-container-high/60 border border-outline-variant/30 rounded-xl p-3.5 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono-data text-outline">
                    <span>STATISTICALLY CALIBRATED CLASS PROBABILITIES:</span>
                    <span>Confidence: {(selectedAssessment.prediction_confidence! * 100).toFixed(1)}%</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-center text-[11px] font-mono-data">
                    {Object.entries(selectedAssessment.class_probabilities).map(([cls, prob]) => (
                      <div key={cls} className="bg-surface-container p-2 rounded-lg border border-outline-variant/20">
                        <div className="text-outline text-[10px]">{cls}</div>
                        <div className="font-bold text-on-surface mt-0.5">{(prob * 100).toFixed(1)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Data Freshness & Model Limitations */}
              <div className="pt-2 border-t border-outline-variant/20 space-y-1.5 text-[11px] text-outline">
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[15px] text-secondary">update</span>
                  <span>{selectedAssessment.data_freshness_label}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[15px] text-[#F5B84B]">info</span>
                  <span>{selectedAssessment.limitations}</span>
                </div>
              </div>

              {/* Quick Navigation to Relief Allocation */}
              <div className="pt-2 flex items-center justify-end gap-3">
                <Link
                  to="/allocation"
                  className="px-4 py-2 rounded-xl bg-primary hover:bg-primary/90 text-on-primary text-[12px] font-bold flex items-center gap-1.5 shadow-sm transition-all"
                >
                  <span>Stage Relief Optimization for {selectedAssessment.zone_code}</span>
                  <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                </Link>
              </div>

            </div>
          ) : (
            <div className="bg-surface-container-low border border-outline-variant/30 rounded-2xl p-12 text-center text-outline">
              Select a sector to view its empirical risk breakdown.
            </div>
          )}
        </div>

      </div>

      {/* 4. Historical Flood Event Benchmarks */}
      {riskAnalysis?.historical_comparisons && (
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[22px]">history_toggle_off</span>
            <h3 className="font-headline-sm text-[16px] font-bold text-on-surface">
              Historical Disaster Event Comparisons & Benchmarks
            </h3>
          </div>
          <p className="text-[12px] text-on-surface-variant">
            Authentic archived Guwahati flood baselines (ASDMA Daily Bulletins & IMD Borjhar) compared against current conditions.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {riskAnalysis.historical_comparisons.map((h) => (
              <div
                key={h.event_id}
                className="bg-surface-container border border-outline-variant/30 rounded-xl p-4 text-[12px] space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-on-surface text-[13px]">{h.event_title}</span>
                  <span className="font-mono-data text-[10px] text-outline px-2 py-0.5 rounded bg-surface-container-high">
                    {h.event_period}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 font-mono-data text-[11px] bg-surface-container-low p-2 rounded-lg border border-outline-variant/20">
                  <div>
                    <span className="text-outline text-[10px] block">Peak 24h Rain</span>
                    <strong>{h.rainfall_24h_mm} mm</strong>
                  </div>
                  <div>
                    <span className="text-outline text-[10px] block">Pandu Stage</span>
                    <strong>{h.peak_pandu_stage_m} m</strong>
                  </div>
                  <div>
                    <span className="text-outline text-[10px] block">Displaced Pop</span>
                    <strong>{h.displaced_population.toLocaleString()}</strong>
                  </div>
                </div>
                <p className="text-on-surface-variant text-[11px]">{h.comparison_notes}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Dataset Audit Modal */}
      {showAuditModal && auditData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 animate-fadeIn">
          <div className="w-full max-w-4xl bg-surface-container border border-outline-variant/50 rounded-2xl p-6 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">fact_check</span>
                <h3 className="font-headline-sm text-[16px] font-bold text-on-surface">
                  Operational Datasets & Sensor Gaps Audit
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAuditModal(false)}
                className="p-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="my-3 flex items-center justify-between text-[11px] font-mono-data bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
              <div>Total Evaluated Feeds: <strong className="text-on-surface">{auditData.total_datasets}</strong></div>
              <div>Standard: <strong className="text-primary">{auditData.governance_compliance}</strong></div>
              <div>Audited: <span className="text-outline">{auditData.audited_at}</span></div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {auditData.datasets.map((ds, idx) => (
                <div key={idx} className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3 text-[12px] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-on-surface text-[13px]">{ds.dataset_name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono-data font-bold bg-primary/10 text-primary border border-primary/30">
                      {ds.quality_trust_tier}
                    </span>
                  </div>
                  <div className="text-[11px] text-on-surface-variant">Agency: {ds.source_agency} • Coverage: {ds.spatial_coverage}</div>
                  <div className="text-[11px] text-outline">Frequency: {ds.update_frequency} • Timestamps: {ds.observation_timestamps}</div>
                  <div className="text-[11px] bg-surface-container-lowest p-2 rounded border border-outline-variant/20 text-[#F5B84B]">
                    <strong>Known Sensor Gaps & Limitations:</strong> {ds.known_sensor_gaps}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-outline-variant/30 flex justify-end">
              <button
                type="button"
                onClick={() => setShowAuditModal(false)}
                className="px-4 py-2 rounded-xl bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-[12px] font-semibold transition-colors cursor-pointer"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. ML Model Metadata & Hydrodynamic Requirements Modal */}
      {showModelModal && modelMetadata && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 animate-fadeIn">
          <div className="w-full max-w-4xl bg-surface-container border border-outline-variant/50 rounded-2xl p-6 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[22px]">model_training</span>
                <h3 className="font-headline-sm text-[16px] font-bold text-on-surface">
                  Machine Learning Architecture & Evaluation Metrics
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowModelModal(false)}
                className="p-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-1 my-3">
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono-data text-[12px]">
                <div className="bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
                  <span className="text-outline text-[10px] block">Accuracy</span>
                  <strong className="text-xl text-primary font-bold">
                    {(modelMetadata.evaluation_metrics.accuracy * 100).toFixed(1)}%
                  </strong>
                </div>
                <div className="bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
                  <span className="text-outline text-[10px] block">Macro F1 Score</span>
                  <strong className="text-xl text-secondary font-bold">
                    {modelMetadata.evaluation_metrics.macro_f1.toFixed(3)}
                  </strong>
                </div>
                <div className="bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
                  <span className="text-outline text-[10px] block">Brier Score Loss</span>
                  <strong className="text-xl text-tertiary font-bold">
                    {modelMetadata.evaluation_metrics.brier_score_loss.toFixed(4)}
                  </strong>
                </div>
                <div className="bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
                  <span className="text-outline text-[10px] block">Training Samples</span>
                  <strong className="text-xl text-on-surface font-bold">
                    {modelMetadata.training_sample_count}
                  </strong>
                </div>
              </div>

              {/* Architecture Details */}
              <div className="bg-surface-container-low p-3.5 rounded-xl border border-outline-variant/20 text-[12px] space-y-1">
                <div>Model Version: <strong className="font-mono-data text-primary">{modelMetadata.model_version}</strong></div>
                <div>Algorithm: <strong>{modelMetadata.algorithm}</strong></div>
                <div>Train/Test Split: <strong>{modelMetadata.train_test_split_ratio} (Stratified)</strong></div>
                <div>Target Variable: <span className="font-mono-data text-outline">{modelMetadata.target_variable}</span></div>
              </div>

              {/* Feature Importances */}
              <div>
                <h4 className="font-bold text-[13px] text-on-surface mb-2">Feature Importances (Gini Impurity)</h4>
                <div className="space-y-1.5 font-mono-data text-[11px]">
                  {Object.entries(modelMetadata.feature_importances).map(([feat, imp]) => (
                    <div key={feat} className="flex items-center gap-3">
                      <span className="w-48 text-on-surface-variant truncate">{feat}</span>
                      <div className="flex-1 bg-surface-container h-2 rounded-full overflow-hidden">
                        <div className="bg-primary h-full rounded-full" style={{ width: `${imp * 100 * 3}%` }}></div>
                      </div>
                      <span className="w-12 text-right text-outline">{(imp * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data Roadmap for 2D Hydrodynamic Modeling */}
              <div className="bg-surface-container-low p-3.5 rounded-xl border border-outline-variant/20 space-y-2">
                <h4 className="font-bold text-[13px] text-on-surface text-tertiary flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[18px]">architecture</span>
                  Roadmap Requirements for Future 2D Hydrodynamic Modeling
                </h4>
                <ul className="list-disc list-inside space-y-1 text-[11px] text-on-surface-variant">
                  {modelMetadata.required_data_for_future_hydrodynamic_model.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="pt-3 border-t border-outline-variant/30 flex justify-end">
              <button
                type="button"
                onClick={() => setShowModelModal(false)}
                className="px-4 py-2 rounded-xl bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-[12px] font-semibold transition-colors cursor-pointer"
              >
                Close Metadata
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

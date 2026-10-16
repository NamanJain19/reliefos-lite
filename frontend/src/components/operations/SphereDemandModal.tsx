import React, { useState } from 'react';
import { calculateSphereDemand, SphereDemandReport } from '../../services/api';

interface SphereDemandModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyRequisition?: (req: {
    resourceType: string;
    requestedQty: number;
    unit: string;
    priority: string;
    notes: string;
  }) => void;
}

export const SphereDemandModal: React.FC<SphereDemandModalProps> = ({
  isOpen,
  onClose,
  onApplyRequisition
}) => {
  const [params, setParams] = useState({
    population_affected: 3500,
    evacuees_in_shelters: 850,
    time_horizon_hours: 24,
    infant_count: 320,
    elderly_count: 410,
    contingency_buffer_pct: 10
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SphereDemandReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await calculateSphereDemand(params);
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to calculate Sphere humanitarian standards.');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = (resourceType: string, qty: number, unit: string) => {
    if (onApplyRequisition) {
      onApplyRequisition({
        resourceType,
        requestedQty: Math.round(qty),
        unit,
        priority: 'CRITICAL',
        notes: `Sphere 2018 Handbook standard calculation for ${params.population_affected} affected pop (${params.time_horizon_hours}h horizon)`
      });
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
      <div className="bg-surface-container-high rounded-2xl max-w-2xl w-full p-6 border border-outline-variant shadow-2xl animate-fade-in text-on-surface max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-primary text-[26px]">medical_services</span>
            <div>
              <h3 className="text-base font-bold text-on-surface">Sphere Humanitarian Standards Calculator</h3>
              <p className="text-[11px] font-mono-data text-outline">Sphere Handbook 2018 Humanitarian Charter Baseline</p>
            </div>
          </div>
          <button onClick={onClose} className="text-outline hover:text-on-surface">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={handleCalculate} className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-xs font-mono-data">
          <div>
            <label className="block text-outline mb-1 font-semibold">Total Affected Pop</label>
            <input
              type="number"
              min={1}
              value={params.population_affected}
              onChange={(e) => setParams({ ...params, population_affected: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface font-bold text-xs"
            />
          </div>

          <div>
            <label className="block text-outline mb-1 font-semibold">Sheltered Evacuees</label>
            <input
              type="number"
              min={0}
              value={params.evacuees_in_shelters}
              onChange={(e) => setParams({ ...params, evacuees_in_shelters: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface font-bold text-xs"
            />
          </div>

          <div>
            <label className="block text-outline mb-1 font-semibold">Horizon</label>
            <select
              value={params.time_horizon_hours}
              onChange={(e) => setParams({ ...params, time_horizon_hours: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface font-bold text-xs"
            >
              <option value={24}>24 Hours (Immediate)</option>
              <option value={72}>72 Hours (Surge)</option>
              <option value={168}>7 Days (Sustenance)</option>
            </select>
          </div>

          <div>
            <label className="block text-outline mb-1 font-semibold">Infant Count (&lt;2y)</label>
            <input
              type="number"
              min={0}
              value={params.infant_count}
              onChange={(e) => setParams({ ...params, infant_count: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
            />
          </div>

          <div>
            <label className="block text-outline mb-1 font-semibold">Elderly / Vulnerable</label>
            <input
              type="number"
              min={0}
              value={params.elderly_count}
              onChange={(e) => setParams({ ...params, elderly_count: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
            />
          </div>

          <div>
            <label className="block text-outline mb-1 font-semibold">Contingency Buffer %</label>
            <input
              type="number"
              min={0}
              max={50}
              value={params.contingency_buffer_pct}
              onChange={(e) => setParams({ ...params, contingency_buffer_pct: Number(e.target.value) })}
              className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
            />
          </div>

          <div className="md:col-span-3 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-primary text-on-primary font-bold hover:brightness-110 shadow-sm flex items-center gap-2 text-xs"
            >
              <span className={`material-symbols-outlined text-[16px] ${loading ? 'animate-spin' : ''}`}>
                {loading ? 'sync' : 'calculate'}
              </span>
              <span>{loading ? 'Computing Sphere Baselines...' : 'Compute Humanitarian Quotas'}</span>
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-error/20 border border-error/40 text-error text-xs font-mono-data">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-4 pt-4 border-t border-outline-variant/30 flex flex-col gap-4 font-mono-data text-xs">
            {/* Standards Citation */}
            <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/30 flex items-center justify-between text-[11px]">
              <div>
                <span className="text-primary font-bold block">{result.standard_reference}</span>
                <span className="text-outline">Energy: 2,100 kcal/person/day • Water: 15.0 L/person/day</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-primary/20 text-primary font-bold">SPHERE VERIFIED</span>
            </div>

            {/* Metrics Output Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
              <div className="p-3 rounded-xl bg-surface-container-low border border-primary/30">
                <span className="text-[10px] text-outline block">TOTAL FOOD REQUIRED</span>
                <span className="text-base font-bold text-primary">
                  {result.consolidated_humanitarian_requirement?.total_food_dry_kg} kg
                </span>
                <button
                  type="button"
                  onClick={() => handleApply('Food Supplies', result.consolidated_humanitarian_requirement?.total_food_dry_kg, 'kg')}
                  className="mt-1.5 px-2 py-0.5 rounded bg-primary/20 text-primary hover:bg-primary/30 text-[10px] font-bold w-full"
                >
                  Create Requisition
                </button>
              </div>

              <div className="p-3 rounded-xl bg-surface-container-low border border-secondary/30">
                <span className="text-[10px] text-outline block">POTABLE WATER</span>
                <span className="text-base font-bold text-secondary">
                  {result.consolidated_humanitarian_requirement?.total_potable_water_litres} L
                </span>
                <button
                  type="button"
                  onClick={() => handleApply('Potable Water', result.consolidated_humanitarian_requirement?.total_potable_water_litres, 'L')}
                  className="mt-1.5 px-2 py-0.5 rounded bg-secondary/20 text-secondary hover:bg-secondary/30 text-[10px] font-bold w-full"
                >
                  Create Requisition
                </button>
              </div>

              <div className="p-3 rounded-xl bg-surface-container-low border border-tertiary/30">
                <span className="text-[10px] text-outline block">SHELTER TARPAULINS</span>
                <span className="text-base font-bold text-tertiary">
                  {result.consolidated_humanitarian_requirement?.emergency_tarpaulins_units} units
                </span>
                <button
                  type="button"
                  onClick={() => handleApply('Tarpaulins', result.consolidated_humanitarian_requirement?.emergency_tarpaulins_units, 'units')}
                  className="mt-1.5 px-2 py-0.5 rounded bg-tertiary/20 text-tertiary hover:bg-tertiary/30 text-[10px] font-bold w-full"
                >
                  Create Requisition
                </button>
              </div>

              <div className="p-3 rounded-xl bg-surface-container-low border border-purple-400/30">
                <span className="text-[10px] text-outline block">HYGIENE KITS</span>
                <span className="text-base font-bold text-purple-400">
                  {result.consolidated_humanitarian_requirement?.hygiene_kits_units} kits
                </span>
                <button
                  type="button"
                  onClick={() => handleApply('Hygiene Kits', result.consolidated_humanitarian_requirement?.hygiene_kits_units, 'kits')}
                  className="mt-1.5 px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 text-[10px] font-bold w-full"
                >
                  Create Requisition
                </button>
              </div>
            </div>

            {/* Multi-horizon Breakdown */}
            <div className="p-3 rounded-xl bg-surface-container border border-outline-variant/20 flex flex-col gap-1.5">
              <span className="text-[10px] text-outline uppercase font-bold">Multi-Horizon Food Projections</span>
              <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
                <div className="p-1.5 rounded bg-surface-container-high">
                  <span className="text-outline block text-[10px]">24h Immediate</span>
                  <span className="font-bold text-on-surface">{result.horizon_breakdown['24_hours_immediate_kg']} kg</span>
                </div>
                <div className="p-1.5 rounded bg-surface-container-high">
                  <span className="text-outline block text-[10px]">72h Surge</span>
                  <span className="font-bold text-secondary">{result.horizon_breakdown['72_hours_surge_kg']} kg</span>
                </div>
                <div className="p-1.5 rounded bg-surface-container-high">
                  <span className="text-outline block text-[10px]">7-Day Sustenance</span>
                  <span className="font-bold text-primary">{result.horizon_breakdown['7_days_sustenance_kg']} kg</span>
                </div>
              </div>
            </div>

            {/* Uncertainty Notice */}
            <p className="text-[10px] text-outline leading-relaxed italic">
              {result.uncertainty_and_governance_notice}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

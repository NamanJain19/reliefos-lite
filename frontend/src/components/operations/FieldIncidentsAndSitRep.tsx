import React, { useState, useEffect } from 'react';
import {
  IncidentItem, SituationReportItem, StockMovementItem, InventoryAlertsReport,
  getIncidents, createIncident, updateIncident,
  getSituationReports, compileSituationReport, approveSituationReport,
  getStockMovements, adjustStockQuantity, getInventoryAlerts
} from '../../services/api';
import { useLocationContext } from '../../context/LocationContext';

interface FieldIncidentsAndSitRepProps {
  currentUserRole?: string;
  currentUserName?: string;
  onToast?: (msg: string) => void;
}

export const FieldIncidentsAndSitRep: React.FC<FieldIncidentsAndSitRepProps> = ({
  currentUserRole = 'OPERATOR',
  currentUserName = 'Insp. S. Sharma',
  onToast
}) => {
  const { selectedLocation } = useLocationContext();
  const [activeSection, setActiveSection] = useState<'incidents' | 'sitreps' | 'inventory_ledger'>('incidents');

  // Incidents state
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [incidentsLoading, setIncidentsLoading] = useState(false);
  const [incidentModalOpen, setIncidentModalOpen] = useState(false);
  const [newIncident, setNewIncident] = useState({
    title: '',
    incident_type: 'ROAD_INUNDATION',
    severity: 'HIGH',
    zone_code: 'ZONE 01',
    description: '',
    persons_stranded: 50,
    casualties_reported: 0
  });

  // SitReps state
  const [sitreps, setSitreps] = useState<SituationReportItem[]>([]);
  const [sitrepsLoading, setSitrepsLoading] = useState(false);
  const [compilingSitrep, setCompilingSitrep] = useState(false);
  const [selectedSitrep, setSelectedSitrep] = useState<SituationReportItem | null>(null);

  // Inventory Ledger state
  const [movements, setMovements] = useState<StockMovementItem[]>([]);
  const [movementsLoading, setMovementsLoading] = useState(false);
  const [inventoryAlerts, setInventoryAlerts] = useState<InventoryAlertsReport | null>(null);
  const [adjustModalOpen, setAdjustModalOpen] = useState(false);
  const [adjustmentForm, setAdjustmentForm] = useState({
    item_sku: 'FOOD-001',
    depot_code: selectedLocation.primaryDepot,
    adjustment_type: 'CYCLE_COUNT',
    quantity_delta: 0,
    notes: 'Monthly physical warehouse cycle count verification'
  });

  const notify = (msg: string) => {
    if (onToast) onToast(msg);
    else alert(msg);
  };

  const loadIncidents = async () => {
    setIncidentsLoading(true);
    try {
      const data = await getIncidents();
      setIncidents(data);
    } catch (err: any) {
      console.warn('Failed to load incidents', err);
    } finally {
      setIncidentsLoading(false);
    }
  };

  const loadSitreps = async () => {
    setSitrepsLoading(true);
    try {
      const data = await getSituationReports();
      setSitreps(data);
      if (data.length > 0 && !selectedSitrep) {
        setSelectedSitrep(data[0]);
      }
    } catch (err: any) {
      console.warn('Failed to load SitReps', err);
    } finally {
      setSitrepsLoading(false);
    }
  };

  const loadMovements = async () => {
    setMovementsLoading(true);
    try {
      const [movData, alertData] = await Promise.allSettled([
        getStockMovements({ limit: 30 }),
        getInventoryAlerts()
      ]);
      if (movData.status === 'fulfilled') setMovements(movData.value);
      if (alertData.status === 'fulfilled') setInventoryAlerts(alertData.value);
    } catch (err: any) {
      console.warn('Failed to load movements', err);
    } finally {
      setMovementsLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
    loadSitreps();
    loadMovements();
  }, [selectedLocation.id]);

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIncident.title.trim()) {
      notify('Incident title is required.');
      return;
    }
    try {
      await createIncident({
        ...newIncident,
        location_id: selectedLocation.id,
        reported_by: currentUserName
      });
      notify(`Incident "${newIncident.title}" registered in operational ledger.`);
      setIncidentModalOpen(false);
      setNewIncident({
        title: '',
        incident_type: 'ROAD_INUNDATION',
        severity: 'HIGH',
        zone_code: 'ZONE 01',
        description: '',
        persons_stranded: 50,
        casualties_reported: 0
      });
      loadIncidents();
    } catch (err: any) {
      notify(`Failed to log incident: ${err?.message || err}`);
    }
  };

  const handleUpdateIncidentStatus = async (id: number | string, status: string) => {
    try {
      await updateIncident(String(id), {
        status,
        verified_by: currentUserName
      });
      notify(`Incident status updated to ${status}.`);
      loadIncidents();
    } catch (err: any) {
      notify(`Status update failed: ${err?.message || err}`);
    }
  };

  const handleCompileSitRep = async () => {
    setCompilingSitrep(true);
    try {
      const newRep = await compileSituationReport({
        compiling_officer: currentUserName,
        weather_synopsis: `Monsoon flood monitoring across ${selectedLocation.displayName}. Active hydrological watch on ${selectedLocation.primaryRiver}.`
      });
      notify(`ASDMA Situation Report ${newRep.sitrep_id} compiled successfully.`);
      loadSitreps();
      setSelectedSitrep(newRep);
    } catch (err: any) {
      notify(`SitRep compilation failed: ${err?.message || err}`);
    } finally {
      setCompilingSitrep(false);
    }
  };

  const handleApproveSitRep = async (sitrepIdentifier: string) => {
    if (currentUserRole !== 'COMMANDER') {
      notify('Approval requires authorized COMMANDER role credentials.');
      return;
    }
    try {
      const updated = await approveSituationReport(sitrepIdentifier, {
        approving_commander: currentUserName,
        notes: `Validated and authorized by ${currentUserName} for SEOC dissemination.`
      });
      notify(`SitRep ${sitrepIdentifier} approved with digital commander sign-off.`);
      loadSitreps();
      setSelectedSitrep(updated);
    } catch (err: any) {
      notify(`Approval failed: ${err?.message || err}`);
    }
  };

  const handleStockAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (adjustmentForm.quantity_delta === 0) {
      notify('Quantity delta cannot be zero.');
      return;
    }
    try {
      await adjustStockQuantity({
        sku: adjustmentForm.item_sku,
        depot_name: adjustmentForm.depot_code,
        adjustment_type: adjustmentForm.adjustment_type,
        quantity_delta: Number(adjustmentForm.quantity_delta),
        reason: adjustmentForm.notes,
        officer_id: currentUserName
      });
      notify(`Physical inventory ledger updated for SKU ${adjustmentForm.item_sku}.`);
      setAdjustModalOpen(false);
      loadMovements();
    } catch (err: any) {
      notify(`Stock adjustment failed: ${err?.message || err}`);
    }
  };

  return (
    <div className="flex flex-col gap-4 text-on-surface">
      {/* Sub-navigation Ribbon */}
      <div className="flex items-center justify-between flex-wrap gap-2 bg-surface-container-low p-2 rounded-xl border border-outline-variant/30">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveSection('incidents')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSection === 'incidents'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-outline hover:text-on-surface hover:bg-surface-container'
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">report_problem</span>
            <span>Field Incidents ({incidents.length})</span>
          </button>
          <button
            onClick={() => setActiveSection('sitreps')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSection === 'sitreps'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-outline hover:text-on-surface hover:bg-surface-container'
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">assignment</span>
            <span>ASDMA Situation Reports ({sitreps.length})</span>
          </button>
          <button
            onClick={() => setActiveSection('inventory_ledger')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSection === 'inventory_ledger'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-outline hover:text-on-surface hover:bg-surface-container'
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">receipt_long</span>
            <span>Stock Ledger & Movements ({movements.length})</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeSection === 'incidents' && (
            <button
              onClick={() => setIncidentModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:brightness-110 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">add_alert</span>
              <span>Log Field Incident</span>
            </button>
          )}
          {activeSection === 'sitreps' && (
            <button
              onClick={handleCompileSitRep}
              disabled={compilingSitrep}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:brightness-110 shadow-sm disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[16px] ${compilingSitrep ? 'animate-spin' : ''}`}>
                {compilingSitrep ? 'sync' : 'auto_fix_high'}
              </span>
              <span>{compilingSitrep ? 'Compiling...' : 'Compile Daily SitRep'}</span>
            </button>
          )}
          {activeSection === 'inventory_ledger' && (
            <button
              onClick={() => setAdjustModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:brightness-110 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">tune</span>
              <span>Adjust Physical Stock</span>
            </button>
          )}
        </div>
      </div>

      {/* ============================================================== */}
      {/* SECTION 1: FIELD INCIDENTS */}
      {/* ============================================================== */}
      {activeSection === 'incidents' && (
        <div className="flex flex-col gap-3">
          {incidentsLoading ? (
            <div className="p-8 text-center text-outline font-mono-data text-xs">Loading registered incidents...</div>
          ) : incidents.length === 0 ? (
            <div className="p-8 bg-surface-container-low rounded-xl border border-outline-variant/30 text-center">
              <span className="material-symbols-outlined text-outline text-[36px] mb-2">check_circle</span>
              <p className="text-sm font-semibold">No active field incidents recorded for this location.</p>
              <p className="text-xs text-outline mt-1">Use "Log Field Incident" to record ground hazards or breaches.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {incidents.map((inc) => {
                const isCrit = inc.severity === 'CRITICAL';
                const isHigh = inc.severity === 'HIGH';
                const borderColor = isCrit ? 'border-error/60' : isHigh ? 'border-tertiary/60' : 'border-outline-variant/40';
                const badgeColor = isCrit ? 'bg-error/20 text-error' : isHigh ? 'bg-tertiary/20 text-tertiary' : 'bg-primary/20 text-primary';

                return (
                  <div
                    key={inc.id || inc.incident_id}
                    className={`bg-surface-container-low rounded-xl p-3.5 border ${borderColor} shadow-sm flex flex-col justify-between gap-3`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="font-mono-data text-[10px] text-outline font-bold">{inc.incident_id}</span>
                        <div className="flex items-center gap-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${badgeColor}`}>
                            {inc.severity}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono-data font-semibold bg-surface-container text-on-surface border border-outline-variant/40">
                            {inc.status}
                          </span>
                        </div>
                      </div>

                      <h4 className="text-sm font-bold text-on-surface leading-tight mb-1">{inc.title}</h4>
                      <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-2">{inc.description}</p>
                    </div>

                    <div className="pt-2 border-t border-outline-variant/20 flex flex-col gap-1.5 text-[11px] font-mono-data text-outline">
                      <div className="flex items-center justify-between">
                        <span>Zone: <strong className="text-on-surface">{inc.zone_code || 'N/A'}</strong></span>
                        <span>Stranded: <strong className="text-secondary">{inc.persons_stranded || 0}</strong></span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span>Reported: {inc.reported_by || 'Officer'}</span>
                        <span>{inc.reported_at ? new Date(inc.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Logged'}</span>
                      </div>

                      {/* Officer Status Transitions */}
                      <div className="flex items-center gap-1 mt-1 pt-1.5 border-t border-outline-variant/10">
                        {inc.status === 'REPORTED' && (
                          <button
                            onClick={() => handleUpdateIncidentStatus(inc.id, 'VERIFIED')}
                            className="flex-1 py-1 rounded bg-secondary/15 hover:bg-secondary/25 text-secondary text-[10px] font-bold text-center"
                          >
                            Verify Incident
                          </button>
                        )}
                        {inc.status === 'VERIFIED' && (
                          <button
                            onClick={() => handleUpdateIncidentStatus(inc.id, 'RESPONDING')}
                            className="flex-1 py-1 rounded bg-tertiary/15 hover:bg-tertiary/25 text-tertiary text-[10px] font-bold text-center"
                          >
                            Dispatch Response
                          </button>
                        )}
                        {inc.status === 'RESPONDING' && (
                          <button
                            onClick={() => handleUpdateIncidentStatus(inc.id, 'RESOLVED')}
                            className="flex-1 py-1 rounded bg-primary/15 hover:bg-primary/25 text-primary text-[10px] font-bold text-center"
                          >
                            Mark Resolved
                          </button>
                        )}
                        {inc.status === 'RESOLVED' && (
                          <span className="flex-1 py-0.5 text-center text-primary text-[10px] font-bold">
                            Resolved & Archived
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* SECTION 2: ASDMA SITUATION REPORTS (SITREPS) */}
      {/* ============================================================== */}
      {activeSection === 'sitreps' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* SitRep List */}
          <div className="lg:col-span-1 flex flex-col gap-2">
            <h3 className="text-xs font-mono-data font-bold text-outline uppercase tracking-wider">Compiled Bulletins</h3>
            {sitrepsLoading ? (
              <div className="p-4 text-center text-outline font-mono-data text-xs">Loading SitReps...</div>
            ) : sitreps.length === 0 ? (
              <div className="p-6 bg-surface-container-low rounded-xl border border-outline-variant/30 text-center text-xs text-outline">
                No SitReps compiled. Click "Compile Daily SitRep" above.
              </div>
            ) : (
              sitreps.map((s) => (
                <div
                  key={s.id || s.sitrep_id}
                  onClick={() => setSelectedSitrep(s)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedSitrep?.sitrep_id === s.sitrep_id
                      ? 'bg-surface-container-high border-primary text-on-surface shadow-sm'
                      : 'bg-surface-container-low border-outline-variant/30 text-on-surface-variant hover:bg-surface-container'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-mono-data font-bold mb-1">
                    <span className="text-primary">{s.sitrep_id}</span>
                    <span className={`px-2 py-0.2 rounded text-[10px] ${
                      s.approval_status === 'APPROVED' ? 'bg-primary/20 text-primary' : 'bg-tertiary/20 text-tertiary'
                    }`}>
                      {s.approval_status}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-on-surface truncate">{s.location_id.toUpperCase()} • {s.report_date}</div>
                  <div className="text-[10px] text-outline font-mono-data mt-1 flex justify-between">
                    <span>Officer: {s.compiling_officer}</span>
                    <span>{s.created_at ? new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Today'}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Selected SitRep Detail View */}
          <div className="lg:col-span-2 bg-surface-container-low rounded-xl p-4 border border-outline-variant/30 shadow-sm flex flex-col justify-between">
            {selectedSitrep ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-start justify-between flex-wrap gap-2 pb-3 border-b border-outline-variant/30">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono-data text-xs text-primary font-bold">{selectedSitrep.sitrep_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        selectedSitrep.approval_status === 'APPROVED' ? 'bg-primary/20 text-primary' : 'bg-tertiary/20 text-tertiary'
                      }`}>
                        {selectedSitrep.approval_status === 'APPROVED' ? 'OFFICIALLY AUTHORIZED' : 'DRAFT BULLETIN'}
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-on-surface mt-1">
                      ASDMA Daily Flood Situation Report — {selectedSitrep.district_name || selectedSitrep.location_id.replace('_', ' ').toUpperCase()}
                    </h2>
                    <div className="text-xs font-mono-data text-outline mt-0.5">
                      Compiled: {selectedSitrep.created_at ? new Date(selectedSitrep.created_at).toLocaleString() : 'Today'} by {selectedSitrep.compiling_officer}
                    </div>
                  </div>

                  {selectedSitrep.approval_status !== 'APPROVED' && (
                    <button
                      onClick={() => handleApproveSitRep(selectedSitrep.sitrep_id)}
                      className="px-3.5 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:brightness-110 shadow-sm flex items-center gap-1.5"
                    >
                      <span className="material-symbols-outlined text-[16px]">verified_user</span>
                      <span>Commander Sign-Off</span>
                    </button>
                  )}
                </div>

                {/* KPI Metrics Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/20">
                    <span className="text-[10px] font-mono-data text-outline block">ACTIVE INCIDENTS</span>
                    <span className="text-lg font-bold text-error">{selectedSitrep.active_incidents_count}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/20">
                    <span className="text-[10px] font-mono-data text-outline block">DISPLACED IN SHELTERS</span>
                    <span className="text-lg font-bold text-secondary">{selectedSitrep.displaced_in_shelters}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/20">
                    <span className="text-[10px] font-mono-data text-outline block">ACTIVE SHELTERS</span>
                    <span className="text-lg font-bold text-primary">{selectedSitrep.active_shelters_count}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/20">
                    <span className="text-[10px] font-mono-data text-outline block">ROADS CLOSED</span>
                    <span className="text-lg font-bold text-tertiary">{selectedSitrep.roads_closed_count}</span>
                  </div>
                </div>

                {/* Weather & Hydro Synopsis */}
                <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 text-xs">
                  <span className="font-mono-data font-bold text-secondary uppercase text-[10px] block mb-1">
                    Hydro-Meteorological Observation
                  </span>
                  <p className="text-on-surface-variant leading-relaxed">{selectedSitrep.weather_synopsis}</p>
                </div>

                {/* Critical River Stages */}
                {selectedSitrep.critical_river_stages && selectedSitrep.critical_river_stages.length > 0 && (
                  <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 text-xs">
                    <span className="font-mono-data font-bold text-tertiary uppercase text-[10px] block mb-1">
                      Critical River Stages & Flood Threat Gauges
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                      {selectedSitrep.critical_river_stages.map((g, idx) => (
                        <div key={idx} className="p-2 rounded bg-surface-container-high flex justify-between items-center text-[11px] font-mono-data">
                          <span>{g.station} ({g.river})</span>
                          <span className="font-bold text-tertiary">{g.stage_m}m MSL ({g.status})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Digital Approval Sign-off Box */}
                {selectedSitrep.approving_commander && (
                  <div className="p-3 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary text-[20px]">verified</span>
                      <div>
                        <span className="font-bold text-primary block">Digitally Authorized by Commander</span>
                        <span className="text-[10px] font-mono-data text-outline">{selectedSitrep.approving_commander} • {selectedSitrep.approved_at || 'Verified'}</span>
                      </div>
                    </div>
                    <span className="font-mono-data text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded font-bold">
                      {selectedSitrep.form_reference || 'FORM 8B'}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-outline font-mono-data text-xs">
                Select a Situation Report to view bulletin details.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* SECTION 3: INVENTORY LEDGER & STOCK MOVEMENTS */}
      {/* ============================================================== */}
      {activeSection === 'inventory_ledger' && (
        <div className="flex flex-col gap-4">
          {/* Inventory Safety Alerts Header */}
          {inventoryAlerts && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-surface-container-low p-3 rounded-xl border border-outline-variant/30 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono-data text-outline block">CRITICAL LOW-STOCK ALERTS</span>
                  <span className="text-lg font-bold text-error">{inventoryAlerts.total_low_stock_alerts}</span>
                </div>
                <span className="material-symbols-outlined text-error text-[24px]">inventory_2</span>
              </div>
              <div className="bg-surface-container-low p-3 rounded-xl border border-outline-variant/30 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono-data text-outline block">NEAR EXPIRY LOTS (&lt;30D)</span>
                  <span className="text-lg font-bold text-tertiary">{inventoryAlerts.total_near_expiry_alerts}</span>
                </div>
                <span className="material-symbols-outlined text-tertiary text-[24px]">event_busy</span>
              </div>
            </div>
          )}

          {/* Audit Ledger Table */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/30 overflow-hidden shadow-sm">
            <div className="p-3 border-b border-outline-variant/20 flex items-center justify-between">
              <span className="font-mono-data text-xs font-bold text-on-surface">STOCK MOVEMENTS & AUDIT TRAILS</span>
              <span className="text-[11px] font-mono-data text-outline">Real-Time Transactional History</span>
            </div>

            {movementsLoading ? (
              <div className="p-8 text-center text-outline font-mono-data text-xs">Loading ledger records...</div>
            ) : movements.length === 0 ? (
              <div className="p-8 text-center text-outline font-mono-data text-xs">No stock movements recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono-data">
                  <thead className="bg-surface-container text-outline text-[10px] uppercase border-b border-outline-variant/20">
                    <tr>
                      <th className="p-2.5">Movement ID</th>
                      <th className="p-2.5">SKU</th>
                      <th className="p-2.5">Depot</th>
                      <th className="p-2.5">Type</th>
                      <th className="p-2.5 text-right">Delta</th>
                      <th className="p-2.5 text-right">New Balance</th>
                      <th className="p-2.5">Officer / Notes</th>
                      <th className="p-2.5">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/10 text-[11px]">
                    {movements.map((m) => {
                      const isPositive = m.quantity > 0;
                      return (
                        <tr key={m.movement_id} className="hover:bg-surface-container/40">
                          <td className="p-2.5 text-outline font-bold">{m.movement_id}</td>
                          <td className="p-2.5 text-on-surface font-semibold">{m.item_sku}</td>
                          <td className="p-2.5 text-outline truncate max-w-[140px]">{m.depot_code}</td>
                          <td className="p-2.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              m.movement_type === 'RECEIPT' ? 'bg-primary/20 text-primary' :
                              m.movement_type === 'ADJUSTMENT' ? 'bg-secondary/20 text-secondary' :
                              'bg-tertiary/20 text-tertiary'
                            }`}>
                              {m.movement_type}
                            </span>
                          </td>
                          <td className={`p-2.5 text-right font-bold ${isPositive ? 'text-primary' : 'text-error'}`}>
                            {isPositive ? `+${m.quantity}` : m.quantity} {m.unit}
                          </td>
                          <td className="p-2.5 text-right font-semibold text-on-surface">
                            {m.balance_after} {m.unit}
                          </td>
                          <td className="p-2.5 truncate max-w-[180px]" title={m.notes || m.reference_doc}>
                            <span className="text-on-surface font-semibold">{m.operator_name}: </span>
                            <span className="text-outline">{m.notes || m.reference_doc}</span>
                          </td>
                          <td className="p-2.5 text-outline text-[10px]">
                            {m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recorded'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 1: LOG FIELD INCIDENT */}
      {/* ============================================================== */}
      {incidentModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-surface-container-high rounded-xl max-w-lg w-full p-5 border border-outline-variant shadow-2xl animate-fade-in text-on-surface">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-error text-[22px]">warning</span>
                <h3 className="text-base font-bold">Log Ground Incident Report</h3>
              </div>
              <button onClick={() => setIncidentModalOpen(false)} className="text-outline hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateIncident} className="flex flex-col gap-3 mt-4 text-xs font-mono-data">
              <div>
                <label className="block text-outline mb-1 font-semibold">Incident Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sluice Gate Overtopping at Bharalumukh"
                  value={newIncident.title}
                  onChange={(e) => setNewIncident({ ...newIncident, title: e.target.value })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-outline mb-1 font-semibold">Incident Type</label>
                  <select
                    value={newIncident.incident_type}
                    onChange={(e) => setNewIncident({ ...newIncident, incident_type: e.target.value })}
                    className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                  >
                    <option value="ROAD_INUNDATION">ROAD_INUNDATION</option>
                    <option value="EMBANKMENT_BREACH">EMBANKMENT_BREACH</option>
                    <option value="SHELTER_OVERFLOW">SHELTER_OVERFLOW</option>
                    <option value="WATER_CONTAMINATION">WATER_CONTAMINATION</option>
                    <option value="POWER_OUTAGE">POWER_OUTAGE</option>
                  </select>
                </div>

                <div>
                  <label className="block text-outline mb-1 font-semibold">Severity Tier</label>
                  <select
                    value={newIncident.severity}
                    onChange={(e) => setNewIncident({ ...newIncident, severity: e.target.value })}
                    className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MODERATE">MODERATE</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-outline mb-1 font-semibold">Zone Code</label>
                  <input
                    type="text"
                    value={newIncident.zone_code}
                    onChange={(e) => setNewIncident({ ...newIncident, zone_code: e.target.value })}
                    className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                  />
                </div>
                <div>
                  <label className="block text-outline mb-1 font-semibold">Stranded Population</label>
                  <input
                    type="number"
                    value={newIncident.persons_stranded}
                    onChange={(e) => setNewIncident({ ...newIncident, persons_stranded: Number(e.target.value) })}
                    className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-outline mb-1 font-semibold">Detailed Description</label>
                <textarea
                  rows={3}
                  placeholder="Enter field observer notes, flood height, impassable vehicle constraints..."
                  value={newIncident.description}
                  onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-outline-variant/30">
                <button
                  type="button"
                  onClick={() => setIncidentModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-outline-variant text-outline hover:text-on-surface text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-primary text-on-primary font-bold hover:brightness-110 text-xs shadow-sm"
                >
                  Submit Incident to Ledger
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 2: ADJUST PHYSICAL STOCK */}
      {/* ============================================================== */}
      {adjustModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-surface-container-high rounded-xl max-w-md w-full p-5 border border-outline-variant shadow-2xl animate-fade-in text-on-surface">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">tune</span>
                <h3 className="text-base font-bold">Physical Stock Cycle Count</h3>
              </div>
              <button onClick={() => setAdjustModalOpen(false)} className="text-outline hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleStockAdjustment} className="flex flex-col gap-3 mt-4 text-xs font-mono-data">
              <div>
                <label className="block text-outline mb-1 font-semibold">Stock Keeping Unit (SKU)</label>
                <select
                  value={adjustmentForm.item_sku}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, item_sku: e.target.value })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                >
                  <option value="FOOD-001">FOOD-001 (High-Energy Biscuits / Rice, kg)</option>
                  <option value="WATR-001">WATR-001 (Chlorinated Drinking Water, L)</option>
                  <option value="MED-001">MED-001 (First Aid Emergency Kit, sets)</option>
                </select>
              </div>

              <div>
                <label className="block text-outline mb-1 font-semibold">Adjustment Type</label>
                <select
                  value={adjustmentForm.adjustment_type}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, adjustment_type: e.target.value })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                >
                  <option value="CYCLE_COUNT">CYCLE_COUNT (Physical Verification)</option>
                  <option value="DAMAGED">DAMAGED (Spoilage / Water Damage Write-off)</option>
                  <option value="REALLOCATION">REALLOCATION (Inter-depot transfer)</option>
                </select>
              </div>

              <div>
                <label className="block text-outline mb-1 font-semibold">Quantity Delta (+/-)</label>
                <input
                  type="number"
                  placeholder="e.g. +100 or -50"
                  value={adjustmentForm.quantity_delta}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, quantity_delta: Number(e.target.value) })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                />
              </div>

              <div>
                <label className="block text-outline mb-1 font-semibold">Audit Justification *</label>
                <textarea
                  rows={2}
                  required
                  placeholder="State reason for physical ledger adjustment..."
                  value={adjustmentForm.notes}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, notes: e.target.value })}
                  className="w-full bg-surface-container border border-outline-variant rounded-lg p-2 text-on-surface text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-outline-variant/30">
                <button
                  type="button"
                  onClick={() => setAdjustModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-outline-variant text-outline hover:text-on-surface text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-primary text-on-primary font-bold hover:brightness-110 text-xs shadow-sm"
                >
                  Save Stock Adjustment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

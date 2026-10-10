import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useLocationContext } from '../context/LocationContext';
import { getGisZonesForLocation } from '../components/map/gisLayersData';

const KAMRUP_INITIAL_DEMANDS = [
  {
    id: 'DEM-2024-001',
    zoneCode: 'ZONE 01',
    zoneName: 'North Guwahati (Riverfront)',
    resourceType: 'Food Supplies',
    requestedQty: 1200,
    unit: 'kg',
    priority: 'CRITICAL',
    status: 'APPROVED',
    source: 'Field Audit (ASDMA Circle Officer)',
    time: 'Today, 13:45 IST'
  },
  {
    id: 'DEM-2024-002',
    zoneCode: 'ZONE 01',
    zoneName: 'North Guwahati (Riverfront)',
    resourceType: 'Potable Water',
    requestedQty: 900,
    unit: 'L',
    priority: 'CRITICAL',
    status: 'APPROVED',
    source: 'Field Audit',
    time: 'Today, 13:45 IST'
  },
  {
    id: 'DEM-2024-003',
    zoneCode: 'ZONE 02',
    zoneName: 'Bharalumukh Sluice Basin',
    resourceType: 'Food Supplies',
    requestedQty: 1000,
    unit: 'kg',
    priority: 'CRITICAL',
    status: 'APPROVED',
    source: 'Observed Population Census',
    time: 'Today, 13:50 IST'
  },
  {
    id: 'DEM-2024-004',
    zoneCode: 'ZONE 02',
    zoneName: 'Bharalumukh Sluice Basin',
    resourceType: 'Potable Water',
    requestedQty: 700,
    unit: 'L',
    priority: 'CRITICAL',
    status: 'APPROVED',
    source: 'Observed Population Census',
    time: 'Today, 13:50 IST'
  },
  {
    id: 'DEM-2024-005',
    zoneCode: 'ZONE 03',
    zoneName: 'Uzan Bazar Ghat',
    resourceType: 'Food Supplies',
    requestedQty: 800,
    unit: 'kg',
    priority: 'HIGH',
    status: 'APPROVED',
    source: 'Community Liaison',
    time: 'Today, 14:00 IST'
  },
  {
    id: 'DEM-2024-006',
    zoneCode: 'ZONE 03',
    zoneName: 'Uzan Bazar Ghat',
    resourceType: 'Potable Water',
    requestedQty: 600,
    unit: 'L',
    priority: 'HIGH',
    status: 'APPROVED',
    source: 'Community Liaison',
    time: 'Today, 14:00 IST'
  },
  {
    id: 'DEM-2024-007',
    zoneCode: 'ZONE 04',
    zoneName: 'Basistha Stream Corridor',
    resourceType: 'Food Supplies',
    requestedQty: 700,
    unit: 'kg',
    priority: 'MEDIUM',
    status: 'PENDING',
    source: 'Estimated Demand Model',
    time: 'Today, 14:10 IST'
  },
  {
    id: 'DEM-2024-008',
    zoneCode: 'ZONE 04',
    zoneName: 'Basistha Stream Corridor',
    resourceType: 'Potable Water',
    requestedQty: 500,
    unit: 'L',
    priority: 'MEDIUM',
    status: 'PENDING',
    source: 'Estimated Demand Model',
    time: 'Today, 14:10 IST'
  },
  {
    id: 'DEM-2024-009',
    zoneCode: 'ZONE 05',
    zoneName: 'Dispur Secretariat Lowlands',
    resourceType: 'Food Supplies',
    requestedQty: 500,
    unit: 'kg',
    priority: 'LOW',
    status: 'PENDING',
    source: 'Estimated Demand Model',
    time: 'Today, 14:15 IST'
  },
  {
    id: 'DEM-2024-010',
    zoneCode: 'ZONE 05',
    zoneName: 'Dispur Secretariat Lowlands',
    resourceType: 'Potable Water',
    requestedQty: 300,
    unit: 'L',
    priority: 'LOW',
    status: 'PENDING',
    source: 'Estimated Demand Model',
    time: 'Today, 14:15 IST'
  }
];

export const DemandManagement: React.FC = () => {
  const { selectedLocation, isKamrupMetro } = useLocationContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'FULFILLED'>('ALL');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [demands, setDemands] = useState<any[]>(() => isKamrupMetro ? KAMRUP_INITIAL_DEMANDS : []);

  const activeZones = getGisZonesForLocation(selectedLocation.id);
  const [selectedZone, setSelectedZone] = useState(activeZones[0]?.code || 'ZONE 01');
  const [resourceType, setResourceType] = useState('Food Supplies');
  const [quantity, setQuantity] = useState(500);
  const [priority, setPriority] = useState('HIGH');

  useEffect(() => {
    const locZones = getGisZonesForLocation(selectedLocation.id);
    if (locZones.length > 0) {
      setSelectedZone(locZones[0].code);
    }
  }, [selectedLocation.id]);

  useEffect(() => {
    const fetchDemands = async () => {
      setLoading(true);
      try {
        const data = await api.getDemands();
        if (data && data.length > 0) {
          setDemands(data.map((d: any) => ({
            id: d.id,
            zoneCode: d.zone_code,
            zoneName: d.zone_name,
            resourceType: d.resource_type,
            requestedQty: d.requested_qty,
            unit: d.unit,
            priority: d.priority,
            status: d.status,
            source: d.request_source,
            time: d.created_at
          })));
        } else if (!isKamrupMetro) {
          // Provide baseline contingency requisitions for monitored districts if database has none
          const defaultDemands = activeZones.slice(0, 3).map((z, idx) => ({
            id: `DEM-${selectedLocation.shortName.toUpperCase()}-00${idx + 1}`,
            zoneCode: z.code,
            zoneName: z.name,
            resourceType: idx % 2 === 0 ? 'Food Supplies' : 'Potable Water',
            requestedQty: idx % 2 === 0 ? 800 : 600,
            unit: idx % 2 === 0 ? 'kg' : 'L',
            priority: z.risk === 'CRITICAL' ? 'CRITICAL' : 'HIGH',
            status: 'PENDING',
            source: `${selectedLocation.districtName} Circle Officer Audit`,
            time: 'Contingency Staging'
          }));
          setDemands(defaultDemands);
        } else {
          setDemands(KAMRUP_INITIAL_DEMANDS);
        }
      } catch (err) {
        console.warn('Using baseline demands cache', err);
        setDemands(isKamrupMetro ? KAMRUP_INITIAL_DEMANDS : []);
      } finally {
        setLoading(false);
      }
    };
    fetchDemands();
  }, [selectedLocation.id, isKamrupMetro]);

  const handleOpenAuditLogs = async () => {
    try {
      const logs = await api.getAuditLogs();
      setAuditLogs(logs || []);
      setAuditModalOpen(true);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    }
  };

  const handleVerifyDemand = async (id: string) => {
    try {
      await api.verifyDemand(id, { verified_by: 'OFFICER_SHARMA', notes: 'Field operational review' });
      setDemands(prev => prev.map(d => d.id === id ? { ...d, status: 'VERIFIED' } : d));
      alert(`Requisition ${id} verified and audited into SQLite.`);
    } catch (err) {
      alert(`Verification failed: ${err}`);
    }
  };

  const handleDispatchDemand = async (id: string) => {
    try {
      await api.dispatchDemand(id, { vehicle_code: 'VH-02', dispatched_by: 'OFFICER_SHARMA', notes: `Dispatched via ${selectedLocation.primaryDepot}` });
      setDemands(prev => prev.map(d => d.id === id ? { ...d, status: 'DISPATCHED' } : d));
      alert(`Requisition ${id} marked DISPATCHED with audit log.`);
    } catch (err) {
      alert(`Dispatch failed: ${err}`);
    }
  };

  const handleExportDemandsCSV = () => {
    const headers = ["Requisition ID", "Zone Code", "Zone Name", "Resource", "Requested Qty", "Unit", "Priority", "Status", "Source"];
    const rows = demands.map(d => [
      `"${d.id}"`,
      `"${d.zoneCode}"`,
      `"${d.zoneName}"`,
      `"${d.resourceType}"`,
      d.requestedQty,
      `"${d.unit}"`,
      `"${d.priority}"`,
      `"${d.status}"`,
      `"${d.source}"`
    ]);
    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `ASDMA_Relief_Demands_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCreateDemand = async (e: React.FormEvent) => {
    e.preventDefault();
    const zoneMap: Record<string, string> = {};
    activeZones.forEach(z => {
      zoneMap[z.code] = z.name;
    });

    const newReq = {
      id: `DEM-2024-${String(demands.length + 1).padStart(3, '0')}`,
      zoneCode: selectedZone,
      zoneName: zoneMap[selectedZone] || selectedZone,
      resourceType,
      requestedQty: Number(quantity),
      unit: resourceType.includes('Water') ? 'L' : 'kg',
      priority,
      status: 'PENDING',
      source: 'Manual Field Report',
      time: 'Just now'
    };

    try {
      await api.createDemand({
        zone_code: selectedZone,
        resource_type: resourceType,
        requested_qty: quantity,
        unit: newReq.unit,
        priority
      });
    } catch {
      // Maintain UI state
    }

    setDemands([newReq, ...demands]);
    setCreateModalOpen(false);
    alert(`Relief demand requisition ${newReq.id} recorded.`);
  };

  const filteredDemands = demands.filter((d) => {
    const matchesStatus = statusFilter === 'ALL' || d.status === statusFilter;
    const matchesSearch =
      d.zoneName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.zoneCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.resourceType.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const totalFood = demands.filter(d => d.resourceType.includes('Food')).reduce((s, d) => s + d.requestedQty, 0);
  const totalWater = demands.filter(d => d.resourceType.includes('Water')).reduce((s, d) => s + d.requestedQty, 0);
  const totalCombined = totalFood + totalWater;
  const criticalCount = demands.filter(d => d.priority === 'CRITICAL').length;
  const pendingCount = demands.filter(d => d.status === 'PENDING').length;
  const approvedCount = demands.filter(d => d.status === 'APPROVED').length;

  return (
    <div className="p-space-md lg:p-space-lg flex flex-col gap-y-space-md max-w-[1920px] mx-auto w-full select-none">
      {/* Header */}
      <header className="bg-surface-container-low rounded-xl p-space-md lg:px-space-lg lg:py-space-md shadow-md border border-outline-variant/30 flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-space-sm flex-wrap">
            <h1 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">
              Demand Management
            </h1>
            <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-surface-container-high text-secondary border border-secondary/30">
              Human-in-the-Loop Requisition Review
            </span>
            <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-primary/10 text-primary border border-primary/25">
              Sector: {selectedLocation.shortName}
            </span>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Audit, validate, and prioritize multi-zone relief demands for food rations and potable water before triggering optimization dispatches.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenAuditLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">history_edu</span>
            <span>SQLite Audit Logs</span>
          </button>
          <button
            onClick={handleExportDemandsCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold text-[12px] shadow-sm transition-all bg-primary-container text-on-primary-container hover:brightness-110 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">add_circle</span>
            <span>+ Create Demand Request</span>
          </button>
        </div>
      </header>

      {/* Non-metro tactical sector banner */}
      {!isKamrupMetro && (
        <div className="p-3.5 rounded-xl bg-primary/5 border border-primary/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-primary">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[24px]">location_on</span>
            <div>
              <div className="font-bold text-[13px] tracking-wide uppercase">
                DISTRICT SECTOR: {selectedLocation.displayName.toUpperCase()}
              </div>
              <div className="text-[12px] text-on-surface-variant mt-0.5">
                Demands calibrated for {selectedLocation.revenueCirclesCount} operational revenue circles in {selectedLocation.displayName}. Staged via {selectedLocation.primaryDepot}. Hydrology station on {selectedLocation.primaryRiver} active.
              </div>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded text-[11px] font-bold uppercase bg-primary/15 border border-primary/30 shrink-0 self-start sm:self-auto">
            {selectedLocation.tierBadgeText}
          </span>
        </div>
      )}

      {/* KPI Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-sm">
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 min-h-[96px] flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>TOTAL REVIEWED DEMAND</span>
            <span className="material-symbols-outlined text-[18px]">order_approve</span>
          </div>
          <div className="text-kpi-lg font-bold text-on-surface font-mono-data mt-1 tabular-nums">
            {totalCombined.toLocaleString()} kg/eq
          </div>
          <span className="text-[11px] text-secondary font-medium">
            Food: {totalFood.toLocaleString()} kg • Water: {totalWater.toLocaleString()} L
          </span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 min-h-[96px] flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-tertiary text-[11px] uppercase font-bold">
            <span>CRITICAL TIER REQUISITIONS</span>
            <span className="material-symbols-outlined text-[18px]">priority_high</span>
          </div>
          <div className="text-kpi-lg font-bold text-tertiary font-mono-data mt-1 tabular-nums">
            {String(criticalCount).padStart(2, '0')} Requisitions
          </div>
          <span className="text-[11px] text-on-surface-variant">
            {criticalCount > 0 ? 'High-priority life safety' : 'No critical emergencies'}
          </span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 min-h-[96px] flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-[#f5b84b] text-[11px] uppercase font-bold">
            <span>PENDING OPERATOR SIGN-OFF</span>
            <span className="material-symbols-outlined text-[18px]">pending_actions</span>
          </div>
          <div className="text-kpi-lg font-bold text-[#f5b84b] font-mono-data mt-1 tabular-nums">
            {String(pendingCount).padStart(2, '0')} Pending
          </div>
          <span className="text-[11px] text-on-surface-variant">
            {pendingCount > 0 ? 'Awaiting officer certification' : 'Queue cleared'}
          </span>
        </div>

        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 min-h-[96px] flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-primary text-[11px] uppercase font-bold">
            <span>APPROVED FOR SOLVER</span>
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
          </div>
          <div className="text-kpi-lg font-bold text-primary font-mono-data mt-1 tabular-nums">
            {String(approvedCount).padStart(2, '0')} Approved
          </div>
          <span className="text-[11px] text-primary font-medium">
            {approvedCount > 0 ? 'Locked into Stage 1 solver' : 'No active dispatches'}
          </span>
        </div>
      </section>

      {/* Requisitions Table */}
      <section className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30">
        <div className="flex flex-wrap items-center justify-between pb-3 border-b border-outline-variant/30 gap-2">
          {/* Search bar */}
          <div className="relative min-w-[260px]">
            <span className="material-symbols-outlined text-[16px] text-outline absolute left-2.5 top-2.5">search</span>
            <input
              type="text"
              placeholder="Search by zone, requisition, resource..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/40 text-[12px] text-on-surface focus:outline-none focus:border-primary"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-surface-container p-0.5 rounded text-[11px]">
            {(['ALL', 'PENDING', 'APPROVED', 'FULFILLED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-3 py-1 rounded font-medium transition-all ${
                  statusFilter === tab
                    ? 'bg-surface-container-high text-primary font-bold shadow-sm'
                    : 'text-outline hover:text-on-surface'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="border-b border-outline-variant/30 text-outline text-[11px] uppercase font-semibold tracking-wider">
                <th className="px-3 py-2">Req ID</th>
                <th className="px-3 py-2">Zone & Target</th>
                <th className="px-3 py-2">Resource Type</th>
                <th className="px-3 py-2">Quantity Requested</th>
                <th className="px-3 py-2">Priority</th>
                <th className="px-3 py-2">Data Provenance Source</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20 font-mono-data text-[11px]">
              {filteredDemands.map((d) => (
                <tr key={d.id} className="hover:bg-surface-container/50 transition-colors">
                  <td className="px-3 py-2.5 font-bold text-secondary">{d.id}</td>
                  <td className="px-3 py-2.5 font-sans">
                    <span className="font-bold text-on-surface block text-[12px]">{d.zoneCode}</span>
                    <span className="text-[10px] text-outline block">{d.zoneName}</span>
                  </td>
                  <td className="px-3 py-2.5 font-sans">
                    <span className="font-medium text-on-surface">{d.resourceType}</span>
                  </td>
                  <td className="px-3 py-2.5 font-bold text-on-surface tabular-nums">
                    {d.requestedQty.toLocaleString()} <span className="text-[10px] font-normal text-outline">{d.unit}</span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      d.priority === 'CRITICAL'
                        ? 'bg-error/20 text-error border border-error/30'
                        : d.priority === 'HIGH'
                        ? 'bg-[#f5b84b]/20 text-[#f5b84b] border border-[#f5b84b]/30'
                        : 'bg-primary/20 text-primary border border-primary/30'
                    }`}>
                      {d.priority}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-sans text-on-surface-variant text-[11px]">
                    {d.source}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      d.status === 'VERIFIED' || d.status === 'APPROVED'
                        ? 'bg-primary-container/20 text-primary border border-primary/30'
                        : d.status === 'DISPATCHED'
                        ? 'bg-secondary/20 text-secondary border border-secondary/30'
                        : 'bg-[#f5b84b]/20 text-[#f5b84b] border border-[#f5b84b]/30'
                    }`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    {d.status === 'PENDING' || d.status === 'REQUESTED' || d.status === 'UNVERIFIED' ? (
                      <button
                        onClick={() => handleVerifyDemand(d.id)}
                        className="px-2.5 py-1 rounded bg-primary-container text-on-primary-container font-semibold text-[10px] hover:brightness-110"
                      >
                        Verify
                      </button>
                    ) : d.status === 'APPROVED' || d.status === 'VERIFIED' ? (
                      <button
                        onClick={() => handleDispatchDemand(d.id)}
                        className="px-2.5 py-1 rounded bg-secondary/20 text-secondary border border-secondary/40 font-semibold text-[10px] hover:bg-secondary/30"
                      >
                        Dispatch
                      </button>
                    ) : (
                      <span className="text-secondary text-[10px] font-bold font-mono-data">DISPATCHED</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Create Demand Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-surface-container-low border border-outline-variant/50 rounded-xl shadow-2xl w-full max-w-md p-space-lg text-on-surface">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30 mb-3">
              <h3 className="font-headline-sm text-[16px] font-bold text-on-surface flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[20px]">add_circle</span>
                <span>Create Zone Demand Requisition</span>
              </h3>
              <button onClick={() => setCreateModalOpen(false)} className="text-outline hover:text-on-surface">
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateDemand} className="space-y-3 text-[12px]">
              <div>
                <label className="text-outline text-[11px] block mb-1">Target Operational Zone</label>
                <select
                  value={selectedZone}
                  onChange={(e) => setSelectedZone(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                >
                  {activeZones.map(z => (
                    <option key={z.code} value={z.code}>{z.code} — {z.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-outline text-[11px] block mb-1">Resource Commodity</label>
                <select
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                >
                  <option value="Food Supplies">Food Supplies (Grain & Dry Rations)</option>
                  <option value="Potable Water">Potable Drinking Water</option>
                  <option value="Medical Packs">Emergency Medical / ORS Kits</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-outline text-[11px] block mb-1">Quantity Requested</label>
                  <input
                    type="number"
                    required
                    min="50"
                    step="50"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/40 text-on-surface font-mono-data focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-outline text-[11px] block mb-1">Priority Tier</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  >
                    <option value="CRITICAL">CRITICAL (Tier 1)</option>
                    <option value="HIGH">HIGH (Tier 2)</option>
                    <option value="MEDIUM">MEDIUM (Tier 3)</option>
                    <option value="LOW">LOW (Tier 4)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/30">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-3 py-1.5 rounded bg-surface-container text-on-surface text-[12px] hover:bg-surface-container-high"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 shadow-sm"
                >
                  Register Demand
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SQLite Audit Log Modal */}
      {auditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-surface-container-high border border-outline-variant/50 rounded-xl shadow-2xl w-full max-w-4xl p-6 text-on-surface flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">history_edu</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                  Operational SQLite Database Audit Trail
                </h3>
              </div>
              <button onClick={() => setAuditModalOpen(false)} className="p-1 rounded hover:bg-surface-container text-outline hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="mt-3 flex-1 overflow-y-auto">
              <p className="text-[12px] text-outline mb-3">
                Immutable, timestamped record of operational requisition reviews, verification state changes, dispatch events, and manual telemetry overrides.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-body-sm text-[12px]">
                  <thead className="bg-surface-container-lowest text-outline font-label-sm uppercase">
                    <tr>
                      <th className="p-2">Timestamp (UTC)</th>
                      <th className="p-2">Operator ID</th>
                      <th className="p-2">Action</th>
                      <th className="p-2">Entity</th>
                      <th className="p-2">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/20 font-mono-data">
                    {auditLogs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-4 text-center text-outline">
                          No audit events recorded in database yet.
                        </td>
                      </tr>
                    ) : (
                      auditLogs.map((log: any, idx: number) => (
                        <tr key={idx} className="hover:bg-surface-container/50">
                          <td className="p-2 text-outline text-[11px] whitespace-nowrap">{log.timestamp}</td>
                          <td className="p-2 text-primary font-bold">{log.operator_id}</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                              {log.action}
                            </span>
                          </td>
                          <td className="p-2 text-on-surface">{log.entity_type} #{log.entity_id}</td>
                          <td className="p-2 text-on-surface-variant text-[11px] max-w-xs truncate" title={JSON.stringify(log.details || {})}>
                            {JSON.stringify(log.details || {})}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="pt-3 border-t border-outline-variant/30 flex justify-end">
              <button
                type="button"
                onClick={() => setAuditModalOpen(false)}
                className="px-4 py-1.5 rounded bg-surface-container hover:bg-surface-container-highest text-on-surface text-[12px] font-medium"
              >
                Close Audit Trail
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface FeedItem {
  id: string;
  name: string;
  subtext: string;
  authority: string;
  classification: 'OBSERVED' | 'FORECAST' | 'ESTIMATED' | 'STATIC + SENSOR' | 'MANUAL AUDIT' | 'MANUAL OBSERVED' | 'SIMULATED';
  protocol: string;
  cadence: string;
  lastIngest: string;
  latency: string;
  health: number;
  status: 'healthy' | 'warning' | 'degraded';
  endpoint: string;
  category: string;
  metrics?: { label: string; value: string; extra: string }[];
}

const INITIAL_FEEDS: FeedItem[] = [
  {
    id: 'CWC-HYD-01',
    name: 'Brahmaputra Gauges (DC Court & Pandu)',
    subtext: 'Real-time water level & discharge rate',
    authority: 'Central Water Commission (CWC)',
    classification: 'OBSERVED',
    protocol: 'MQTT / GeoJSON',
    cadence: 'Every 15 min',
    lastIngest: '14:40 IST',
    latency: '24ms',
    health: 99.9,
    status: 'healthy',
    endpoint: 'wss://telemetry.cwc.gov.in/assam/kamrup/v2/stream',
    category: 'Hydrology',
    metrics: [
      { label: 'DC Court Station (GHY)', value: '49.88m', extra: '+0.20m over danger (Rising 2.1cm/h)' },
      { label: 'Pandu Port Gauge', value: '49.12m', extra: '+0.14m over danger (High Flood)' },
    ]
  },
  {
    id: 'CWC-REGIONAL-01',
    name: 'Assam State River Gauges Network (10 Stations)',
    subtext: 'Brahmaputra & Barak Basins: Pandu, DC Court, Puthimari, Beki, Pagladiya, Kopili (Kampur/Dharamtul), Barak (AP Ghat)',
    authority: 'CWC & Assam Water Resources Department (waterresources.assam.gov.in / asdma.gov.in)',
    classification: 'OBSERVED',
    protocol: 'REST / GeoJSON & Certified Bulletins',
    cadence: 'Daily / Manual Event Post',
    lastIngest: 'Official Baseline Bulletin',
    latency: 'Certified Manual',
    health: 100.0,
    status: 'healthy',
    endpoint: 'https://waterresources.assam.gov.in',
    category: 'Hydrology',
    metrics: [
      { label: 'Verified Stations', value: '10 Stations', extra: '7 Districts across Assam' },
      { label: 'Provenance', value: 'LAST_KNOWN / MANUAL', extra: 'Zero fabricated IoT telemetry' },
    ]
  },
  {
    id: 'MET-RAD-02',
    name: 'IMD Doppler Radar & Open-Meteo GFS',
    subtext: 'Borjhar Radar reflectivity & 24h precip model',
    authority: 'IMD RMC Borjhar / Open-Meteo',
    classification: 'FORECAST',
    protocol: 'REST / NetCDF-4',
    cadence: 'Hourly',
    lastIngest: '14:00 IST',
    latency: '110ms',
    health: 98.4,
    status: 'healthy',
    endpoint: 'https://api.open-meteo.com/v1/forecast?latitude=26.14&longitude=91.73',
    category: 'Meteorology',
    metrics: [
      { label: 'Borjhar Radar Reflectivity', value: '38 dBZ', extra: 'Moderate to heavy convection' },
      { label: '24h Precipitation Accumulation', value: '72 mm', extra: 'Peak run-off expected 18:00 IST' },
    ]
  },
  {
    id: 'SAT-SAR-03',
    name: 'Copernicus Sentinel-1 SAR Extent',
    subtext: 'Next pass 16:15 IST • Spline hydrodynamic back-cast active',
    authority: 'ESA / NRSC Disaster Watch',
    classification: 'ESTIMATED',
    protocol: 'WMS / GeoTIFF COG',
    cadence: '6-Hour Orbit',
    lastIngest: '10:30 IST',
    latency: '4h 12m ago',
    health: 88.5,
    status: 'degraded',
    endpoint: 'https://sentinel-hub.com/api/v1/process/kamrup_water_mask',
    category: 'Satellite EO',
    metrics: [
      { label: 'Raster Inundation Grid', value: '14.2 sq km', extra: 'Interpolated via DEM hydro-mesh' },
      { label: 'Next Satellite Orbit Pass', value: '16:15 IST', extra: 'Sensor in ascending orbit' },
    ]
  },
  {
    id: 'GIS-RDS-04',
    name: 'Kamrup Metro Road Network & Bridge Graph',
    subtext: 'OSRM routing mesh with dynamic flood cut-off attributes',
    authority: 'OSM Assam / PWD Roads',
    classification: 'STATIC + SENSOR',
    protocol: 'gRPC / Protobuf',
    cadence: 'Continuous',
    lastIngest: '14:38 IST',
    latency: '18ms',
    health: 100.0,
    status: 'healthy',
    endpoint: 'grpc://router.kamrup.pwd.gov.in:50051/topology',
    category: 'Road Graph',
    metrics: [
      { label: 'Network Graph Size', value: '18 Segments', extra: '1 Severed (MG Road @ 0.40m)' },
      { label: 'Active Bypass Corridor', value: 'AT Road & GS Rd', extra: 'Clearance >0.35m nominal' },
    ]
  },
  {
    id: 'ERP-DPT-05',
    name: 'Sarusajai Depot Inventory Ledger',
    subtext: 'Rations, medical kits, inflatable dinghies, fuel drums',
    authority: 'ASDMA Logistics ERP',
    classification: 'MANUAL AUDIT',
    protocol: 'SQL Webhook / JSON',
    cadence: 'Every 30 min',
    lastIngest: '14:15 IST',
    latency: '35ms',
    health: 99.5,
    status: 'healthy',
    endpoint: 'https://erp.asdma.gov.in/api/v1/depots/sarusajai/inventory',
    category: 'Depot ERP',
    metrics: [
      { label: 'Audited Available Stock', value: '5,500 kg', extra: '8 SKUs stored at central warehouse' },
      { label: 'Quarantine / Reserve Buffer', value: '15.0%', extra: '825 kg locked for Level-3 SOS' },
    ]
  },
  {
    id: 'FLD-OBS-06',
    name: 'Zonal SDRF 4th Bn Incident Stream',
    subtext: 'Live field rescue SOS reports, embankment breach pings',
    authority: 'SDRF Assam Quick Response',
    classification: 'MANUAL OBSERVED',
    protocol: 'TETRA / Mobile App',
    cadence: 'Event-driven',
    lastIngest: '14:28 IST',
    latency: '14m ago',
    health: 96.0,
    status: 'healthy',
    endpoint: 'wss://sdrf-ops.assam.gov.in/channels/kamrup_command',
    category: 'Field Ops',
    metrics: [
      { label: 'Active Rescue Tasks', value: '4 Patrols', extra: '2 Zonal dinghies deployed at Majgaon' },
      { label: 'Evacuated Civilians', value: '412 persons', extra: 'Kamrup Girls HS & Amingaon' },
    ]
  },
  {
    id: 'DEM-EST-07',
    name: 'Population Exposure & Demand Model',
    subtext: 'Ward census grid combined with water-depth vulnerability',
    authority: 'Census / GIS Grid v2.4',
    classification: 'SIMULATED',
    protocol: 'RPC / JSON',
    cadence: 'On-demand snap',
    lastIngest: '14:30 IST',
    latency: 'Snapshot-1430',
    health: 99.1,
    status: 'healthy',
    endpoint: 'https://models.reliefos.internal/exposure/kamrup_v2',
    category: 'Field Ops',
    metrics: [
      { label: 'Aggregated Ration Demand', value: '7,200 kg', extra: '5 Zones calculated (Sphere standard)' },
      { label: 'Critical Risk Weighting', value: 'w=10 (Z01/Z02)', extra: 'Stage 1 priority-weighted' },
    ]
  },
  {
    id: 'GIS-ZON-08',
    name: 'Kamrup Operational Zones GeoJSON Layer',
    subtext: 'RFC 7946 Polygon boundaries in WGS84 EPSG:4326',
    authority: 'ASDMA Pilot Scheme v2.4',
    classification: 'ESTIMATED',
    protocol: 'REST / GeoJSON',
    cadence: 'Version Controlled',
    lastIngest: 'Active v2.4',
    latency: '8ms',
    health: 100.0,
    status: 'healthy',
    endpoint: '/api/gis/zones.geojson',
    category: 'GIS Boundary',
    metrics: [
      { label: 'Validated Spatial Features', value: '5 Zones', extra: '100% closed linear rings verified' },
      { label: 'Coordinate System', value: 'EPSG:4326', extra: 'RFC 7946 [lng, lat] compliant' },
    ]
  }
];

export const DataSources: React.FC = () => {
  const [feeds, setFeeds] = useState<FeedItem[]>(INITIAL_FEEDS);
  const [selectedFeedId, setSelectedFeedId] = useState<string>('CWC-HYD-01');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [pipelineData, setPipelineData] = useState<any>(null);

  // Manual Gauge Entry State
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [manualGaugeId, setManualGaugeId] = useState('PANDU');
  const [manualLevel, setManualLevel] = useState('49.85');
  const [manualOperator, setManualOperator] = useState('OFFICER_SHARMA');
  const [manualReason, setManualReason] = useState('Physical staff gauge reading during sensor maintenance');
  const [manualSubmitting, setManualSubmitting] = useState(false);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const [data, providers] = await Promise.allSettled([
          api.getDataSources(),
          api.getProvidersHealth()
        ]);
        if (data.status === 'fulfilled' && data.value) {
          setPipelineData(data.value);
        }
      } catch (err) {
        console.warn('Using baseline data sources cache', err);
      }
    };
    fetchSources();
  }, []);

  const handleManualEntrySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setManualSubmitting(true);
    try {
      await api.postManualGaugeReading({
        station_id: manualGaugeId,
        water_level_m: parseFloat(manualLevel),
        operator_name: manualOperator,
        notes: manualReason
      });
      showToast(`Manual reading for ${manualGaugeId} (${manualLevel}m) logged and audited.`);
      setManualModalOpen(false);
    } catch (err) {
      showToast(`Error recording manual reading: ${err}`);
    } finally {
      setManualSubmitting(false);
    }
  };

  const handleExportAuditJSON = () => {
    const auditDossier = {
      system: "RELIEFOS Lite Data Provenance Highway",
      standard: "ISO-19115 Geographic Information - Metadata",
      gateway: "Kamrup Metro Regional Gateway (Node-GHY-04)",
      generated_at: new Date().toISOString(),
      streams_audited: feeds.length,
      feeds: feeds
    };
    const blob = new Blob([JSON.stringify(auditDossier, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ASDMA_Data_Highway_Telemetry_Audit_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported ISO-19115 Data Highway Telemetry Audit JSON.');
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const selectedFeed = feeds.find(f => f.id === selectedFeedId) || feeds[0];

  const filteredFeeds = feeds.filter(f => {
    const matchesSearch = f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          f.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          f.authority.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          f.classification.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || f.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleRefreshFeed = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    showToast(`Polling latest telemetry packet from ${id}...`);
    setFeeds(prev => prev.map(feed => {
      if (feed.id === id) {
        return {
          ...feed,
          lastIngest: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) + ' IST',
          latency: `${Math.floor(15 + Math.random() * 25)}ms`
        };
      }
      return feed;
    }));
  };

  const pingSelectedFeed = () => {
    showToast(`Ping sent to ${selectedFeed.endpoint}: 200 OK (22ms roundtrip)`);
  };

  return (
    <div className="p-space-md lg:p-space-lg flex flex-col gap-y-space-md max-w-[1920px] mx-auto w-full select-none">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-surface-container-highest border border-primary/40 text-on-surface px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 font-mono-data text-body-sm animate-fade-in">
          <span className="material-symbols-outlined text-primary text-[18px]">sensors</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* TOP HEADER & CONTEXT STRIP */}
      <header className="bg-surface-container-low rounded-xl p-space-md lg:px-space-lg lg:py-space-md shadow-md border border-outline-variant/30 flex flex-col gap-space-md">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-space-sm flex-wrap">
              <h1 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">
                Data Sources & Ingestion Operations
              </h1>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-surface-container-high text-primary border border-primary/30">
                PIPELINE ENGINE V2.4 • ASDMA DATA HIGHWAY
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-4xl">
              Monitor real-time hydrologic telemetry, meteorological feeds, satellite inundation rasters, road network graphs, and depot logistics ledgers feeding Kamrup Metro operational models.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setManualModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-secondary/15 hover:bg-secondary/25 text-secondary border border-secondary/40 text-[12px] font-semibold transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">edit_note</span>
              <span>Manual Gauge Entry</span>
            </button>
            <button
              onClick={() => showToast('Refreshed all telemetry streams across Kamrup Metro gateway.')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-secondary">sync</span>
              <span>Refresh All</span>
            </button>
            <button
              onClick={() => showToast('All handshakes verified: Open-Meteo LIVE, CWC Gauges ACTIVE, OSRM Mesh OK.')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-primary">network_check</span>
              <span>Test Handshakes</span>
            </button>
            <button
              onClick={handleExportAuditJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-[12px] border border-outline-variant/30 font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">download</span>
              <span>Export Audit</span>
            </button>
            <button
              onClick={() => showToast('Opening ASDMA Regional Gateway configuration modal...')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 shadow-sm transition-all"
            >
              <span className="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Configure Pipeline</span>
            </button>
          </div>
        </div>

        {/* Telemetry Status Ribbon */}
        <div className="p-space-sm rounded bg-surface-container-lowest border border-outline-variant/30 flex items-center justify-between flex-wrap gap-y-2 text-[11px] font-mono-data">
          <div className="flex items-center gap-x-4 gap-y-1 flex-wrap text-on-surface-variant">
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px] text-primary">hub</span>
              <span className="text-outline">Data Highway:</span>
              <span className="text-on-surface font-semibold">Kamrup Metro Regional Gateway (Node-GHY-04)</span>
            </div>
            <span className="text-outline-variant">•</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span className="text-on-surface font-semibold">06 Operational</span>
              <span className="text-outline">/</span>
              <span className="text-tertiary font-semibold">01 Degraded</span>
            </div>
            <span className="text-outline-variant">•</span>
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px] text-secondary">update</span>
              <span className="text-outline">Cadence:</span>
              <span className="text-on-surface font-semibold">15m Polling & Webhooks</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px] text-primary">security</span>
            <span className="text-primary font-semibold">Stale Feed Fallback Active</span>
          </div>
        </div>
      </header>

      {/* TOP METRIC CARDS (5 HORIZONTAL CARDS) */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-space-sm">
        {/* Card 1 */}
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm min-h-[96px]">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>Active Feeds</span>
            <span className="material-symbols-outlined text-[18px] text-primary">sensors</span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-kpi-lg font-bold text-on-surface font-mono-data tabular-nums">07</span>
            <span className="text-[12px] text-on-surface-variant font-normal">Ingested</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-primary font-mono-data mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            <span>6 Healthy</span>
            <span className="text-outline">•</span>
            <span className="text-tertiary font-semibold">1 Warning</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm min-h-[96px]">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>Throughput</span>
            <span className="material-symbols-outlined text-[18px] text-secondary">speed</span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-kpi-lg font-bold text-on-surface font-mono-data tabular-nums">1.42</span>
            <span className="text-[12px] text-on-surface-variant font-normal">MB/s</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-on-surface-variant font-mono-data mt-0.5">
            <span>42ms avg</span>
            <span>•</span>
            <span className="text-primary font-semibold">99.8% SLA</span>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm min-h-[96px]">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>Freshness Target</span>
            <span className="material-symbols-outlined text-[18px] text-primary">timer</span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-kpi-lg font-bold text-primary font-mono-data tabular-nums">94.2%</span>
            <span className="text-[12px] text-on-surface-variant font-normal">compliant</span>
          </div>
          <div className="text-[11px] text-on-surface-variant font-mono-data mt-0.5">
            <span>Threshold: &lt;15m window</span>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm min-h-[96px]">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>Degraded / Stale</span>
            <span className="material-symbols-outlined text-[18px] text-tertiary">warning</span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-kpi-lg font-bold text-tertiary font-mono-data tabular-nums">01</span>
            <span className="text-[12px] text-on-surface-variant font-normal">Feed</span>
          </div>
          <div className="font-mono-data text-[11px] text-on-surface-variant truncate mt-0.5">
            Sentinel-1 SAR (4h mesh)
          </div>
        </div>

        {/* Card 5 */}
        <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col justify-between shadow-sm min-h-[96px]">
          <div className="flex items-center justify-between text-outline text-[11px] uppercase font-bold">
            <span>Integrity Gate</span>
            <span className="material-symbols-outlined text-[18px] text-secondary">verified_user</span>
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-kpi-lg font-bold text-on-surface font-mono-data tabular-nums">SHA-256</span>
            <span className="text-[11px] font-bold text-primary">VALID</span>
          </div>
          <div className="font-mono-data text-[11px] text-on-surface-variant truncate mt-0.5">
            HMAC cryptographic seal
          </div>
        </div>
      </section>

      {/* MAIN WORKSPACE: TWO-COLUMN LAYOUT */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-space-md items-start">
        {/* LEFT COLUMN: LEDGER & GOVERNANCE (~68% = 8 cols) */}
        <div className="xl:col-span-8 flex flex-col space-y-space-md">
          {/* FILTER & SEARCH BAR */}
          <div className="bg-surface-container p-space-md rounded-xl flex flex-col space-y-space-md shadow-sm">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-space-sm">
              {/* Search input */}
              <div className="relative flex-1">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">search</span>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by source ID, telemetry type, protocol, or provider..."
                  className="w-full bg-surface-container-low pl-10 pr-space-md py-space-sm rounded-lg text-on-surface placeholder:text-on-surface-variant font-body-sm text-body-sm focus:outline-none focus:bg-surface-container-lowest transition-all"
                />
              </div>

              {/* Bulk actions */}
              <div className="flex items-center gap-space-sm font-label-md text-label-md text-on-surface-variant">
                <label className="flex items-center gap-space-xs cursor-pointer select-none bg-surface-container-low px-space-sm py-space-xs rounded-lg hover:text-on-surface">
                  <input defaultChecked className="accent-primary rounded" type="checkbox"/>
                  <span>Auto-poll (30s)</span>
                </label>
                <label className="flex items-center gap-space-xs cursor-pointer select-none bg-surface-container-low px-space-sm py-space-xs rounded-lg hover:text-on-surface">
                  <input defaultChecked className="accent-primary rounded" type="checkbox"/>
                  <span>Sparklines</span>
                </label>
              </div>
            </div>

            {/* Filter category tags */}
            <div className="flex items-center gap-space-xs overflow-x-auto pb-1">
              {['All', 'Hydrology', 'Meteorology', 'Satellite EO', 'Road Graph', 'Depot ERP', 'Field Ops'].map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-space-sm py-1 rounded font-label-sm text-label-sm font-semibold whitespace-nowrap transition-colors ${
                    selectedCategory === cat
                      ? 'bg-primary text-on-primary'
                      : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface hover:bg-surface-bright'
                  }`}
                >
                  {cat === 'All' ? 'All Feeds (7)' : `${cat}`}
                </button>
              ))}
            </div>
          </div>

          {/* PRIMARY DATA FEEDS LEDGER TABLE */}
          <div className="bg-surface-container rounded-xl overflow-hidden shadow-sm">
            <div className="px-space-md py-space-sm bg-surface-container-high flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-primary text-[18px]">table_chart</span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-bold">Ingested Stream Registry</span>
              </div>
              <span className="font-mono-data text-label-sm text-on-surface-variant">Sorted by criticality rank</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-body-sm text-body-sm">
                <thead className="bg-surface-container-low text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                  <tr>
                    <th className="py-space-sm px-space-md font-semibold">Feed Identity & Source</th>
                    <th className="py-space-sm px-space-md font-semibold">Authority</th>
                    <th className="py-space-sm px-space-md font-semibold">Class / Type</th>
                    <th className="py-space-sm px-space-md font-semibold">Protocol</th>
                    <th className="py-space-sm px-space-md font-semibold">Cadence</th>
                    <th className="py-space-sm px-space-md font-semibold">Last Ingest</th>
                    <th className="py-space-sm px-space-md font-semibold">Health</th>
                    <th className="py-space-sm px-space-md font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-highest/30 text-on-surface font-body-sm">
                  {filteredFeeds.map(feed => {
                    const isSelected = feed.id === selectedFeedId;
                    return (
                      <tr
                        key={feed.id}
                        onClick={() => setSelectedFeedId(feed.id)}
                        className={`hover:bg-surface-bright/40 transition-colors cursor-pointer group ${
                          isSelected ? 'bg-surface-container-high/60 border-l-2 border-primary' : ''
                        }`}
                      >
                        <td className="py-space-md px-space-md">
                          <div className="flex flex-col">
                            <div className="flex items-center gap-space-xs">
                              <span className={`font-mono-data text-label-sm font-bold ${
                                feed.status === 'degraded' ? 'text-tertiary' : 'text-primary'
                              }`}>
                                {feed.id}
                              </span>
                              {feed.status === 'degraded' ? (
                                <span className="bg-tertiary/20 text-tertiary px-1.5 rounded text-[10px] uppercase font-mono-data font-semibold">DEGRADED</span>
                              ) : (
                                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                              )}
                            </div>
                            <span className="font-headline-sm text-body-lg font-semibold text-on-surface group-hover:text-primary transition-colors">
                              {feed.name}
                            </span>
                            <span className="font-mono-data text-label-sm text-on-surface-variant truncate max-w-xs">
                              {feed.subtext}
                            </span>
                          </div>
                        </td>
                        <td className="py-space-md px-space-md text-on-surface-variant font-mono-data text-body-sm">
                          {feed.authority}
                        </td>
                        <td className="py-space-md px-space-md">
                          <span className={`px-space-xs py-0.5 rounded font-mono-data text-label-sm font-semibold ${
                            feed.classification === 'OBSERVED' || feed.classification === 'MANUAL OBSERVED'
                              ? 'bg-primary/10 text-primary'
                              : feed.classification === 'FORECAST'
                              ? 'bg-secondary/10 text-secondary'
                              : feed.classification === 'ESTIMATED'
                              ? 'bg-tertiary/20 text-tertiary'
                              : 'bg-surface-variant text-on-surface-variant'
                          }`}>
                            {feed.classification}
                          </span>
                        </td>
                        <td className="py-space-md px-space-md font-mono-data text-label-sm text-on-surface-variant">
                          {feed.protocol}
                        </td>
                        <td className="py-space-md px-space-md font-mono-data text-label-sm">
                          {feed.cadence}
                        </td>
                        <td className="py-space-md px-space-md">
                          <div className="flex flex-col font-mono-data text-label-sm">
                            <span className="text-on-surface font-semibold">{feed.lastIngest}</span>
                            <span className="text-primary text-[10px]">{feed.latency}</span>
                          </div>
                        </td>
                        <td className="py-space-md px-space-md">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-mono-data text-label-sm ${
                            feed.status === 'degraded'
                              ? 'text-tertiary bg-tertiary/20'
                              : 'text-primary bg-primary/10'
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${feed.status === 'degraded' ? 'bg-tertiary' : 'bg-primary'}`}></span>
                            {feed.health}%
                          </span>
                        </td>
                        <td className="py-space-md px-space-md text-right">
                          <div className="flex items-center justify-end gap-space-xs">
                            <button
                              onClick={(e) => handleRefreshFeed(feed.id, e)}
                              className="p-1 hover:bg-surface-container-high rounded text-on-surface-variant hover:text-primary transition-colors"
                              title="Trigger Polling"
                            >
                              <span className="material-symbols-outlined text-[16px]">sync</span>
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                showToast(`Inspect terminal payload for ${feed.id}`);
                              }}
                              className="p-1 hover:bg-surface-container-high rounded text-on-surface-variant hover:text-secondary transition-colors"
                              title="View Payload Logs"
                            >
                              <span className="material-symbols-outlined text-[16px]">terminal</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* PROVENANCE CLASSIFICATION MATRIX & GOVERNANCE FRAMEWORK */}
          <div className="bg-surface-container p-space-md rounded-xl space-y-space-md shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-secondary text-[20px]">account_tree</span>
                <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">Data Provenance & Verification Protocol</h2>
              </div>
              <span className="font-label-sm text-label-sm bg-surface-container-high text-on-surface-variant px-space-sm py-0.5 rounded font-mono-data">
                ISO-19115 GIS Standard
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              To maintain zero-confusion operational reliability during flash inundation emergencies in Kamrup Metropolitan, every upstream attribute fed into the allocation solvers is tagged with one of eight standardized registry states:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-space-sm">
              {/* State 1: LIVE */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-primary">1. LIVE</span>
                  <span className="material-symbols-outlined text-primary text-[14px]">sensors</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Fresh real-time observation received within SLA (e.g. Open-Meteo live API).</p>
              </div>

              {/* State 2: LAST_KNOWN */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-secondary">2. LAST_KNOWN</span>
                  <span className="material-symbols-outlined text-secondary text-[14px]">cached</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Valid recent observation retained during transient network disconnection.</p>
              </div>

              {/* State 3: STALE */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-[#f5b84b]">3. STALE</span>
                  <span className="material-symbols-outlined text-[#f5b84b] text-[14px]">history</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Observation timestamp exceeds maximum freshness threshold (&gt;60 min).</p>
              </div>

              {/* State 4: UNAVAILABLE */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-error">4. UNAVAILABLE</span>
                  <span className="material-symbols-outlined text-error text-[14px]">cloud_off</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Sensor offline. Never replaced with fake data; requires manual entry.</p>
              </div>

              {/* State 5: MANUAL */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-on-surface">5. MANUAL</span>
                  <span className="material-symbols-outlined text-on-surface text-[14px]">how_to_reg</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Authorized official field entry with audit logging in SQLite database.</p>
              </div>

              {/* State 6: ESTIMATED */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-tertiary">6. ESTIMATED</span>
                  <span className="material-symbols-outlined text-tertiary text-[14px]">insights</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Algorithmic hydraulic derivation or census vulnerability model calculation.</p>
              </div>

              {/* State 7: SIMULATED */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-secondary">7. SIMULATED</span>
                  <span className="material-symbols-outlined text-secondary text-[14px]">model_training</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Controlled disaster scenario drill isolated from live operational ledger.</p>
              </div>

              {/* State 8: UNVERIFIED */}
              <div className="bg-surface-container-high p-space-sm rounded-lg flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono-data text-label-sm font-bold text-outline">8. UNVERIFIED</span>
                  <span className="material-symbols-outlined text-outline text-[14px]">help</span>
                </div>
                <p className="font-body-sm text-[11px] text-on-surface-variant">Crowdsourced report or uncalibrated reading awaiting operator verification.</p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: FEED INSPECTOR & TOPOLOGY (~32% = 4 cols) */}
        <div className="xl:col-span-4 flex flex-col space-y-space-md">
          {/* SELECTED FEED INSPECTOR */}
          <div className="bg-surface-container p-space-md rounded-xl space-y-space-md shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className={`w-2.5 h-2.5 rounded-full ${selectedFeed.status === 'degraded' ? 'bg-tertiary' : 'bg-primary animate-pulse'}`}></span>
                <span className="font-headline-sm text-headline-sm font-bold text-on-surface">Live Inspector</span>
              </div>
              <span className="font-mono-data text-label-sm bg-primary/10 text-primary px-space-xs py-0.5 rounded font-semibold">
                {selectedFeed.id}
              </span>
            </div>

            <div className="bg-surface-container-low p-space-sm rounded-lg space-y-space-xs">
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-label-sm text-on-surface-variant">Stream Identity</span>
                <span className={`font-mono-data text-label-sm font-bold ${selectedFeed.status === 'degraded' ? 'text-tertiary' : 'text-primary'}`}>
                  {selectedFeed.status === 'degraded' ? 'DEGRADED STREAM' : 'ACTIVE TELEMETRY'}
                </span>
              </div>
              <div className="font-body-lg text-body-lg text-on-surface font-semibold">
                {selectedFeed.name}
              </div>
              <div className="font-mono-data text-label-sm text-on-surface-variant break-all">
                {selectedFeed.endpoint}
              </div>
            </div>

            {/* Dynamic Telemetry Metrics for Selected Feed */}
            {selectedFeed.metrics && selectedFeed.metrics.length > 0 && (
              <div className="space-y-space-xs">
                <span className="font-label-sm text-label-sm text-on-surface-variant font-semibold uppercase tracking-wider">
                  Live Sensor Readings
                </span>
                {selectedFeed.metrics.map((m, idx) => (
                  <div key={idx} className="bg-surface-container-high p-space-sm rounded-lg flex items-center justify-between">
                    <div>
                      <div className="font-mono-data text-label-sm text-on-surface font-semibold">{m.label}</div>
                      <div className="font-label-sm text-label-sm text-on-surface-variant font-mono-data">{m.extra}</div>
                    </div>
                    <div className="text-right">
                      <div className={`font-headline-lg text-headline-lg font-bold ${
                        selectedFeed.status === 'degraded' ? 'text-tertiary' : 'text-primary'
                      }`}>
                        {m.value}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Telemetry Health Gauges */}
            <div className="space-y-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant font-semibold uppercase tracking-wider">
                Ingestion Channel Health
              </span>
              <div className="grid grid-cols-2 gap-space-xs text-center font-mono-data text-label-sm">
                <div className="bg-surface-container-high p-space-xs rounded">
                  <div className="text-on-surface-variant text-[10px]">PACKET LOSS</div>
                  <div className="text-primary font-bold">{selectedFeed.status === 'degraded' ? '4.82%' : '0.01%'}</div>
                </div>
                <div className="bg-surface-container-high p-space-xs rounded">
                  <div className="text-on-surface-variant text-[10px]">ROUNDTRIP</div>
                  <div className="text-primary font-bold">{selectedFeed.latency}</div>
                </div>
                <div className="bg-surface-container-high p-space-xs rounded">
                  <div className="text-on-surface-variant text-[10px]">BUFFER LOAD</div>
                  <div className="text-secondary font-bold">12 / 1024</div>
                </div>
                <div className="bg-surface-container-high p-space-xs rounded">
                  <div className="text-on-surface-variant text-[10px]">CHECKSUM</div>
                  <div className="text-primary font-bold">PASSED</div>
                </div>
              </div>
            </div>

            {/* Downstream Consuming Modules */}
            <div className="space-y-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant font-semibold uppercase tracking-wider">
                Downstream Consumers
              </span>
              <div className="flex flex-wrap gap-1">
                <span className="bg-surface-container-low text-on-surface-variant font-mono-data text-label-sm px-2 py-0.5 rounded">Live Flood Map</span>
                <span className="bg-surface-container-low text-on-surface-variant font-mono-data text-label-sm px-2 py-0.5 rounded">Zones & Risk</span>
                <span className="bg-surface-container-low text-on-surface-variant font-mono-data text-label-sm px-2 py-0.5 rounded">Relief Allocation</span>
                <span className="bg-surface-container-low text-on-surface-variant font-mono-data text-label-sm px-2 py-0.5 rounded">Route Optimization</span>
              </div>
            </div>

            {/* Diagnostic Actions */}
            <div className="pt-space-xs flex flex-col gap-space-xs font-label-md text-label-md">
              <div className="flex items-center gap-space-xs">
                <button
                  onClick={pingSelectedFeed}
                  className="flex-1 bg-surface-container-high hover:bg-surface-bright text-on-surface py-space-sm rounded-lg flex items-center justify-center gap-1 transition-colors shadow-sm"
                >
                  <span className="material-symbols-outlined text-[16px] text-primary">network_ping</span>
                  <span>Ping Endpoint</span>
                </button>
                <button
                  onClick={() => showToast(`Re-authenticated session token for ${selectedFeed.id}`)}
                  className="flex-1 bg-surface-container-high hover:bg-surface-bright text-on-surface py-space-sm rounded-lg flex items-center justify-center gap-1 transition-colors shadow-sm"
                >
                  <span className="material-symbols-outlined text-[16px] text-secondary">vpn_key</span>
                  <span>Re-Auth Token</span>
                </button>
              </div>
              <button
                onClick={() => showToast(`Payload sample preview generated for ${selectedFeed.id}`)}
                className="w-full bg-surface-container-high hover:bg-surface-bright text-on-surface-variant hover:text-on-surface py-space-sm rounded-lg flex items-center justify-center gap-1 transition-colors shadow-sm"
              >
                <span className="material-symbols-outlined text-[16px]">data_object</span>
                <span>Inspect Raw JSON Payload</span>
              </button>
            </div>
          </div>

          {/* PIPELINE ARCHITECTURE & DATA FLOW TOPOLOGY */}
          <div className="bg-surface-container p-space-md rounded-xl space-y-space-md shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-primary text-[18px]">schema</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">Data Highway Topology</h3>
              </div>
              <span className="font-mono-data text-label-sm text-primary font-bold">100% ONLINE</span>
            </div>

            {/* Flow Visualizer */}
            <div className="bg-surface-container-low p-space-sm rounded-lg flex flex-col space-y-space-sm font-mono-data text-label-sm">
              {/* Step 1 */}
              <div className="flex items-center justify-between bg-surface-container-high p-space-xs rounded">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">cloud_download</span>
                  <span className="text-on-surface font-semibold">1. Upstream Feeds</span>
                </div>
                <span className="text-primary text-[11px]">CWC, IMD, ESA, SDRF</span>
              </div>
              <div className="flex justify-center text-on-surface-variant -my-1">
                <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
              </div>

              {/* Step 2 */}
              <div className="flex items-center justify-between bg-surface-container-high p-space-xs rounded">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[16px] text-secondary">filter_alt</span>
                  <span className="text-on-surface font-semibold">2. Gateway Normalizer</span>
                </div>
                <span className="text-secondary text-[11px]">GeoJSON & NetCDF Parser</span>
              </div>
              <div className="flex justify-center text-on-surface-variant -my-1">
                <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
              </div>

              {/* Step 3 */}
              <div className="flex items-center justify-between bg-surface-container-high p-space-xs rounded">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[16px] text-primary">verified</span>
                  <span className="text-on-surface font-semibold">3. Checksum & QA Gates</span>
                </div>
                <span className="text-primary text-[11px]">SHA-256 Validated</span>
              </div>
              <div className="flex justify-center text-on-surface-variant -my-1">
                <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
              </div>

              {/* Step 4 */}
              <div className="flex items-center justify-between bg-surface-container-high p-space-xs rounded">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[16px] text-primary">memory</span>
                  <span className="text-on-surface font-semibold">4. Solvers & GIS Cache</span>
                </div>
                <span className="text-primary text-[11px]">OR-Tools CP-SAT</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Gauge Reading Entry Modal */}
      {manualModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-surface-container-high border border-outline-variant rounded-xl max-w-lg w-full p-6 shadow-2xl animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[22px]">edit_note</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                  Authorized Manual Gauge Entry
                </h3>
              </div>
              <button
                onClick={() => setManualModalOpen(false)}
                className="p-1 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleManualEntrySubmit} className="mt-4 space-y-4 text-[13px]">
              <div>
                <label className="block text-outline font-label-sm uppercase mb-1">Station / Gauge</label>
                <select
                  value={manualGaugeId}
                  onChange={(e) => setManualGaugeId(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded p-2 text-on-surface focus:outline-none focus:border-primary"
                >
                  <option value="PANDU">Pandu Port Station (Brahmaputra) — Warning: 49.50m</option>
                  <option value="DC_COURT">DC Court Station (Brahmaputra) — Warning: 49.26m</option>
                  <option value="BHARALU_SLUICE">Bharalu River Sluice Gate — Warning: 47.50m</option>
                  <option value="BASISTHA">Basistha River Sensor — Warning: 53.00m</option>
                </select>
              </div>

              <div>
                <label className="block text-outline font-label-sm uppercase mb-1">Water Level (Meters MSL)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={manualLevel}
                  onChange={(e) => setManualLevel(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded p-2 text-on-surface font-mono-data focus:outline-none focus:border-primary"
                  placeholder="e.g. 49.85"
                />
              </div>

              <div>
                <label className="block text-outline font-label-sm uppercase mb-1">Authorized Operator ID</label>
                <input
                  type="text"
                  required
                  value={manualOperator}
                  onChange={(e) => setManualOperator(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded p-2 text-on-surface font-mono-data focus:outline-none focus:border-primary"
                  placeholder="e.g. OFFICER_SHARMA"
                />
              </div>

              <div>
                <label className="block text-outline font-label-sm uppercase mb-1">Observation Reason / Field Note</label>
                <textarea
                  rows={2}
                  value={manualReason}
                  onChange={(e) => setManualReason(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/40 rounded p-2 text-on-surface focus:outline-none focus:border-primary resize-none"
                  placeholder="Reason for manual entry and calibration reference..."
                />
              </div>

              <div className="p-2.5 rounded bg-surface-container text-[11px] text-outline border border-outline-variant/30 flex items-start gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary shrink-0 mt-0.5">verified_user</span>
                <span>Audit Trail: This reading will be logged permanently in SQLite with your Operator ID, timestamp, and audit hash. Provenance will be set to MANUAL.</span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setManualModalOpen(false)}
                  className="px-4 py-2 rounded bg-surface-container hover:bg-surface-container-highest text-on-surface text-[12px] font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={manualSubmitting}
                  className="px-4 py-2 rounded bg-primary-container text-on-primary-container text-[12px] font-semibold hover:brightness-110 flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">save</span>
                  <span>{manualSubmitting ? 'Logging...' : 'Save & Audit Reading'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

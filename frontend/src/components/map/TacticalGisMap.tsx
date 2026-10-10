import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, useMap } from 'react-leaflet';
import { Link } from 'react-router-dom';
import {
  GIS_ZONES,
  GIS_SHELTERS,
  GIS_GAUGES,
  GisGauge,
  GIS_VEHICLES,
  GIS_CHOKEPOINT,
  GIS_ROUTES,
  GisRoute,
  TILE_PROVIDERS,
  createTacticalIcon,
  normalizeToLatLng,
  getGisZonesForLocation,
  getGisSheltersForLocation,
  getGisRoutesForLocation,
  getGisVehiclesForLocation,
  getGisChokepointForLocation
} from './gisLayersData';
import { useLocationContext } from '../../context/LocationContext';

// Map resize helper to eliminate blank/gray tile lag on tab switch, container resize, or sidebar toggle
const MapResizeHandler: React.FC<{ containerRef: React.RefObject<HTMLDivElement | null> }> = ({ containerRef }) => {
  const map = useMap();

  useEffect(() => {
    // Initial invalidation passes to handle mount layout calculations
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 100);
    const t2 = setTimeout(() => map.invalidateSize(), 300);

    const handleWindowResize = () => {
      map.invalidateSize();
    };
    window.addEventListener('resize', handleWindowResize);

    // ResizeObserver on the actual container element to catch sidebar toggle & responsive breakpoint shifts
    let resizeObserver: ResizeObserver | null = null;
    if (containerRef.current && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        map.invalidateSize();
      });
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', handleWindowResize);
      clearTimeout(t1);
      clearTimeout(t2);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, [map, containerRef]);

  return null;
};

// Map view updater for dynamic center, zoom, or bounding-box fitting on route / selection change
const MapViewUpdater: React.FC<{
  center: [number, number];
  zoom: number;
  fitBoundsPositions?: [number, number][];
  selectedVehicle?: string;
}> = ({ center, zoom, fitBoundsPositions, selectedVehicle }) => {
  const map = useMap();
  const prevVehicleRef = useRef<string | undefined>(selectedVehicle);
  const prevCenterRef = useRef<[number, number]>(center);
  const boundsFittedRef = useRef<boolean>(false);

  useEffect(() => {
    // Invalidate size on view change to prevent tile clipping
    map.invalidateSize();

    const centerChanged =
      !prevCenterRef.current ||
      prevCenterRef.current[0] !== center[0] ||
      prevCenterRef.current[1] !== center[1];

    if (centerChanged) {
      prevCenterRef.current = center;
      boundsFittedRef.current = false;
    }

    if (selectedVehicle !== prevVehicleRef.current) {
      prevVehicleRef.current = selectedVehicle;
      boundsFittedRef.current = false;
    }

    if (fitBoundsPositions && fitBoundsPositions.length > 1 && !boundsFittedRef.current) {
      try {
        const bounds = L.latLngBounds(fitBoundsPositions.map((p) => [p[0], p[1]]));
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
          boundsFittedRef.current = true;
          return;
        }
      } catch (err) {
        console.warn('Error fitting bounds:', err);
      }
    }

    if (
      center &&
      Array.isArray(center) &&
      typeof center[0] === 'number' &&
      typeof center[1] === 'number' &&
      !isNaN(center[0]) &&
      !isNaN(center[1])
    ) {
      map.setView(center, zoom, { animate: true });
    }
  }, [map, center[0], center[1], zoom, selectedVehicle, fitBoundsPositions]);

  return null;
};

export interface CustomGisMarker {
  id: string;
  coords: [number, number];
  color: string;
  label: string;
  title: string;
  line1?: string;
  line2?: string;
  badge?: string;
  provenance?: string;
}

export interface TacticalGisMapProps {
  compact?: boolean;
  center?: [number, number];
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  selectedZone?: string;
  onSelectZone?: (zoneCode: string) => void;
  baseMap?: 'dark' | 'osm' | 'topo' | 'satellite';
  onChangeBaseMap?: (bm: 'dark' | 'osm' | 'topo' | 'satellite') => void;
  activeLayers?: {
    floodRiskZones?: boolean;
    riverFlow?: boolean;
    gauges?: boolean;
    roadAccessibility?: boolean;
    shelters?: boolean;
    fleet?: boolean;
  };
  opacity?: number;
  showInspector?: boolean;
  showLegend?: boolean;
  showControls?: boolean;
  showViewFullMapLink?: boolean;
  height?: string | number;
  className?: string;
  gisAuditStatus?: string;
  // Route optimization & inventory enhancements:
  selectedVehicle?: string;
  osrmPolyline?: [number, number][];
  osrmRouteInfo?: {
    distance_km?: number;
    duration_minutes?: number;
    duration_formatted?: string;
    route_name?: string;
  } | null;
  customMarkers?: CustomGisMarker[];
  customRoutes?: GisRoute[];
  fitBoundsPositions?: [number, number][];
  gaugesData?: GisGauge[];
  gaugesFilterDistrict?: string;
}

export const TacticalGisMap: React.FC<TacticalGisMapProps> = ({
  compact = false,
  center,
  zoom,
  minZoom = 8,
  maxZoom = 19,
  selectedZone = '02',
  onSelectZone,
  baseMap: controlledBaseMap,
  onChangeBaseMap,
  activeLayers: controlledActiveLayers,
  opacity = 85,
  showInspector = false,
  showLegend = true,
  showControls = true,
  showViewFullMapLink = false,
  height,
  className = '',
  gisAuditStatus = 'EPSG:4326 VALID',
  selectedVehicle,
  osrmPolyline,
  osrmRouteInfo,
  customMarkers,
  customRoutes,
  fitBoundsPositions,
  gaugesData,
  gaugesFilterDistrict
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [internalBaseMap, setInternalBaseMap] = useState<'dark' | 'osm' | 'topo' | 'satellite'>('dark');
  const [tileError, setTileError] = useState(false);

  const activeBaseMap = controlledBaseMap || internalBaseMap;
  const setBaseMap = (bm: 'dark' | 'osm' | 'topo' | 'satellite') => {
    if (onChangeBaseMap) {
      onChangeBaseMap(bm);
    } else {
      setInternalBaseMap(bm);
    }
  };

  const { selectedLocation } = useLocationContext();

  const layers = {
    floodRiskZones: controlledActiveLayers?.floodRiskZones ?? true,
    riverFlow: controlledActiveLayers?.riverFlow ?? true,
    gauges: controlledActiveLayers?.gauges ?? true,
    roadAccessibility: controlledActiveLayers?.roadAccessibility ?? true,
    shelters: controlledActiveLayers?.shelters ?? true,
    fleet: controlledActiveLayers?.fleet ?? true,
  };

  const allGauges = gaugesData || GIS_GAUGES;
  const effectiveFilter = gaugesFilterDistrict !== undefined
    ? gaugesFilterDistrict
    : (selectedLocation.id === 'kamrup_metro' ? 'ALL' : selectedLocation.districtName);
  const displayGauges = effectiveFilter && effectiveFilter.toUpperCase() !== 'ALL'
    ? allGauges.filter((g) => g.district?.toLowerCase().includes(effectiveFilter.toLowerCase()))
    : allGauges;

  // Center & zoom defaults react to selected operational location from context when not explicitly overridden
  const mapCenter: [number, number] = center || selectedLocation.center || (compact ? [26.162, 91.755] : [26.160, 91.750]);
  const mapZoom = zoom || selectedLocation.zoom || (compact ? 12 : 13);

  // Normalize zone codes (e.g. '01' <-> 'ZONE 01')
  const normalizeZone = (code: string) => code.replace(/[^0-9]/g, '').padStart(2, '0');
  const currentNormZone = normalizeZone(selectedZone);

  const activeZones = getGisZonesForLocation(selectedLocation.id);
  const activeShelters = getGisSheltersForLocation(selectedLocation.id);
  const activeVehicles = getGisVehiclesForLocation(selectedLocation.id);
  const activeRoutes = getGisRoutesForLocation(selectedLocation.id);
  const activeChokepoint = getGisChokepointForLocation(selectedLocation.id);

  const currentZoneObj = activeZones.find((z) => z.numberCode === currentNormZone) || activeZones[0] || GIS_ZONES[0];

  const handleZoneClick = (z: typeof GIS_ZONES[0]) => {
    if (onSelectZone) {
      onSelectZone(z.numberCode);
    }
  };

  const provider = TILE_PROVIDERS[activeBaseMap] || TILE_PROVIDERS.dark;
  const containerHeight = typeof height === 'number' ? `${height}px` : (height || (compact ? '340px' : '100%'));

  // Sanitize OSRM polyline through normalizeToLatLng to guarantee [latitude, longitude] order
  const safeOsrmPolyline = osrmPolyline
    ? osrmPolyline
        .map(normalizeToLatLng)
        .filter((p): p is [number, number] => p !== null)
    : undefined;

  const safeFitBounds = fitBoundsPositions
    ? fitBoundsPositions
        .map(normalizeToLatLng)
        .filter((p): p is [number, number] => p !== null)
    : undefined;

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden bg-[#051423] select-none isolate ${className}`}
      style={{ height: containerHeight, minHeight: containerHeight }}
    >
      {/* Coordinates / Datum Bar (Full Map or when requested) */}
      {!compact && (
        <div className="absolute top-3 left-3 z-[1000] bg-surface-container/90 backdrop-blur px-3 py-1.5 rounded border border-outline-variant/40 flex items-center gap-3 text-[11px] font-mono-data text-on-surface pointer-events-none">
          <span>{mapCenter[0].toFixed(3)}° N, {mapCenter[1].toFixed(3)}° E</span>
          <span className="text-outline">•</span>
          <span>{selectedLocation.displayName.toUpperCase()}</span>
          <span className="text-outline">•</span>
          <span>EPSG:4326</span>
          <span className="text-outline">•</span>
          <span className="text-primary font-semibold">{gisAuditStatus}</span>
        </div>
      )}

      {/* Tile Error Degraded Alert Banner */}
      {tileError && (
        <div className="absolute top-3 left-3 right-3 sm:right-auto z-[1000] bg-surface-container-highest/95 border border-tertiary/60 text-on-surface px-3 py-1.5 rounded-lg shadow-lg flex items-center gap-2 text-[11px] font-mono-data animate-pulse">
          <span className="material-symbols-outlined text-tertiary text-[16px]">warning</span>
          <span>Basemap tiles degraded. Operational GIS vector layers remain fully active.</span>
        </div>
      )}

      {/* Compact View Header Controls (View Full Map Link + Basemap Selector) */}
      {compact && showControls && (
        <div className="absolute top-2.5 right-2.5 z-[1000] flex items-center gap-1.5">
          {/* Quick Basemap Dropdown for compact container */}
          <div className="bg-surface-container/90 backdrop-blur border border-outline-variant/40 rounded px-2 py-1 flex items-center gap-1 text-[11px]">
            <span className="text-outline font-mono-data text-[10px]">MAP:</span>
            <select
              value={activeBaseMap}
              onChange={(e) => setBaseMap(e.target.value as any)}
              className="bg-transparent text-primary font-bold focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="dark" className="bg-surface-container-low text-on-surface">Tactical Dark</option>
              <option value="osm" className="bg-surface-container-low text-on-surface">OSM Standard</option>
              <option value="topo" className="bg-surface-container-low text-on-surface">OpenTopoMap</option>
              <option value="satellite" className="bg-surface-container-low text-on-surface">Satellite</option>
            </select>
          </div>

          {/* Open Full GIS Map Navigation Link */}
          {(showViewFullMapLink || compact) && (
            <Link
              to="/flood-map"
              className="bg-primary/20 hover:bg-primary/30 text-primary px-2.5 py-1 rounded text-[11px] font-semibold border border-primary/40 flex items-center gap-1 transition-all shadow-sm backdrop-blur"
              title="Open full interactive GIS console with advanced layer controls"
            >
              <span>View Full Map</span>
              <span className="material-symbols-outlined text-[14px]">open_in_new</span>
            </Link>
          )}
        </div>
      )}

      {/* OSRM Route Active Indicator Overlay */}
      {safeOsrmPolyline && safeOsrmPolyline.length > 1 && (
        <div className="absolute top-2.5 left-2.5 z-[1000] bg-surface-container/90 backdrop-blur px-2.5 py-1 rounded border border-[#00e5ff]/50 flex items-center gap-1.5 text-[10px] font-mono-data text-[#00e5ff] shadow-md pointer-events-none">
          <span className="w-2 h-2 rounded-full bg-[#00e5ff] animate-pulse"></span>
          <span>OSRM LIVE ROAD POLYLINE ACTIVE</span>
        </div>
      )}

      {/* Main Leaflet Map Instance */}
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        minZoom={minZoom}
        maxZoom={maxZoom}
        scrollWheelZoom={!compact} // Disable scrollWheelZoom on compact overview to prevent trapping user page scrolling
        className="w-full h-full"
        style={{ height: '100%', width: '100%', background: '#051423' }}
      >
        <MapResizeHandler containerRef={containerRef} />
        <MapViewUpdater
          center={mapCenter}
          zoom={mapZoom}
          fitBoundsPositions={
            safeFitBounds || (safeOsrmPolyline && safeOsrmPolyline.length > 1 ? safeOsrmPolyline : undefined)
          }
          selectedVehicle={selectedVehicle}
        />
        
        <TileLayer
          key={activeBaseMap}
          className={provider.className}
          attribution={provider.attribution}
          url={provider.url}
          maxZoom={maxZoom}
          minZoom={minZoom}
          maxNativeZoom={provider.maxNativeZoom || 18}
          eventHandlers={{
            tileerror: () => setTileError(true),
            tileload: () => setTileError(false)
          }}
        />

        {/* 1. Flood Risk Zone Polygons */}
        {layers.floodRiskZones &&
          activeZones.map((zone) => {
            const isSelected = zone.numberCode === currentNormZone;
            return (
              <Polygon
                key={zone.code}
                positions={zone.coords}
                pathOptions={{
                  color: zone.color,
                  fillColor: zone.color,
                  fillOpacity: (opacity / 100) * 0.35,
                  weight: isSelected ? 3.5 : 1.8
                }}
                eventHandlers={{
                  click: () => handleZoneClick(zone)
                }}
              >
                <Popup>
                  <div className="text-[12px] p-1 font-sans">
                    <span className="font-bold text-primary block">{zone.code}: {zone.name}</span>
                    <span className="text-[11px] text-tertiary block font-bold">Risk Tier: {zone.risk}</span>
                    <span className="text-[11px] text-on-surface-variant block">Avg Depth: {zone.depth} • Pop: {zone.pop}</span>
                    <span className="text-[11px] text-outline block">Road Access: {zone.road}</span>
                    <span className="text-[10px] text-outline font-mono-data block mt-1 pt-1 border-t border-outline-variant/30">
                      CLASSIFICATION: {zone.classification}
                    </span>
                  </div>
                </Popup>
              </Polygon>
            );
          })}

        {/* 1B. Official District Boundary Envelope for Monitored Districts if no active microzones */}
        {activeZones.length === 0 && selectedLocation.bounds && (
          <Polygon
            positions={[
              [selectedLocation.bounds[0][0], selectedLocation.bounds[0][1]],
              [selectedLocation.bounds[0][0], selectedLocation.bounds[1][1]],
              [selectedLocation.bounds[1][0], selectedLocation.bounds[1][1]],
              [selectedLocation.bounds[1][0], selectedLocation.bounds[0][1]],
            ]}
            pathOptions={{
              color: '#38bdf8',
              weight: 2,
              dashArray: '6, 6',
              fillColor: '#38bdf8',
              fillOpacity: 0.06,
            }}
          >
            <Popup>
              <div className="p-1 font-sans text-[12px]">
                <div className="font-bold text-sky-400 text-xs uppercase tracking-wider">{selectedLocation.displayName}</div>
                <div className="text-[11px] text-on-surface mt-1">Official ASDMA Administrative Boundary Envelope</div>
                <div className="text-[10px] text-amber-300 font-mono-data mt-1">STATUS: {selectedLocation.tierBadgeText}</div>
                <div className="text-[10px] text-outline mt-0.5">Micro-zone survey in progress. Base telemetry active.</div>
              </div>
            </Popup>
          </Polygon>
        )}

        {/* 2. Central Depot & Verified Shelters */}
        {layers.shelters &&
          activeShelters.map((s) => (
            <Marker key={s.id} position={s.coords} icon={createTacticalIcon(s.color, s.label)}>
              <Popup>
                <div className="p-1 text-[12px]">
                  <span className="font-bold text-primary block">{s.details.title}</span>
                  <span className="text-[11px] text-on-surface block">{s.details.line1}</span>
                  <span className="text-[11px] text-secondary block">{s.details.line2}</span>
                  <span className="text-[10px] text-primary font-mono-data block mt-1 pt-1 border-t border-outline-variant/30">
                    {s.details.provenance}
                  </span>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* 3. CWC & WRD Assam Hydro Stage River Gauges */}
        {layers.gauges &&
          displayGauges.map((g) => {
            const hasReading = g.levelM !== null && g.levelM !== undefined;
            const isDanger = hasReading && g.levelM! >= g.dangerM;
            const isWarning = hasReading && g.warningM && g.levelM! >= g.warningM;
            const markerColor = isDanger ? '#f07171' : isWarning ? '#f5b84b' : hasReading ? '#20bfa5' : '#45bfea';

            return (
              <Marker key={g.id} position={g.coords} icon={createTacticalIcon(markerColor, g.label)}>
                <Popup>
                  <div className="p-1.5 text-[12px] min-w-[220px]">
                    <div className="flex items-center justify-between gap-2 border-b border-outline-variant/30 pb-1 mb-1.5">
                      <span className="font-bold text-on-surface block leading-tight">{g.name}</span>
                      <span className="text-[9px] font-mono-data px-1.5 py-0.5 rounded font-bold uppercase bg-surface-container text-primary border border-primary/30 whitespace-nowrap">
                        {g.district || 'Assam'}
                      </span>
                    </div>

                    <div className="text-[11px] text-on-surface space-y-1">
                      {g.river && (
                        <div className="text-secondary font-medium">River: {g.river}</div>
                      )}
                      {hasReading ? (
                        <div className="font-semibold text-primary">
                          Live Stage: <span className="font-mono-data">{g.levelM!.toFixed(2)} m</span> MSL
                        </div>
                      ) : (
                        <div className="text-[11px] text-outline font-mono-data">
                          Stage Reading: <span className="text-tertiary font-bold">[MANUAL POST • NO IOT]</span>
                        </div>
                      )}
                      <div className="text-on-surface-variant font-mono-data text-[10px] flex items-center gap-2">
                        <span>Danger: {g.dangerM.toFixed(2)}m</span>
                        {g.warningM && <span>Warning: {g.warningM.toFixed(2)}m</span>}
                        {g.hflM && <span>HFL: {g.hflM.toFixed(2)}m</span>}
                      </div>
                      <div className="text-tertiary text-[10px]">
                        Discharge: {g.discharge} • Trend: {g.trend}
                      </div>
                    </div>

                    <div className="mt-2 pt-1 border-t border-outline-variant/30 text-[9px] font-mono-data flex flex-col gap-0.5">
                      <div className="text-primary font-bold">
                        PROVENANCE: {g.provenanceState || 'LAST_KNOWN'} (CERTIFIED BULLETIN)
                      </div>
                      {g.sourceUrl && (
                        <a
                          href={g.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-secondary hover:underline flex items-center gap-1"
                        >
                          <span>Official: {g.sourceUrl.replace('https://', '')}</span>
                          <span className="material-symbols-outlined text-[10px]">open_in_new</span>
                        </a>
                      )}
                      {g.sourceDate && (
                        <span className="text-outline">Bulletin Date: {g.sourceDate}</span>
                      )}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* 4. Fleet Vehicle Markers with Transponder Tags */}
        {layers.fleet &&
          activeVehicles.map((v) => (
            <Marker key={v.id} position={v.coords} icon={createTacticalIcon(v.color, v.label)}>
              <Popup>
                <div className="p-1 text-[12px]">
                  <span className="font-bold text-secondary block">{v.name}</span>
                  <span className="text-[11px] text-on-surface block">{v.details}</span>
                  <span className="text-[10px] text-outline block font-mono-data">STATUS: {v.status}</span>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* 5. Road Accessibility: Chokepoint & Detours */}
        {layers.roadAccessibility && (
          <>
            {activeChokepoint && (
              <Marker position={activeChokepoint.coords} icon={createTacticalIcon(activeChokepoint.color, activeChokepoint.label)}>
                <Popup>
                  <div className="p-1 text-[12px]">
                    <span className="font-bold text-error block">{activeChokepoint.title}</span>
                    <span className="text-[11px] text-tertiary block">{activeChokepoint.desc}</span>
                    <span className="text-[11px] text-primary block">{activeChokepoint.detour}</span>
                  </div>
                </Popup>
              </Marker>
            )}

            {(customRoutes || activeRoutes).map((r) => {
              const isSelectedVehicle = selectedVehicle && r.vehicleCode === selectedVehicle;
              const weight = isSelectedVehicle ? 4.5 : (selectedVehicle ? 2 : r.weight);
              const opacity = isSelectedVehicle ? 1.0 : (selectedVehicle ? 0.35 : r.opacity);
              const color = isSelectedVehicle ? (r.color || '#20bfa5') : (selectedVehicle ? '#6b7280' : r.color);

              return (
                <Polyline
                  key={r.id}
                  positions={r.positions}
                  pathOptions={{
                    color,
                    weight,
                    opacity,
                    dashArray: r.dashArray
                  }}
                >
                  <Popup>
                    <div className="p-1 text-[12px] font-sans">
                      <span className="font-bold text-primary block">{r.name}</span>
                      <span className="text-[11px] text-on-surface block">{r.description}</span>
                      <span className="text-[10px] text-secondary font-mono-data block mt-1 pt-1 border-t border-outline-variant/30">
                        VEHICLE: {r.vehicleCode} • ROUTE: NetworkX Graph Path
                      </span>
                    </div>
                  </Popup>
                </Polyline>
              );
            })}
          </>
        )}

        {/* Real System / OSRM Driving Polyline (High-Visibility Cyan Road Geometry) */}
        {safeOsrmPolyline && safeOsrmPolyline.length > 1 && (
          <Polyline
            positions={safeOsrmPolyline}
            pathOptions={{
              color: '#00e5ff',
              weight: 5,
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round'
            }}
          >
            <Popup>
              <div className="p-1 text-[12px] font-sans">
                <span className="font-bold text-[#00e5ff] block">
                  {osrmRouteInfo?.route_name || 'OSRM Real-World Road Route'}
                </span>
                <span className="text-[11px] text-on-surface block">
                  Distance: {osrmRouteInfo?.distance_km} km • ETA: {osrmRouteInfo?.duration_formatted || `${osrmRouteInfo?.duration_minutes} min`}
                </span>
                <span className="text-[10px] text-secondary font-mono-data block mt-1 pt-1 border-t border-outline-variant/30">
                  ROUTING ENGINE: OpenStreetMap OSRM v5 (Real Road Network)
                </span>
              </div>
            </Popup>
          </Polyline>
        )}

        {/* 6. Custom / Dynamic Markers (Depots, Waypoints, Consignment Drops) */}
        {customMarkers &&
          customMarkers
            .filter((m) => m && Array.isArray(m.coords) && typeof m.coords[0] === 'number' && !isNaN(m.coords[0]) && typeof m.coords[1] === 'number' && !isNaN(m.coords[1]))
            .map((m) => (
              <Marker key={m.id} position={m.coords} icon={createTacticalIcon(m.color, m.label)}>
                <Popup>
                  <div className="p-1 text-[12px] font-sans">
                    <span className="font-bold text-primary block">{m.title}</span>
                    {m.line1 && <span className="text-[11px] text-on-surface block">{m.line1}</span>}
                    {m.line2 && <span className="text-[11px] text-secondary block">{m.line2}</span>}
                    {m.badge && (
                      <span className="text-[10px] font-mono-data font-bold text-tertiary block mt-0.5">
                        {m.badge}
                      </span>
                    )}
                    {m.provenance && (
                      <span className="text-[10px] text-outline font-mono-data block mt-1 pt-1 border-t border-outline-variant/30">
                        {m.provenance}
                      </span>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}
      </MapContainer>

      {/* Interactive Zone Inspector Card (Bottom Left Overlay for compact view) */}
      {compact && showInspector && (
        <div className="absolute bottom-2.5 left-2.5 z-[1000] max-w-xs bg-surface-container-low/95 backdrop-blur-md rounded-lg p-2.5 shadow-xl flex flex-col gap-1 border-l-4 border-outline-variant/30 text-[11px]"
             style={{ borderLeftColor: currentZoneObj.color }}>
          <div className="flex items-center justify-between">
            <span className="font-label-sm font-bold text-on-surface flex items-center gap-1">
              <span className="material-symbols-outlined text-[15px]" style={{ color: currentZoneObj.color }}>crisis_alert</span>
              {currentZoneObj.code}: {currentZoneObj.name}
            </span>
            <span
              className="px-1.5 py-0.5 rounded font-mono-data text-[9px] font-bold"
              style={{ backgroundColor: `${currentZoneObj.color}20`, color: currentZoneObj.color }}
            >
              {currentZoneObj.risk}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 font-mono-data pt-1 border-t border-outline-variant/20">
            <div className="flex flex-col">
              <span className="text-outline text-[9px] uppercase">Surge / Depth</span>
              <span className="text-tertiary font-bold">{currentZoneObj.depth}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-outline text-[9px] uppercase">Road</span>
              <span className="text-on-surface font-semibold truncate">{currentZoneObj.road.split(' ')[0]}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-outline text-[9px] uppercase">Exposed</span>
              <span className="text-on-surface font-bold">{currentZoneObj.pop.replace(' est.', '')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Depth Scale Bar / Legend (Bottom Right Overlay) */}
      {showLegend && (
        <div className="absolute bottom-2.5 right-2.5 z-[1000] bg-surface-container/90 backdrop-blur px-2.5 py-1 rounded border border-outline-variant/40 flex items-center gap-2 text-[10px] font-mono-data pointer-events-none">
          <span className="font-semibold text-outline uppercase hidden sm:inline">Depth:</span>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#27ae80]"></span>
            <span>&lt;0.5m</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#f5b84b]"></span>
            <span>0.5–1.2m</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#f07171]"></span>
            <span>&gt;1.2m</span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * RELIEFOS Lite — Centralized Supported Location Registry
 * Authoritative registry of operational districts across Assam.
 *
 * Operational Tiers:
 * - FULL_OPERATIONAL: Multi-zone tactical flood grid, local depots, shelters, real OSRM road mesh (Kamrup Metropolitan).
 * - CONTINGENCY_OPERATIONAL: Multi-revenue-circle operational sector, local DDMA warehouse, relief shelters, convoy routing, and live CWC hydrology.
 */

export type OperationalTier =
  | 'FULL_OPERATIONAL'
  | 'CONTINGENCY_OPERATIONAL'
  | 'TELEMETRY_MONITORED'
  | 'BASELINE_REFERENCE';

export interface OperationalDatasetFlags {
  zones: boolean;
  sheltersDepots: boolean;
  fleetRoutes: boolean;
  cwcGauges: boolean;
  nwpWeather: boolean;
  demands: boolean;
  roadClosures?: boolean;
  simulations?: boolean;
}

export interface LocationConfig {
  id: string;
  displayName: string;
  shortName: string;
  districtName: string;
  state: string;
  center: [number, number];
  zoom: number;
  bounds: [[number, number], [number, number]];
  operationalTier: OperationalTier;
  tierBadgeText: string;
  dataAvailability: OperationalDatasetFlags;
  description: string;
  stationCount: number;
  primaryRiver: string;
  eocSector: string;
  zoneCount?: number;
  depotName?: string;
  primaryDepot: string;
  revenueCirclesCount: number;
}

export const LOCATIONS_REGISTRY: LocationConfig[] = [
  {
    id: 'kamrup_metro',
    displayName: 'Kamrup Metropolitan, Assam',
    shortName: 'Kamrup Metro',
    districtName: 'Kamrup Metropolitan',
    state: 'Assam',
    center: [26.160, 91.750],
    zoom: 12,
    bounds: [[26.050, 91.600], [26.250, 91.900]],
    operationalTier: 'FULL_OPERATIONAL',
    tierBadgeText: 'FULL EOC GRID',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Primary State EOC Command Grid. 5 tactical flood zones, Sarusajai central staging depot, 2 verified relief shelters, live GPS fleet.',
    stationCount: 4,
    zoneCount: 5,
    revenueCirclesCount: 5,
    depotName: 'Sarusajai Central Relief Depot',
    primaryDepot: 'Sarusajai Central Relief Depot',
    primaryRiver: 'Brahmaputra Mainstem & Bharalu Tributary',
    eocSector: 'Sector Alpha (Central Command)',
  },
  {
    id: 'kamrup_rural',
    displayName: 'Kamrup Rural, Assam',
    shortName: 'Kamrup Rural',
    districtName: 'Kamrup Rural',
    state: 'Assam',
    center: [26.3467, 91.6458],
    zoom: 11,
    bounds: [[25.950, 91.250], [26.650, 91.950]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Northern embankment corridor. 4 Revenue Circles (Hajo, Rangia, Palasbari, Boko), Amingaon Logistics Warehouse, 3 relief shelters, Puthimari CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Amingaon DDMA Logistics Warehouse',
    primaryDepot: 'Amingaon DDMA Logistics Warehouse',
    primaryRiver: 'Puthimari River & Brahmaputra South',
    eocSector: 'Sector Bravo (North Bank)',
  },
  {
    id: 'barpeta',
    displayName: 'Barpeta, Assam',
    shortName: 'Barpeta',
    districtName: 'Barpeta',
    state: 'Assam',
    center: [26.3216, 90.9865],
    zoom: 11,
    bounds: [[26.080, 90.750], [26.600, 91.300]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Lower Brahmaputra valley. 4 Revenue Circles (Barpeta Sadar, Kalgachia, Sarthebari, Mandia), Barpeta DDMA Central Godown, 3 relief camps, Beki CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Barpeta DDMA Central Godown',
    primaryDepot: 'Barpeta DDMA Central Godown',
    primaryRiver: 'Beki River (Manas Tributary)',
    eocSector: 'Sector Charlie (Lower Assam)',
  },
  {
    id: 'nalbari',
    displayName: 'Nalbari, Assam',
    shortName: 'Nalbari',
    districtName: 'Nalbari',
    state: 'Assam',
    center: [26.4494, 91.4600],
    zoom: 11,
    bounds: [[26.200, 91.250], [26.650, 91.650]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Pagladiya river basin. 4 Revenue Circles (Nalbari Sadar, Barkhetri, Borigog, Tihu), Nalbari Relief Godown, 3 shelters, Pagladiya NT Road CWC station.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Nalbari District Relief Godown',
    primaryDepot: 'Nalbari District Relief Godown',
    primaryRiver: 'Pagladiya River',
    eocSector: 'Sector Delta (Central North)',
  },
  {
    id: 'darrang',
    displayName: 'Darrang, Assam',
    shortName: 'Darrang',
    districtName: 'Darrang',
    state: 'Assam',
    center: [26.4350, 92.0350],
    zoom: 11,
    bounds: [[26.150, 91.750], [26.750, 92.350]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Mangaldai sub-basin. 4 Revenue Circles (Mangaldai, Sipajhar, Dalgaon, Patharighat), Mangaldai Relief Godown, 3 shelters, Nonoi & Brahmaputra hydrology.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Mangaldai District Relief Godown',
    primaryDepot: 'Mangaldai District Relief Godown',
    primaryRiver: 'Nonoi River / Brahmaputra',
    eocSector: 'Sector Echo (Middle North)',
  },
  {
    id: 'morigaon',
    displayName: 'Morigaon, Assam',
    shortName: 'Morigaon',
    districtName: 'Morigaon',
    state: 'Assam',
    center: [26.1642, 92.3500],
    zoom: 11,
    bounds: [[26.000, 92.050], [26.450, 92.650]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Kopili-Brahmaputra confluence. 4 Revenue Circles (Morigaon Sadar, Mayong, Bhuragaon, Laharighat), Morigaon Stadium Hub, 3 shelters, Kopili Dharamtul CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Morigaon Stadium Logistics Hub',
    primaryDepot: 'Morigaon Stadium Logistics Hub',
    primaryRiver: 'Kopili River & Brahmaputra',
    eocSector: 'Sector Foxtrot (Middle South)',
  },
  {
    id: 'goalpara',
    displayName: 'Goalpara, Assam',
    shortName: 'Goalpara',
    districtName: 'Goalpara',
    state: 'Assam',
    center: [26.1782, 90.6272],
    zoom: 11,
    bounds: [[25.900, 90.200], [26.350, 90.950]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'South bank lower Brahmaputra. 4 Revenue Circles (Goalpara Sadar, Balijana, Lakhipur, Dudhnoi), Goalpara Central Warehouse, 3 shelters, Goalpara CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Goalpara Town Central Warehouse',
    primaryDepot: 'Goalpara Town Central Warehouse',
    primaryRiver: 'Brahmaputra River Mainstem',
    eocSector: 'Sector Golf (Lower South)',
  },
  {
    id: 'nagaon',
    displayName: 'Nagaon, Assam',
    shortName: 'Nagaon',
    districtName: 'Nagaon',
    state: 'Assam',
    center: [26.1531, 92.6564],
    zoom: 11,
    bounds: [[25.800, 92.300], [26.700, 93.150]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Central Assam flood plain. 4 Revenue Circles (Nagaon Sadar, Kampur, Kaliabor, Raha), Nagaon Polytechnic Godown, 3 shelters, Kopili Kampur CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Nagaon Polytechnic Relief Godown',
    primaryDepot: 'Nagaon Polytechnic Relief Godown',
    primaryRiver: 'Kopili River & Kolong',
    eocSector: 'Sector Hotel (Central East)',
  },
  {
    id: 'cachar',
    displayName: 'Cachar, Assam',
    shortName: 'Cachar',
    districtName: 'Cachar',
    state: 'Assam',
    center: [24.8319, 92.7961],
    zoom: 11,
    bounds: [[24.400, 92.400], [25.150, 93.200]],
    operationalTier: 'CONTINGENCY_OPERATIONAL',
    tierBadgeText: 'DISTRICT EOC',
    dataAvailability: {
      zones: true,
      sheltersDepots: true,
      fleetRoutes: true,
      cwcGauges: true,
      nwpWeather: true,
      demands: true,
      roadClosures: true,
      simulations: true,
    },
    description: 'Barak Valley Southern Basin. 4 Revenue Circles (Silchar Sadar, Katigorah, Lakhipur, Sonai), Silchar DSA Godown, 3 shelters, Barak Annapurna Ghat CWC gauge.',
    stationCount: 1,
    zoneCount: 4,
    revenueCirclesCount: 4,
    depotName: 'Silchar DSA Relief Godown',
    primaryDepot: 'Silchar DSA Relief Godown',
    primaryRiver: 'Barak River Mainstem',
    eocSector: 'Sector India (Barak Valley)',
  },
];

export const DEFAULT_LOCATION: LocationConfig = LOCATIONS_REGISTRY[0];

export const getLocationById = (id: string): LocationConfig => {
  const found = LOCATIONS_REGISTRY.find(
    (loc) => loc.id.toLowerCase() === id.toLowerCase() ||
             loc.districtName.toLowerCase() === id.toLowerCase() ||
             loc.displayName.toLowerCase().includes(id.toLowerCase())
  );
  return found || DEFAULT_LOCATION;
};

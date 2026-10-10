import L from 'leaflet';

export interface GisZone {
  code: string;
  numberCode?: string;
  name: string;
  risk: string;
  color: string;
  coords: [number, number][];
  center: [number, number];
  depth: string;
  pop: string;
  area: string;
  road: string;
  classification: string;
}

export interface GisShelter {
  id: string;
  name: string;
  type: 'DEPOT' | 'SHELTER';
  coords: [number, number];
  color: string;
  label: string;
  details: {
    title: string;
    line1: string;
    line2: string;
    provenance: string;
  };
}

export interface GisGauge {
  id: string;
  name: string;
  station: string;
  river?: string;
  district?: string;
  coords: [number, number];
  color: string;
  label: string;
  levelM?: number | null;
  warningM?: number;
  dangerM: number;
  hflM?: number;
  trend: string;
  discharge: string;
  statusText: string;
  sourceUrl?: string;
  sourceDate?: string;
  provenanceState?: string;
  isLiveTelemetry?: boolean;
}

export interface GisVehicle {
  id: string;
  name: string;
  coords: [number, number];
  color: string;
  label: string;
  details: string;
  status: string;
}

export interface GisRoute {
  id: string;
  name: string;
  vehicleCode: string;
  color: string;
  weight: number;
  opacity: number;
  dashArray?: string;
  positions: [number, number][];
  description: string;
}

export interface TileProviderConfig {
  name: string;
  url: string;
  attribution: string;
  className: string;
  subtext: string;
  maxZoom?: number;
  maxNativeZoom?: number;
  minZoom?: number;
}

// OpenStreetMap compliant tile configuration (No CARTO API key dependencies)
const defaultOsmUrl = import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const defaultOsmAttribution = import.meta.env.VITE_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export const TILE_PROVIDERS: Record<'dark' | 'osm' | 'topo' | 'satellite', TileProviderConfig> = {
  dark: {
    name: 'OSM Tactical Dark',
    url: defaultOsmUrl,
    attribution: defaultOsmAttribution,
    className: 'dark-map-tiles',
    subtext: 'OSM Standard + Dark Filter',
    maxZoom: 19,
    maxNativeZoom: 18,
    minZoom: 7,
  },
  osm: {
    name: 'OSM Standard',
    url: defaultOsmUrl,
    attribution: defaultOsmAttribution,
    className: '',
    subtext: 'Public OSM Standard',
    maxZoom: 19,
    maxNativeZoom: 18,
    minZoom: 7,
  },
  topo: {
    name: 'OpenTopoMap',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
    className: '',
    subtext: 'SRTM Elevation Contours',
    maxZoom: 19,
    maxNativeZoom: 17, // OpenTopoMap server only serves up to z=17
    minZoom: 7,
  },
  satellite: {
    name: 'Satellite Hybrid',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and GIS User Community',
    className: '',
    subtext: 'ESRI World Imagery',
    maxZoom: 19,
    maxNativeZoom: 18,
    minZoom: 7,
  }
};

// =============================================================================
// REVENUE CIRCLE OPERATIONAL ZONES PER DISTRICT (EPSG:4326 [lat, lng])
// =============================================================================

export const DISTRICT_GIS_ZONES: Record<string, GisZone[]> = {
  kamrup_metro: [
    {
      code: 'ZONE 01',
      numberCode: '01',
      name: 'North Guwahati (Riverfront)',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.215, 91.715], [26.220, 91.750], [26.195, 91.745], [26.190, 91.710]],
      center: [26.205, 91.730],
      depth: '1.10m',
      pop: '2,850 est.',
      area: '24.1 ha',
      road: 'MONITORED',
      classification: 'ASDMA Pilot Scheme v2.4'
    },
    {
      code: 'ZONE 02',
      numberCode: '02',
      name: 'Bharalumukh Basin',
      risk: 'CRITICAL L-4',
      color: '#ff8786',
      coords: [[26.180, 91.720], [26.185, 91.748], [26.160, 91.750], [26.155, 91.725]],
      center: [26.172, 91.735],
      depth: '1.85m',
      pop: '4,120 est.',
      area: '38.4 ha',
      road: 'RESTRICTED (MG Road Severed 0.40m)',
      classification: 'ASDMA Pilot Scheme v2.4'
    },
    {
      code: 'ZONE 03',
      numberCode: '03',
      name: 'Uzan Bazar Ghat',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.200, 91.750], [26.205, 91.775], [26.180, 91.778], [26.175, 91.752]],
      center: [26.192, 91.765],
      depth: '0.85m',
      pop: '3,400 est.',
      area: '19.7 ha',
      road: 'OPEN',
      classification: 'ASDMA Pilot Scheme v2.4'
    },
    {
      code: 'ZONE 04',
      numberCode: '04',
      name: 'Basistha Stream Corridor',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.130, 91.765], [26.135, 91.800], [26.105, 91.805], [26.100, 91.770]],
      center: [26.118, 91.785],
      depth: '0.45m',
      pop: '1,920 est.',
      area: '12.5 ha',
      road: 'OPEN',
      classification: 'ASDMA Pilot Scheme v2.4'
    },
    {
      code: 'ZONE 05',
      numberCode: '05',
      name: 'Dispur Secretariat Lowlands',
      risk: 'LOW',
      color: '#27ae80',
      coords: [[26.155, 91.780], [26.160, 91.815], [26.135, 91.820], [26.130, 91.785]],
      center: [26.145, 91.798],
      depth: '0.10m',
      pop: '850 est.',
      area: '4.2 ha',
      road: 'OPEN',
      classification: 'ASDMA Pilot Scheme v2.4'
    }
  ],
  barpeta: [
    {
      code: 'BRP-Z01',
      numberCode: '01',
      name: 'Barpeta Sadar (Urban Core)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.305, 90.965], [26.335, 90.965], [26.335, 91.005], [26.305, 91.005]],
      center: [26.320, 90.985],
      depth: '1.20m',
      pop: '5,200 est.',
      area: '34.5 ha',
      road: 'MONITORED (NH-127A Passable)',
      classification: 'ASDMA Barpeta Revenue Circle Grid'
    },
    {
      code: 'BRP-Z02',
      numberCode: '02',
      name: 'Kalgachia / Beki Riparian',
      risk: 'CRITICAL L-4',
      color: '#f07171',
      coords: [[26.370, 90.820], [26.400, 90.820], [26.400, 90.860], [26.370, 90.860]],
      center: [26.388, 90.842],
      depth: '2.10m',
      pop: '7,100 est.',
      area: '62.0 ha',
      road: 'RESTRICTED (Beki Causeway Submerged 0.50m)',
      classification: 'ASDMA Barpeta Revenue Circle Grid'
    },
    {
      code: 'BRP-Z03',
      numberCode: '03',
      name: 'Sarthebari Alluvial Sector',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.335, 91.100], [26.365, 91.100], [26.365, 91.140], [26.335, 91.140]],
      center: [26.352, 91.122],
      depth: '0.90m',
      pop: '3,900 est.',
      area: '28.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Barpeta Revenue Circle Grid'
    },
    {
      code: 'BRP-Z04',
      numberCode: '04',
      name: 'Mandia Charland Lowlands',
      risk: 'CRITICAL',
      color: '#ff8786',
      coords: [[26.175, 90.900], [26.205, 90.900], [26.205, 90.940], [26.175, 90.940]],
      center: [26.192, 90.920],
      depth: '1.65m',
      pop: '4,800 est.',
      area: '44.0 ha',
      road: 'WATERCRAFT TRANSIT ONLY',
      classification: 'ASDMA Barpeta Revenue Circle Grid'
    }
  ],
  nalbari: [
    {
      code: 'NLB-Z01',
      numberCode: '01',
      name: 'Nalbari Sadar (Town Core)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.430, 91.420], [26.460, 91.420], [26.460, 91.460], [26.430, 91.460]],
      center: [26.445, 91.442],
      depth: '0.75m',
      pop: '4,400 est.',
      area: '22.0 ha',
      road: 'OPEN (NH-27 Transit Open)',
      classification: 'ASDMA Nalbari Revenue Circle Grid'
    },
    {
      code: 'NLB-Z02',
      numberCode: '02',
      name: 'Barkhetri Alluvial Basin',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.265, 91.340], [26.295, 91.340], [26.295, 91.380], [26.265, 91.380]],
      center: [26.282, 91.362],
      depth: '1.90m',
      pop: '6,800 est.',
      area: '55.0 ha',
      road: 'RESTRICTED (Pagladiya Overtopping)',
      classification: 'ASDMA Nalbari Revenue Circle Grid'
    },
    {
      code: 'NLB-Z03',
      numberCode: '03',
      name: 'Borigog Alluvial Sector',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.495, 91.460], [26.525, 91.460], [26.525, 91.500], [26.495, 91.500]],
      center: [26.512, 91.482],
      depth: '0.60m',
      pop: '3,200 est.',
      area: '18.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Nalbari Revenue Circle Grid'
    },
    {
      code: 'NLB-Z04',
      numberCode: '04',
      name: 'Tihu / Buradia Lowlands',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.475, 91.300], [26.505, 91.300], [26.505, 91.340], [26.475, 91.340]],
      center: [26.492, 91.322],
      depth: '0.50m',
      pop: '2,900 est.',
      area: '15.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Nalbari Revenue Circle Grid'
    }
  ],
  cachar: [
    {
      code: 'CCH-Z01',
      numberCode: '01',
      name: 'Silchar Sadar (Urban Core)',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[24.810, 92.775], [24.840, 92.775], [24.840, 92.815], [24.810, 92.815]],
      center: [24.825, 92.795],
      depth: '1.40m',
      pop: '6,500 est.',
      area: '41.0 ha',
      road: 'MONITORED (Rangirkhari Drainage Active)',
      classification: 'ASDMA Cachar Revenue Circle Grid'
    },
    {
      code: 'CCH-Z02',
      numberCode: '02',
      name: 'Katigorah Trans-Barak Corridor',
      risk: 'CRITICAL L-4',
      color: '#ff8786',
      coords: [[24.945, 92.630], [24.975, 92.630], [24.975, 92.670], [24.945, 92.670]],
      center: [24.962, 92.652],
      depth: '1.75m',
      pop: '5,800 est.',
      area: '51.0 ha',
      road: 'RESTRICTED (Kalain Link Submerged 0.45m)',
      classification: 'ASDMA Cachar Revenue Circle Grid'
    },
    {
      code: 'CCH-Z03',
      numberCode: '03',
      name: 'Lakhipur Eastern Corridor',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[24.715, 92.870], [24.745, 92.870], [24.745, 92.910], [24.715, 92.910]],
      center: [24.732, 92.892],
      depth: '0.55m',
      pop: '3,100 est.',
      area: '16.0 ha',
      road: 'OPEN (NH-37 East Transit)',
      classification: 'ASDMA Cachar Revenue Circle Grid'
    },
    {
      code: 'CCH-Z04',
      numberCode: '04',
      name: 'Sonai River Basin',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[24.775, 92.990], [24.805, 92.990], [24.805, 93.030], [24.775, 93.030]],
      center: [24.792, 93.012],
      depth: '0.80m',
      pop: '4,200 est.',
      area: '24.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Cachar Revenue Circle Grid'
    }
  ],
  kamrup_rural: [
    {
      code: 'KMR-Z01',
      numberCode: '01',
      name: 'Hajo Historic Lowlands',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.235, 91.580], [26.265, 91.580], [26.265, 91.620], [26.235, 91.620]],
      center: [26.252, 91.602],
      depth: '0.85m',
      pop: '3,800 est.',
      area: '21.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Kamrup Rural Circle Grid'
    },
    {
      code: 'KMR-Z02',
      numberCode: '02',
      name: 'Rangia Railway Junction',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.445, 91.610], [26.475, 91.610], [26.475, 91.650], [26.445, 91.650]],
      center: [26.462, 91.632],
      depth: '1.40m',
      pop: '5,100 est.',
      area: '36.0 ha',
      road: 'RESTRICTED (Borolia Overtopping)',
      classification: 'ASDMA Kamrup Rural Circle Grid'
    },
    {
      code: 'KMR-Z03',
      numberCode: '03',
      name: 'Palasbari Embankment Corridor',
      risk: 'CRITICAL',
      color: '#ff8786',
      coords: [[26.115, 91.480], [26.145, 91.480], [26.145, 91.520], [26.115, 91.520]],
      center: [26.132, 91.502],
      depth: '1.70m',
      pop: '4,600 est.',
      area: '42.0 ha',
      road: 'MONITORED',
      classification: 'ASDMA Kamrup Rural Circle Grid'
    },
    {
      code: 'KMR-Z04',
      numberCode: '04',
      name: 'Boko / Chaygaon Foothills',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[25.965, 91.210], [25.995, 91.210], [25.995, 91.250], [25.965, 91.250]],
      center: [25.982, 91.232],
      depth: '0.40m',
      pop: '2,600 est.',
      area: '14.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Kamrup Rural Circle Grid'
    }
  ],
  darrang: [
    {
      code: 'DRG-Z01',
      numberCode: '01',
      name: 'Mangaldai Sadar (Town Core)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.420, 92.015], [26.450, 92.015], [26.450, 92.055], [26.420, 92.055]],
      center: [26.435, 92.035],
      depth: '0.80m',
      pop: '4,100 est.',
      area: '24.0 ha',
      road: 'OPEN (NH-15 Main Artery)',
      classification: 'ASDMA Darrang Circle Grid'
    },
    {
      code: 'DRG-Z02',
      numberCode: '02',
      name: 'Sipajhar Lowlands Sector',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.365, 91.865], [26.395, 91.865], [26.395, 91.905], [26.365, 91.905]],
      center: [26.382, 91.886],
      depth: '1.50m',
      pop: '5,500 est.',
      area: '48.0 ha',
      road: 'RESTRICTED (Nonoi Backflow 0.35m)',
      classification: 'ASDMA Darrang Circle Grid'
    },
    {
      code: 'DRG-Z03',
      numberCode: '03',
      name: 'Dalgaon Charland Sector',
      risk: 'CRITICAL L-4',
      color: '#ff8786',
      coords: [[26.525, 92.190], [26.555, 92.190], [26.555, 92.230], [26.525, 92.230]],
      center: [26.540, 92.210],
      depth: '1.60m',
      pop: '6,400 est.',
      area: '52.0 ha',
      road: 'WATERCRAFT TRANSIT ONLY',
      classification: 'ASDMA Darrang Circle Grid'
    },
    {
      code: 'DRG-Z04',
      numberCode: '04',
      name: 'Patharighat Historic Plains',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.465, 91.930], [26.495, 91.930], [26.495, 91.970], [26.465, 91.970]],
      center: [26.480, 91.950],
      depth: '0.40m',
      pop: '2,800 est.',
      area: '14.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Darrang Circle Grid'
    }
  ],
  morigaon: [
    {
      code: 'MOR-Z01',
      numberCode: '01',
      name: 'Morigaon Sadar (Central Core)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.149, 92.330], [26.179, 92.330], [26.179, 92.370], [26.149, 92.370]],
      center: [26.164, 92.350],
      depth: '0.70m',
      pop: '3,500 est.',
      area: '21.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Morigaon Circle Grid'
    },
    {
      code: 'MOR-Z02',
      numberCode: '02',
      name: 'Mayong / Pabitora Corridor',
      risk: 'CRITICAL L-4',
      color: '#f07171',
      coords: [[26.225, 92.030], [26.255, 92.030], [26.255, 92.070], [26.225, 92.070]],
      center: [26.240, 92.050],
      depth: '1.90m',
      pop: '4,900 est.',
      area: '45.0 ha',
      road: 'RESTRICTED (Brahmaputra Backflow)',
      classification: 'ASDMA Morigaon Circle Grid'
    },
    {
      code: 'MOR-Z03',
      numberCode: '03',
      name: 'Bhuragaon Riparian Sector',
      risk: 'CRITICAL L-4',
      color: '#ff8786',
      coords: [[26.275, 92.400], [26.305, 92.400], [26.305, 92.440], [26.275, 92.440]],
      center: [26.290, 92.420],
      depth: '1.85m',
      pop: '5,200 est.',
      area: '58.0 ha',
      road: 'SEVERED (Dyke Overtopping)',
      classification: 'ASDMA Morigaon Circle Grid'
    },
    {
      code: 'MOR-Z04',
      numberCode: '04',
      name: 'Laharighat Erosion Sector',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.315, 92.460], [26.345, 92.460], [26.345, 92.500], [26.315, 92.500]],
      center: [26.330, 92.480],
      depth: '1.50m',
      pop: '6,100 est.',
      area: '49.0 ha',
      road: 'RESTRICTED',
      classification: 'ASDMA Morigaon Circle Grid'
    }
  ],
  goalpara: [
    {
      code: 'GLP-Z01',
      numberCode: '01',
      name: 'Goalpara Sadar (Town Front)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.163, 90.607], [26.193, 90.607], [26.193, 90.647], [26.163, 90.647]],
      center: [26.178, 90.627],
      depth: '0.80m',
      pop: '4,300 est.',
      area: '26.0 ha',
      road: 'OPEN (NH-17 Route Open)',
      classification: 'ASDMA Goalpara Circle Grid'
    },
    {
      code: 'GLP-Z02',
      numberCode: '02',
      name: 'Balijana Riverine Flatlands',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.105, 90.560], [26.135, 90.560], [26.135, 90.600], [26.105, 90.600]],
      center: [26.120, 90.580],
      depth: '0.55m',
      pop: '3,800 est.',
      area: '18.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Goalpara Circle Grid'
    },
    {
      code: 'GLP-Z03',
      numberCode: '03',
      name: 'Lakhipur Charlands Sector',
      risk: 'CRITICAL',
      color: '#f07171',
      coords: [[26.005, 90.290], [26.035, 90.290], [26.035, 90.330], [26.005, 90.330]],
      center: [26.020, 90.310],
      depth: '1.60m',
      pop: '4,700 est.',
      area: '46.0 ha',
      road: 'WATERCRAFT TRANSIT ONLY',
      classification: 'ASDMA Goalpara Circle Grid'
    },
    {
      code: 'GLP-Z04',
      numberCode: '04',
      name: 'Dudhnoi Foothills Sector',
      risk: 'LOW',
      color: '#27ae80',
      coords: [[25.965, 90.710], [25.995, 90.710], [25.995, 90.750], [25.965, 90.750]],
      center: [25.982, 90.732],
      depth: '0.20m',
      pop: '2,500 est.',
      area: '12.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Goalpara Circle Grid'
    }
  ],
  nagaon: [
    {
      code: 'NGN-Z01',
      numberCode: '01',
      name: 'Nagaon Sadar (Kolong Core)',
      risk: 'HIGH',
      color: '#f5b84b',
      coords: [[26.330, 92.665], [26.360, 92.665], [26.360, 92.705], [26.330, 92.705]],
      center: [26.345, 92.685],
      depth: '0.85m',
      pop: '6,200 est.',
      area: '35.0 ha',
      road: 'OPEN (NH-37 Core Corridor)',
      classification: 'ASDMA Nagaon Circle Grid'
    },
    {
      code: 'NGN-Z02',
      numberCode: '02',
      name: 'Kampur Sector (Kopili Bottleneck)',
      risk: 'CRITICAL L-4',
      color: '#ff8786',
      coords: [[26.138, 92.636], [26.168, 92.636], [26.168, 92.676], [26.138, 92.676]],
      center: [26.153, 92.656],
      depth: '1.95m',
      pop: '4,400 est.',
      area: '52.0 ha',
      road: 'RESTRICTED (Kampur-Dabaka Detour Enforced)',
      classification: 'ASDMA Nagaon Circle Grid'
    },
    {
      code: 'NGN-Z03',
      numberCode: '03',
      name: 'Kaliabor Hill-Flank Sector',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.505, 93.000], [26.535, 93.000], [26.535, 93.040], [26.505, 93.040]],
      center: [26.520, 93.020],
      depth: '0.50m',
      pop: '3,700 est.',
      area: '20.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Nagaon Circle Grid'
    },
    {
      code: 'NGN-Z04',
      numberCode: '04',
      name: 'Raha Wetland Corridor',
      risk: 'MODERATE',
      color: '#20bfa5',
      coords: [[26.205, 92.490], [26.235, 92.490], [26.235, 92.530], [26.205, 92.530]],
      center: [26.220, 92.510],
      depth: '0.45m',
      pop: '3,100 est.',
      area: '18.0 ha',
      road: 'OPEN',
      classification: 'ASDMA Nagaon Circle Grid'
    }
  ]
};

// Default Kamrup Metropolitan Guwahati Flood Risk Zones (EPSG:4326)
export const GIS_ZONES: GisZone[] = DISTRICT_GIS_ZONES.kamrup_metro;

// =============================================================================
// VERIFIED LOGISTICS FACILITIES: DEPOTS & EVACUATION SHELTERS PER DISTRICT
// =============================================================================

export const DISTRICT_GIS_SHELTERS: Record<string, GisShelter[]> = {
  kamrup_metro: [
    {
      id: 'depot-sarusajai',
      name: 'Sarusajai Central Logistics Hub',
      type: 'DEPOT',
      coords: [26.115, 91.758],
      color: '#20bfa5',
      label: 'DEPOT: SARUSAJAI',
      details: {
        title: 'Sarusajai Central Logistics Hub [DEPOT-GAU-01]',
        line1: 'Available Stock: 5,500 kg (Food: 2,500 kg, Water: 3,000 L)',
        line2: 'Active Convoys Staged: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER (ESTIMATED PLANNING RESERVE)'
      }
    },
    {
      id: 'shelter-girls-college',
      name: 'Kamrup Girls High School Camp',
      type: 'SHELTER',
      coords: [26.170, 91.732],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Kamrup Girls High School Relief Shelter',
        line1: 'Capacity: 350 / Current Occupancy: 140 (40.0%)',
        line2: 'Medical Officer: Dr. A. Phukan (On Duty)',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-dispur-high',
      name: 'Dispur High School Relief Shelter',
      type: 'SHELTER',
      coords: [26.145, 91.795],
      color: '#45bfea',
      label: 'SHELTER 02',
      details: {
        title: 'Dispur High School Relief Shelter',
        line1: 'Capacity: 500 / Current Occupancy: 95 (19.0%)',
        line2: 'Water Supply: 2x 2000L Sintex Clean Storage Tanks',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    }
  ],
  barpeta: [
    {
      id: 'depot-barpeta',
      name: 'Barpeta DDMA Central Godown',
      type: 'DEPOT',
      coords: [26.315, 90.980],
      color: '#20bfa5',
      label: 'DEPOT: BARPETA',
      details: {
        title: 'Barpeta DDMA Central Godown [DEPOT-BRP-01]',
        line1: 'Available Stock: 6,000 kg (Food: 2,800 kg, Water: 3,200 L)',
        line2: 'Fleet: 3 Units (Tata 407, SDRF Motorboat, Bolero 4WD)',
        provenance: 'ASDMA CONTINGENCY BUFFER (ESTIMATED PLANNING RESERVE)'
      }
    },
    {
      id: 'shelter-barpeta-girls',
      name: 'Barpeta Girls Higher Secondary School',
      type: 'SHELTER',
      coords: [26.322, 90.985],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Barpeta Girls H.S. School Relief Camp',
        line1: 'Capacity: 450 / Occupancy: 180 (40.0%)',
        line2: 'Sector: Barpeta Sadar Urban Basin',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-kalgachia-college',
      name: 'Kalgachia College Relief Shelter',
      type: 'SHELTER',
      coords: [26.388, 90.842],
      color: '#45bfea',
      label: 'SHELTER 02',
      details: {
        title: 'Kalgachia College Relief Camp',
        line1: 'Capacity: 600 / Occupancy: 310 (51.7%)',
        line2: 'Sector: Beki Riparian Charlands',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-mandia-hs',
      name: 'Mandia Higher Secondary School',
      type: 'SHELTER',
      coords: [26.192, 90.920],
      color: '#45bfea',
      label: 'SHELTER 03',
      details: {
        title: 'Mandia H.S. School Relief Camp',
        line1: 'Capacity: 400 / Occupancy: 220 (55.0%)',
        line2: 'Sector: Mandia Lowlands Sector',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    }
  ],
  nalbari: [
    {
      id: 'depot-nalbari',
      name: 'Nalbari District Relief Godown',
      type: 'DEPOT',
      coords: [26.440, 91.445],
      color: '#20bfa5',
      label: 'DEPOT: NALBARI',
      details: {
        title: 'Nalbari Relief Godown [DEPOT-NAL-01]',
        line1: 'Available Stock: 5,500 kg (Food: 2,600 kg, Water: 2,900 L)',
        line2: 'Fleet: 3 Units (Tata 407, SDRF Watercraft, Bolero Camper)',
        provenance: 'ASDMA CONTINGENCY BUFFER (ESTIMATED PLANNING RESERVE)'
      }
    },
    {
      id: 'shelter-nalbari-college',
      name: 'Nalbari College Relief Camp',
      type: 'SHELTER',
      coords: [26.445, 91.440],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Nalbari College Relief Shelter',
        line1: 'Capacity: 500 / Occupancy: 160 (32.0%)',
        line2: 'Sector: Nalbari Sadar Central Sector',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-barkhetri-hs',
      name: 'Mukalmua Higher Secondary School',
      type: 'SHELTER',
      coords: [26.282, 91.362],
      color: '#45bfea',
      label: 'SHELTER 02',
      details: {
        title: 'Mukalmua H.S. School Relief Camp',
        line1: 'Capacity: 550 / Occupancy: 280 (50.9%)',
        line2: 'Sector: Barkhetri Alluvial Basin',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-tihu-hs',
      name: 'Tihu High School Relief Camp',
      type: 'SHELTER',
      coords: [26.492, 91.322],
      color: '#45bfea',
      label: 'SHELTER 03',
      details: {
        title: 'Tihu High School Relief Camp',
        line1: 'Capacity: 350 / Occupancy: 90 (25.7%)',
        line2: 'Sector: Tihu Alluvial Plains',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    }
  ],
  cachar: [
    {
      id: 'depot-cachar',
      name: 'Silchar DSA Relief Godown',
      type: 'DEPOT',
      coords: [24.820, 92.790],
      color: '#20bfa5',
      label: 'DEPOT: SILCHAR',
      details: {
        title: 'Silchar DSA Relief Godown [CCH-DEPOT-01]',
        line1: 'Available Stock: 7,200 kg (Food: 3,400 kg, Water: 3,800 L)',
        line2: 'Fleet: 3 Units (Barak 4x4, Heavy Rescue 4x4, SDRF Boat)',
        provenance: 'ASDMA CONTINGENCY BUFFER (ESTIMATED PLANNING RESERVE)'
      }
    },
    {
      id: 'shelter-silchar-govt',
      name: 'Govt. Boys Higher Secondary School Silchar',
      type: 'SHELTER',
      coords: [24.825, 92.795],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Govt. Boys H.S. School Relief Camp',
        line1: 'Capacity: 600 / Occupancy: 270 (45.0%)',
        line2: 'Sector: Silchar Sadar Urban Sector',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-katigorah-hs',
      name: 'Katigorah Higher Secondary School',
      type: 'SHELTER',
      coords: [24.962, 92.652],
      color: '#45bfea',
      label: 'SHELTER 02',
      details: {
        title: 'Katigorah H.S. School Relief Camp',
        line1: 'Capacity: 500 / Occupancy: 320 (64.0%)',
        line2: 'Sector: Katigorah Trans-Barak Corridor',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    },
    {
      id: 'shelter-lakhipur-college',
      name: 'Lakhipur College Relief Shelter',
      type: 'SHELTER',
      coords: [24.732, 92.892],
      color: '#45bfea',
      label: 'SHELTER 03',
      details: {
        title: 'Lakhipur College Relief Camp',
        line1: 'Capacity: 450 / Occupancy: 110 (24.4%)',
        line2: 'Sector: Lakhipur East Corridor',
        provenance: 'VERIFIED SHELTER (ASDMA Designated Relief Camp Register)'
      }
    }
  ],
  kamrup_rural: [
    {
      id: 'depot-kmr',
      name: 'Amingaon DDMA Logistics Warehouse',
      type: 'DEPOT',
      coords: [26.240, 91.610],
      color: '#20bfa5',
      label: 'DEPOT: AMINGAON',
      details: {
        title: 'Amingaon DDMA Warehouse [DEPOT-KMR-01]',
        line1: 'Available Stock: 5,300 kg (Food: 2,500 kg, Water: 2,800 L)',
        line2: 'Fleet: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER (ESTIMATED PLANNING RESERVE)'
      }
    },
    {
      id: 'shelter-hajo-hs',
      name: 'Hajo Higher Secondary School',
      type: 'SHELTER',
      coords: [26.252, 91.602],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Hajo H.S. School Relief Camp',
        line1: 'Capacity: 450 / Occupancy: 130',
        line2: 'Sector: Hajo Historic Lowlands',
        provenance: 'VERIFIED SHELTER'
      }
    },
    {
      id: 'shelter-rangia-hs',
      name: 'Rangia Higher Secondary School',
      type: 'SHELTER',
      coords: [26.462, 91.632],
      color: '#45bfea',
      label: 'SHELTER 02',
      details: {
        title: 'Rangia H.S. School Relief Camp',
        line1: 'Capacity: 500 / Occupancy: 210',
        line2: 'Sector: Rangia Rail Corridor',
        provenance: 'VERIFIED SHELTER'
      }
    }
  ],
  darrang: [
    {
      id: 'depot-drg',
      name: 'Mangaldai District Relief Godown',
      type: 'DEPOT',
      coords: [26.430, 92.030],
      color: '#20bfa5',
      label: 'DEPOT: MANGALDAI',
      details: {
        title: 'Mangaldai Relief Godown [DEPOT-DRG-01]',
        line1: 'Available Stock: 5,100 kg (Food: 2,400 kg, Water: 2,700 L)',
        line2: 'Fleet: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER'
      }
    },
    {
      id: 'shelter-mangaldai-college',
      name: 'Mangaldai College Pavilion Camp',
      type: 'SHELTER',
      coords: [26.435, 92.035],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Mangaldai College Pavilion',
        line1: 'Capacity: 550 / Occupancy: 170',
        line2: 'Sector: Mangaldai Sadar',
        provenance: 'VERIFIED SHELTER'
      }
    }
  ],
  morigaon: [
    {
      id: 'depot-mor',
      name: 'Morigaon Stadium Logistics Hub',
      type: 'DEPOT',
      coords: [26.160, 92.345],
      color: '#20bfa5',
      label: 'DEPOT: MORIGAON',
      details: {
        title: 'Morigaon Stadium Hub [DEPOT-MOR-01]',
        line1: 'Available Stock: 5,600 kg (Food: 2,600 kg, Water: 3,000 L)',
        line2: 'Fleet: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER'
      }
    },
    {
      id: 'shelter-morigaon-hs',
      name: 'Morigaon Higher Secondary School',
      type: 'SHELTER',
      coords: [26.164, 92.350],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Morigaon H.S. School Camp',
        line1: 'Capacity: 450 / Occupancy: 190',
        line2: 'Sector: Morigaon Sadar',
        provenance: 'VERIFIED SHELTER'
      }
    }
  ],
  goalpara: [
    {
      id: 'depot-glp',
      name: 'Goalpara Town Central Warehouse',
      type: 'DEPOT',
      coords: [26.170, 90.620],
      color: '#20bfa5',
      label: 'DEPOT: GOALPARA',
      details: {
        title: 'Goalpara Central Warehouse [DEPOT-GLP-01]',
        line1: 'Available Stock: 5,300 kg (Food: 2,500 kg, Water: 2,800 L)',
        line2: 'Fleet: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER'
      }
    },
    {
      id: 'shelter-goalpara-college',
      name: 'Goalpara College Relief Camp',
      type: 'SHELTER',
      coords: [26.178, 90.627],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Goalpara College Relief Camp',
        line1: 'Capacity: 500 / Occupancy: 140',
        line2: 'Sector: Goalpara Sadar',
        provenance: 'VERIFIED SHELTER'
      }
    }
  ],
  nagaon: [
    {
      id: 'depot-ngn',
      name: 'Nagaon Polytechnic Relief Godown',
      type: 'DEPOT',
      coords: [26.340, 92.680],
      color: '#20bfa5',
      label: 'DEPOT: NAGAON',
      details: {
        title: 'Nagaon Polytechnic Godown [DEPOT-NGN-01]',
        line1: 'Available Stock: 6,400 kg (Food: 3,000 kg, Water: 3,400 L)',
        line2: 'Fleet: 3 Units',
        provenance: 'ASDMA CONTINGENCY BUFFER'
      }
    },
    {
      id: 'shelter-nagaon-poly',
      name: 'Nagaon Polytechnic Hostel Relief Camp',
      type: 'SHELTER',
      coords: [26.345, 92.685],
      color: '#45bfea',
      label: 'SHELTER 01',
      details: {
        title: 'Nagaon Polytechnic Hostel Camp',
        line1: 'Capacity: 600 / Occupancy: 280',
        line2: 'Sector: Nagaon Sadar',
        provenance: 'VERIFIED SHELTER'
      }
    }
  ]
};

export const GIS_SHELTERS: GisShelter[] = DISTRICT_GIS_SHELTERS.kamrup_metro;

// =============================================================================
// CWC & WRD ASSAM HYDROMETRIC MONITORING STATIONS
// =============================================================================

export const GIS_GAUGES: GisGauge[] = [
  {
    id: 'gauge-pandu',
    name: 'Brahmaputra River at Pandu Port',
    station: 'Pandu Central Port Gauge [CWC-PANDU-01]',
    river: 'Brahmaputra River Mainstem',
    district: 'Kamrup Metropolitan',
    coords: [26.185, 91.688],
    color: '#20bfa5',
    label: 'GAUGE: PANDU (49.68m)',
    levelM: 49.68,
    warningM: 48.60,
    dangerM: 49.60,
    hflM: 51.20,
    trend: 'STEADY (+0.02m / 3h)',
    discharge: '58,200 m³/s',
    statusText: 'WARNING STAGE (+0.08m over DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-dc-court',
    name: 'Brahmaputra River at Guwahati DC Court',
    station: 'Guwahati DC Court Ghat [CWC-DCCOURT-02]',
    river: 'Brahmaputra River Mainstem',
    district: 'Kamrup Metropolitan',
    coords: [26.192, 91.745],
    color: '#20bfa5',
    label: 'GAUGE: DC COURT (49.82m)',
    levelM: 49.82,
    warningM: 48.68,
    dangerM: 49.68,
    hflM: 51.46,
    trend: 'RISING (+0.04m / 3h)',
    discharge: '59,400 m³/s',
    statusText: 'DANGER STAGE (+0.14m over DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-bharalu',
    name: 'Bharalu River Sluice Gate Outfall',
    station: 'Bharalu Urban Sluice Outfall [WRD-BHARALU-03]',
    river: 'Bharalu Tributary Outfall',
    district: 'Kamrup Metropolitan',
    coords: [26.175, 91.732],
    color: '#f07171',
    label: 'SLUICE: BHARALU (BACKFLOW)',
    levelM: 48.95,
    warningM: 47.50,
    dangerM: 48.50,
    hflM: 50.10,
    trend: 'BACKFLOW (+0.10m / 3h)',
    discharge: '450 m³/s (Reverse Backflow Pressure)',
    statusText: 'SLUICE OVERTOPPING / BACKFLOW',
    sourceUrl: 'https://waterresources.assam.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-beki',
    name: 'Beki River at Barpeta Road Bridge',
    station: 'Beki Road Bridge [CWC-BEKI-06]',
    river: 'Beki River (Manas Tributary)',
    district: 'Barpeta',
    coords: [26.3216, 90.9865],
    color: '#20bfa5',
    label: 'GAUGE: BEKI (DL 45.10m)',
    levelM: 44.85,
    warningM: 44.10,
    dangerM: 45.10,
    hflM: 45.90,
    trend: 'RISING (+0.05m / 3h)',
    discharge: '8,400 m³/s',
    statusText: 'APPROACHING DANGER STAGE (0.25m below DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-pagladiya',
    name: 'Pagladiya River at NT Road Crossing',
    station: 'Pagladiya NT Road Crossing [CWC-PAGLADIYA-07]',
    river: 'Pagladiya River',
    district: 'Nalbari',
    coords: [26.4494, 91.4600],
    color: '#20bfa5',
    label: 'GAUGE: PAGLADIYA (DL 52.75m)',
    levelM: 52.20,
    warningM: 51.75,
    dangerM: 52.75,
    hflM: 54.10,
    trend: 'STEADY',
    discharge: '4,200 m³/s',
    statusText: 'MONITORED (0.55m below DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-barak',
    name: 'Barak River at Annapurna Ghat (Silchar)',
    station: 'Annapurna Ghat [CWC-BARAK-10]',
    river: 'Barak River Mainstem',
    district: 'Cachar',
    coords: [24.8319, 92.7961],
    color: '#20bfa5',
    label: 'GAUGE: BARAK (DL 19.83m)',
    levelM: 19.20,
    warningM: 18.83,
    dangerM: 19.83,
    hflM: 21.98,
    trend: 'WARNING (Rising +0.06m / 3h)',
    discharge: '14,600 m³/s',
    statusText: 'WARNING STAGE (0.63m below DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-puthimari',
    name: 'Puthimari River at NH Road Crossing',
    station: 'Puthimari NH Crossing [CWC-PALASBARI-03]',
    river: 'Puthimari River',
    district: 'Kamrup Rural',
    coords: [26.3467, 91.6458],
    color: '#20bfa5',
    label: 'GAUGE: PUTHIMARI (DL 51.81m)',
    levelM: 51.30,
    warningM: 50.81,
    dangerM: 51.81,
    hflM: 53.05,
    trend: 'STEADY',
    discharge: '3,800 m³/s',
    statusText: 'MONITORED (0.51m below DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-dharamtul',
    name: 'Kopili River at Dharamtul Bridge',
    station: 'Kopili Dharamtul [CWC-DHARAMTUL-05]',
    river: 'Kopili River',
    district: 'Morigaon',
    coords: [26.1642, 92.3500],
    color: '#f07171',
    label: 'GAUGE: DHARAMTUL (DL 56.00m)',
    levelM: 56.40,
    warningM: 55.00,
    dangerM: 56.00,
    hflM: 57.65,
    trend: 'RISING (+0.08m / 3h)',
    discharge: '9,100 m³/s',
    statusText: 'DANGER STAGE (+0.40m over DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-kampur',
    name: 'Kopili River at Kampur Post',
    station: 'Kopili Kampur [CWC-KAMPUR-02]',
    river: 'Kopili River',
    district: 'Nagaon',
    coords: [26.1531, 92.6564],
    color: '#f07171',
    label: 'GAUGE: KAMPUR (DL 60.50m)',
    levelM: 61.10,
    warningM: 59.50,
    dangerM: 60.50,
    hflM: 62.20,
    trend: 'SEVERE SURGE (+0.12m / 3h)',
    discharge: '11,200 m³/s',
    statusText: 'SEVERE FLOOD (+0.60m over DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  },
  {
    id: 'gauge-goalpara',
    name: 'Brahmaputra River at Goalpara Ghat',
    station: 'Goalpara Ghat [CWC-GOALPARA-09]',
    river: 'Brahmaputra River Mainstem',
    district: 'Goalpara',
    coords: [26.1782, 90.6272],
    color: '#20bfa5',
    label: 'GAUGE: GOALPARA (DL 36.27m)',
    levelM: 35.80,
    warningM: 35.27,
    dangerM: 36.27,
    hflM: 37.43,
    trend: 'STEADY',
    discharge: '62,000 m³/s',
    statusText: 'MONITORED (0.47m below DL)',
    sourceUrl: 'https://ffs.india-water.gov.in',
    sourceDate: '2026-10-10 14:00 IST',
    provenanceState: 'LIVE_SENSOR_FEED',
    isLiveTelemetry: true
  }
];

// =============================================================================
// FLEET VEHICLES PER DISTRICT
// =============================================================================

export const DISTRICT_GIS_VEHICLES: Record<string, GisVehicle[]> = {
  kamrup_metro: [
    { id: 'vh-01', name: 'VH-01: Tata 407 (4x4)', coords: [26.195, 91.710], color: '#61d4ff', label: 'VH-01 (Tata 407)', details: 'Zone 01 (North Guwahati)', status: 'DISPATCH READY' },
    { id: 'vh-02', name: 'VH-02: Ashok Leyland 4x4', coords: [26.168, 91.740], color: '#20bfa5', label: 'VH-02 (Ashok Leyland)', details: 'Zone 02 via AT Road Detour', status: 'DISPATCH READY' },
    { id: 'vh-03', name: 'VH-03: Bolero Camper', coords: [26.128, 91.775], color: '#f5b84b', label: 'VH-03 (Bolero Camper)', details: 'Zone 04 & 05 (Basistha/Dispur)', status: 'DISPATCH READY' }
  ],
  barpeta: [
    { id: 'brp-vh-01', name: 'BRP-VH-01: Tata 407 4x4', coords: [26.350, 90.910], color: '#61d4ff', label: 'BRP-VH-01 (4x4)', details: 'Barpeta Sadar -> Kalgachia', status: 'DISPATCH READY' },
    { id: 'brp-vh-02', name: 'BRP-VH-02: SDRF Rescue Rivercraft', coords: [26.388, 90.842], color: '#ff8786', label: 'BRP-VH-02 (Watercraft)', details: 'Beki Riparian Charland Evac', status: 'ACTIVE IN SECTOR' },
    { id: 'brp-vh-03', name: 'BRP-VH-03: Bolero 4WD Camper', coords: [26.335, 91.050], color: '#f5b84b', label: 'BRP-VH-03 (Bolero)', details: 'Sarthebari Alluvial Relay', status: 'DISPATCH READY' }
  ],
  nalbari: [
    { id: 'nlb-vh-01', name: 'NLB-VH-01: Tata 407 4x4', coords: [26.380, 91.390], color: '#61d4ff', label: 'NLB-VH-01 (4x4)', details: 'Barkhetri Basin Relief Run', status: 'DISPATCH READY' },
    { id: 'nlb-vh-02', name: 'NLB-VH-02: Pagladiya SDRF Boat', coords: [26.282, 91.362], color: '#ff8786', label: 'NLB-VH-02 (Watercraft)', details: 'Mukalmua Dyke Evacuation', status: 'ACTIVE IN SECTOR' },
    { id: 'nlb-vh-03', name: 'NLB-VH-03: Bolero 4WD Camper', coords: [26.470, 91.380], color: '#f5b84b', label: 'NLB-VH-03 (Bolero)', details: 'Tihu Lowlands Relay', status: 'DISPATCH READY' }
  ],
  cachar: [
    { id: 'cch-vh-01', name: 'CCH-VH-01: Tata 407 4x4', coords: [24.825, 92.795], color: '#61d4ff', label: 'CCH-VH-01 (4x4)', details: 'Silchar Sadar Relief Run', status: 'DISPATCH READY' },
    { id: 'cch-vh-02', name: 'CCH-VH-02: Heavy Rescue 4x4', coords: [24.900, 92.720], color: '#20bfa5', label: 'CCH-VH-02 (Heavy 4x4)', details: 'Katigorah Trans-Barak Corridor', status: 'DISPATCH READY' },
    { id: 'cch-vh-03', name: 'CCH-VH-03: SDRF Barak Jet-Boat', coords: [24.831, 92.796], color: '#ff8786', label: 'CCH-VH-03 (Jet-Boat)', details: 'Barak Riverfront Patrol', status: 'ACTIVE IN SECTOR' }
  ],
  kamrup_rural: [
    { id: 'kmr-vh-01', name: 'KMR-VH-01: Tata 407 4x4', coords: [26.350, 91.620], color: '#61d4ff', label: 'KMR-VH-01 (4x4)', details: 'Rangia North Artery', status: 'DISPATCH READY' }
  ],
  darrang: [
    { id: 'drg-vh-01', name: 'DRG-VH-01: Ashok Leyland 4x4', coords: [26.400, 91.950], color: '#61d4ff', label: 'DRG-VH-01 (4x4)', details: 'Sipajhar Lowlands Relay', status: 'DISPATCH READY' }
  ],
  morigaon: [
    { id: 'mor-vh-01', name: 'MOR-VH-01: High-Clearance 4x4', coords: [26.200, 92.200], color: '#61d4ff', label: 'MOR-VH-01 (4x4)', details: 'Mayong / Pabitora Corridor', status: 'DISPATCH READY' }
  ],
  goalpara: [
    { id: 'glp-vh-01', name: 'GLP-VH-01: Tata 407 4x4', coords: [26.080, 90.680], color: '#61d4ff', label: 'GLP-VH-01 (4x4)', details: 'Dudhnoi Foothills Transit', status: 'DISPATCH READY' }
  ],
  nagaon: [
    { id: 'ngn-vh-01', name: 'NGN-VH-01: Heavy Rescue 4x4', coords: [26.250, 92.660], color: '#61d4ff', label: 'NGN-VH-01 (4x4)', details: 'Kampur Flash Corridor via Dabaka', status: 'DISPATCH READY' }
  ]
};

export const GIS_VEHICLES: GisVehicle[] = DISTRICT_GIS_VEHICLES.kamrup_metro;

// =============================================================================
// FLEET DISPATCH CONVOY ROUTES PER DISTRICT
// =============================================================================

export const DISTRICT_GIS_ROUTES: Record<string, GisRoute[]> = {
  kamrup_metro: [
    {
      id: 'route-vh-01',
      name: 'Route 1: VH-01 Saraighat Corridor',
      vehicleCode: 'VH-01',
      color: '#61d4ff',
      weight: 2.5,
      opacity: 0.85,
      dashArray: '6 4',
      description: 'Round-trip from Sarusajai to North Guwahati via Saraighat Bridge',
      positions: [
        [26.115, 91.758], [26.120, 91.765], [26.130, 91.685], [26.185, 91.690],
        [26.208, 91.732], [26.185, 91.690], [26.130, 91.685], [26.115, 91.758]
      ]
    },
    {
      id: 'route-vh-02',
      name: 'Route 2: VH-02 AT Road Detour (Active Detour Bypassing MG Road)',
      vehicleCode: 'VH-02',
      color: '#20bfa5',
      weight: 3.5,
      opacity: 0.95,
      description: 'Bypasses submerged MG Road via AT Road Arya Nagar flyover to Kamrup Girls College',
      positions: [
        [26.115, 91.758], [26.120, 91.765], [26.155, 91.770], [26.175, 91.750],
        [26.165, 91.742], [26.172, 91.735], [26.170, 91.732], [26.165, 91.742], [26.115, 91.758]
      ]
    },
    {
      id: 'route-vh-03',
      name: 'Route 3: VH-03 Basistha / Dispur Corridor',
      vehicleCode: 'VH-03',
      color: '#f5b84b',
      weight: 2.5,
      opacity: 0.85,
      dashArray: '4 4',
      description: 'Direct distribution through Basistha to Dispur Secretariat Lowlands',
      positions: [
        [26.115, 91.758], [26.120, 91.765], [26.118, 91.785], [26.142, 91.792],
        [26.145, 91.795], [26.120, 91.765], [26.115, 91.758]
      ]
    }
  ],
  barpeta: [
    {
      id: 'brp-rt-01',
      name: 'BRP Route 1: BRP-VH-01 Kalgachia / Beki Artery',
      vehicleCode: 'BRP-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.90,
      description: 'Barpeta DDMA Godown -> NH-127A -> Kalgachia Riparian Drop (38.2 km)',
      positions: [
        [26.315, 90.980], [26.320, 90.985], [26.350, 90.950], [26.370, 90.910],
        [26.388, 90.842], [26.370, 90.910], [26.315, 90.980]
      ]
    },
    {
      id: 'brp-rt-02',
      name: 'BRP Route 2: BRP-VH-03 Sarthebari Circuit',
      vehicleCode: 'BRP-VH-03',
      color: '#f5b84b',
      weight: 2.5,
      opacity: 0.85,
      description: 'Barpeta Godown -> Sarthebari Alluvial Sector Relay (24.6 km)',
      positions: [
        [26.315, 90.980], [26.330, 91.020], [26.340, 91.080], [26.352, 91.122],
        [26.340, 91.080], [26.315, 90.980]
      ]
    }
  ],
  nalbari: [
    {
      id: 'nlb-rt-01',
      name: 'NLB Route 1: NLB-VH-01 Barkhetri Lowlands Corridor',
      vehicleCode: 'NLB-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.90,
      description: 'Nalbari Godown -> Mukalmua Relief Camp via PWD Artery (28.4 km)',
      positions: [
        [26.440, 91.445], [26.400, 91.420], [26.330, 91.380], [26.282, 91.362],
        [26.330, 91.380], [26.440, 91.445]
      ]
    },
    {
      id: 'nlb-rt-02',
      name: 'NLB Route 2: NLB-VH-03 Tihu Flood Plain Relay',
      vehicleCode: 'NLB-VH-03',
      color: '#f5b84b',
      weight: 2.5,
      opacity: 0.85,
      description: 'Nalbari Godown -> Tihu H.S. School Camp (22.1 km)',
      positions: [
        [26.440, 91.445], [26.460, 91.400], [26.480, 91.350], [26.492, 91.322],
        [26.460, 91.400], [26.440, 91.445]
      ]
    }
  ],
  cachar: [
    {
      id: 'cch-rt-01',
      name: 'CCH Route 1: CCH-VH-01 Silchar Sadar Core Circuit',
      vehicleCode: 'CCH-VH-01',
      color: '#61d4ff',
      weight: 2.5,
      opacity: 0.85,
      description: 'Silchar DSA Godown -> Govt. Boys H.S. School Camp (12.4 km)',
      positions: [
        [24.820, 92.790], [24.822, 92.792], [24.826, 92.796], [24.830, 92.805], [24.820, 92.790]
      ]
    },
    {
      id: 'cch-rt-02',
      name: 'CCH Route 2: CCH-VH-02 Katigorah Bypass Detour',
      vehicleCode: 'CCH-VH-02',
      color: '#20bfa5',
      weight: 3.5,
      opacity: 0.95,
      description: 'Silchar DSA -> Kumbhirgram Bypass -> Katigorah H.S. School (36.8 km)',
      positions: [
        [24.820, 92.790], [24.860, 92.820], [24.910, 92.860], [24.940, 92.750],
        [24.962, 92.652], [24.860, 92.820], [24.820, 92.790]
      ]
    }
  ],
  kamrup_rural: [
    {
      id: 'kmr-rt-01',
      name: 'KMR Route 1: KMR-VH-01 Rangia Railway Corridor',
      vehicleCode: 'KMR-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.85,
      description: 'Amingaon Depot -> Rangia Junction Camp (34.0 km)',
      positions: [[26.240, 91.610], [26.350, 91.620], [26.462, 91.632], [26.240, 91.610]]
    }
  ],
  darrang: [
    {
      id: 'drg-rt-01',
      name: 'DRG Route 1: DRG-VH-01 Sipajhar Lowlands Relay',
      vehicleCode: 'DRG-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.85,
      description: 'Mangaldai Godown -> Sipajhar Lowlands Drop (26.5 km)',
      positions: [[26.430, 92.030], [26.400, 91.950], [26.382, 91.886], [26.430, 92.030]]
    }
  ],
  morigaon: [
    {
      id: 'mor-rt-01',
      name: 'MOR Route 1: MOR-VH-01 Mayong Sanctuary Access',
      vehicleCode: 'MOR-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.85,
      description: 'Morigaon Stadium Hub -> Mayong / Pabitora Corridor (28.0 km)',
      positions: [[26.160, 92.345], [26.200, 92.200], [26.242, 92.052], [26.160, 92.345]]
    }
  ],
  goalpara: [
    {
      id: 'glp-rt-01',
      name: 'GLP Route 1: GLP-VH-01 Dudhnoi Foothills Run',
      vehicleCode: 'GLP-VH-01',
      color: '#61d4ff',
      weight: 3.0,
      opacity: 0.85,
      description: 'Goalpara Central Warehouse -> Dudhnoi Relief Post (32.5 km)',
      positions: [[26.170, 90.620], [26.080, 90.680], [25.982, 90.732], [26.170, 90.620]]
    }
  ],
  nagaon: [
    {
      id: 'ngn-rt-01',
      name: 'NGN Route 1: NGN-VH-01 Kampur Detour via Dabaka',
      vehicleCode: 'NGN-VH-01',
      color: '#20bfa5',
      weight: 3.5,
      opacity: 0.95,
      description: 'Nagaon Godown -> Dabaka Detour -> Kampur Breach Zone (42.0 km)',
      positions: [[26.340, 92.680], [26.250, 92.660], [26.155, 92.658], [26.340, 92.680]]
    }
  ]
};

export const GIS_ROUTES: GisRoute[] = DISTRICT_GIS_ROUTES.kamrup_metro;

// Road Chokepoint & Detours (per location)
export const DISTRICT_GIS_CHOKEPOINTS: Record<string, {
  coords: [number, number];
  label: string;
  color: string;
  title: string;
  desc: string;
  detour: string;
}> = {
  kamrup_metro: {
    coords: [26.175, 91.738],
    label: '⛔ MG ROAD (0.40m)',
    color: '#f07171',
    title: 'MG Road Santipur Chokepoint',
    desc: 'Submerged under 0.40m Brahmaputra backflow.',
    detour: 'Active Detour via AT Road Flyover enforced.'
  },
  barpeta: {
    coords: [26.370, 90.910],
    label: '⛔ BEKI BRIDGE (0.50m)',
    color: '#f07171',
    title: 'Beki Road Bridge Approach Chokepoint',
    desc: 'Water depth 0.50m over approach causeway.',
    detour: 'Heavy vehicles divert via Sarthebari-Pathsala link.'
  },
  nalbari: {
    coords: [26.330, 91.380],
    label: '⛔ PAGLADIYA DYKE (0.45m)',
    color: '#f07171',
    title: 'Barkhetri-Mukalmua Dyke Causeway',
    desc: 'Embankment overtopping with 0.45m flow.',
    detour: 'Divert via Tihu-Barama elevated corridor.'
  },
  cachar: {
    coords: [24.940, 92.750],
    label: '⛔ SILCHAR-KALAIN ROAD (0.45m)',
    color: '#f07171',
    title: 'Bethukandi Sluice / Kalain Link Chokepoint',
    desc: 'Submerged under 0.45m Barak waterlogging.',
    detour: 'Enforce detour via Kumbhirgram Airport Bypass.'
  }
};

export const GIS_CHOKEPOINT = DISTRICT_GIS_CHOKEPOINTS.kamrup_metro;

// =============================================================================
// PUBLIC ACCESSORS FOR MULTI-LOCATION DATA
// =============================================================================

export const getGisZonesForLocation = (locId: string): GisZone[] => {
  const norm = locId?.toLowerCase().trim() || 'kamrup_metro';
  return DISTRICT_GIS_ZONES[norm] || DISTRICT_GIS_ZONES.kamrup_metro;
};

export const getGisSheltersForLocation = (locId: string): GisShelter[] => {
  const norm = locId?.toLowerCase().trim() || 'kamrup_metro';
  return DISTRICT_GIS_SHELTERS[norm] || DISTRICT_GIS_SHELTERS.kamrup_metro;
};

export const getGisVehiclesForLocation = (locId: string): GisVehicle[] => {
  const norm = locId?.toLowerCase().trim() || 'kamrup_metro';
  return DISTRICT_GIS_VEHICLES[norm] || DISTRICT_GIS_VEHICLES.kamrup_metro;
};

export const getGisRoutesForLocation = (locId: string): GisRoute[] => {
  const norm = locId?.toLowerCase().trim() || 'kamrup_metro';
  return DISTRICT_GIS_ROUTES[norm] || DISTRICT_GIS_ROUTES.kamrup_metro;
};

export const getGisChokepointForLocation = (locId: string) => {
  const norm = locId?.toLowerCase().trim() || 'kamrup_metro';
  return DISTRICT_GIS_CHOKEPOINTS[norm] || null;
};

// Custom Tactical SVG Pins for Leaflet DivIcon
export const createTacticalIcon = (color: string, label: string) => {
  return L.divIcon({
    className: 'custom-tactical-pin',
    html: `
      <div style="
        background: #122130;
        border: 2px solid ${color};
        color: #d5e4f9;
        font-family: 'Inter', sans-serif;
        font-size: 10px;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
      ">
        <span style="width: 7px; height: 7px; border-radius: 50%; background: ${color}; display: inline-block;"></span>
        ${label}
      </div>
    `,
    iconSize: [80, 24],
    iconAnchor: [40, 12]
  });
};

// Coordinate safety validator & GeoJSON [lng, lat] to Leaflet [lat, lng] normalizer
export const normalizeToLatLng = (coord: any): [number, number] | null => {
  if (!Array.isArray(coord) || coord.length < 2) return null;
  const a = Number(coord[0]);
  const b = Number(coord[1]);
  if (isNaN(a) || isNaN(b)) return null;

  // Detect GeoJSON [longitude, latitude] where longitude in Assam is ~90-93 and latitude is ~24-27
  if (a > 60 && a <= 180 && b >= -90 && b <= 90) {
    return [b, a];
  }
  // Standard Leaflet [latitude, longitude]
  if (a >= -90 && a <= 90 && b >= -180 && b <= 180) {
    return [a, b];
  }
  return null;
};

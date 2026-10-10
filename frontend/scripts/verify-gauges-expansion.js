import fs from 'fs';
import path from 'path';

console.log('===============================================================');
console.log('RELIEFOS Lite — Assam River Gauges Layer Expansion Verification');
console.log('===============================================================\n');

let allPassed = true;
function check(description, condition, details = '') {
  if (condition) {
    console.log(`[PASS] ${description}`);
  } else {
    console.log(`[FAIL] ${description} - ${details}`);
    allPassed = false;
  }
}

const frontendDir = path.resolve('d:/projects/Disaster Relief Planning & Resource Optimization System/frontend');

// 1. Inspect gisLayersData.ts
const gisLayersData = fs.readFileSync(path.join(frontendDir, 'src/components/map/gisLayersData.ts'), 'utf-8');

check(
  'gisLayersData.ts defines GisGauge interface with river, district, warningM, hflM, provenance metadata',
  gisLayersData.includes('river?: string;') &&
  gisLayersData.includes('district?: string;') &&
  gisLayersData.includes('warningM?: number;') &&
  gisLayersData.includes('hflM?: number;') &&
  gisLayersData.includes('levelM?: number | null;') &&
  gisLayersData.includes('sourceUrl?: string;') &&
  gisLayersData.includes('isLiveTelemetry?: boolean;')
);

// Check all 7 requested stations in GIS_GAUGES
const requiredStations = [
  { id: 'cwc-dc-court', name: 'Guwahati DC Court', river: 'Brahmaputra', lat: 26.191, lon: 91.745, dl: 49.50, wl: 49.26 },
  { id: 'cwc-puthimari', name: 'Puthimari NH Road Crossing', river: 'Puthimari', lat: 26.3467, lon: 91.6458, dl: 51.81, wl: 50.81 },
  { id: 'cwc-beki', name: 'Beki Road Bridge', river: 'Beki', lat: 26.4947, lon: 90.9178, dl: 45.10, wl: 44.10 },
  { id: 'cwc-pagladiya', name: 'Pagladiya NT Road Crossing', river: 'Pagladiya', lat: 26.4494, lon: 91.4600, dl: 52.75, wl: 51.75 },
  { id: 'cwc-kopili-kampur', name: 'Kopili River at Kampur', river: 'Kopili', lat: 26.1531, lon: 92.6564, dl: 60.50, wl: 59.50 },
  { id: 'cwc-kopili-dharamtul', name: 'Kopili River at Dharamtul', river: 'Kopili', lat: 26.1642, lon: 92.3500, dl: 56.00, wl: 55.00 },
  { id: 'cwc-barak-apghat', name: 'Barak River at Annapurna Ghat', river: 'Barak', lat: 24.8319, lon: 92.7961, dl: 19.83, wl: 18.83 }
];

for (const req of requiredStations) {
  check(
    `GIS_GAUGES contains verified station: ${req.name} (${req.river})`,
    gisLayersData.includes(req.id) &&
    gisLayersData.includes(req.lat.toString()) &&
    gisLayersData.includes(req.lon.toString()) &&
    gisLayersData.includes(req.dl.toString())
  );
}

// 2. Check TacticalGisMap.tsx
const tacticalGisMap = fs.readFileSync(path.join(frontendDir, 'src/components/map/TacticalGisMap.tsx'), 'utf-8');
check(
  'TacticalGisMap supports gaugesFilterDistrict and handles null stage readings safely',
  tacticalGisMap.includes('gaugesFilterDistrict?: string;') &&
  tacticalGisMap.includes('const allGauges = gaugesData || GIS_GAUGES;') &&
  tacticalGisMap.includes('hasReading') &&
  tacticalGisMap.includes('[MANUAL POST • NO IOT]')
);

// 3. Check LiveFloodMap.tsx
const liveFloodMap = fs.readFileSync(path.join(frontendDir, 'src/pages/LiveFloodMap.tsx'), 'utf-8');
check(
  'LiveFloodMap contains district filter dropdown and Assam River Stations monitoring section',
  liveFloodMap.includes('selectedGaugeDistrict') &&
  liveFloodMap.includes('gaugesFilterDistrict={selectedGaugeDistrict}') &&
  liveFloodMap.includes('Assam River Stations')
);

// 4. Check DataSources.tsx
const dataSources = fs.readFileSync(path.join(frontendDir, 'src/pages/DataSources.tsx'), 'utf-8');
check(
  'DataSources registry contains Assam State River Gauges Network (10 Stations)',
  dataSources.includes('CWC-REGIONAL-01') &&
  dataSources.includes('Assam State River Gauges Network (10 Stations)') &&
  dataSources.includes('waterresources.assam.gov.in')
);

// 5. Check api.ts
const apiTs = fs.readFileSync(path.join(frontendDir, 'src/services/api.ts'), 'utf-8');
check(
  'api.ts supports district filtering in getFloodGauges',
  apiTs.includes('getFloodGauges: async (district?: string)')
);

console.log('\n===============================================================');
if (allPassed) {
  console.log('ALL FRONTEND GIS GAUGE EXPANSION VERIFICATION CHECKS PASSED!');
} else {
  console.log('SOME FRONTEND CHECKS FAILED!');
}
console.log('===============================================================\n');

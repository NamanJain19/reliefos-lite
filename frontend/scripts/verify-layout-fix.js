import fs from 'fs';
import path from 'path';

console.log('====================================================');
console.log('RELIEFOS Lite — GIS Map & AI Copilot Layout Verification');
console.log('====================================================\n');

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

// 1. Check index.css and styles/index.css for .leaflet-container isolation
const indexCss = fs.readFileSync(path.join(frontendDir, 'src/index.css'), 'utf-8');
const stylesIndexCss = fs.readFileSync(path.join(frontendDir, 'src/styles/index.css'), 'utf-8');

check(
  'index.css defines isolation: isolate on .leaflet-container',
  indexCss.includes('.leaflet-container') && indexCss.includes('isolation: isolate') && indexCss.includes('z-index: 0')
);

check(
  'styles/index.css defines isolation: isolate on .leaflet-container',
  stylesIndexCss.includes('.leaflet-container') && stylesIndexCss.includes('isolation: isolate') && stylesIndexCss.includes('z-index: 0')
);

// 2. Check TacticalGisMap.tsx for isolate class on container
const tacticalGisMap = fs.readFileSync(path.join(frontendDir, 'src/components/map/TacticalGisMap.tsx'), 'utf-8');
check(
  'TacticalGisMap.tsx container has isolate class',
  tacticalGisMap.includes('isolate') && tacticalGisMap.includes('ref={containerRef}')
);

// 3. Check LiveFloodMap.tsx and OperationsOverview.tsx
const liveFloodMap = fs.readFileSync(path.join(frontendDir, 'src/pages/LiveFloodMap.tsx'), 'utf-8');
check(
  'LiveFloodMap.tsx viewport container has isolate class',
  liveFloodMap.includes('bg-[#051423] isolate')
);

const operationsOverview = fs.readFileSync(path.join(frontendDir, 'src/pages/OperationsOverview.tsx'), 'utf-8');
check(
  'OperationsOverview.tsx map container has isolate class',
  operationsOverview.includes('bg-[#051423] h-[360px] isolate')
);

// 4. Check DisasterResponseCopilot.tsx
const copilot = fs.readFileSync(path.join(frontendDir, 'src/components/ai/DisasterResponseCopilot.tsx'), 'utf-8');
check(
  'DisasterResponseCopilot backdrop has z-[1200] and onClick dismissal',
  copilot.includes('z-[1200]') && copilot.includes('onClick={onClose}')
);
check(
  'DisasterResponseCopilot drawer container has z-[1201] and solid background',
  copilot.includes('z-[1201]') && copilot.includes('bg-[#0e1d2c]') && copilot.includes('onClick={(e) => e.stopPropagation()}')
);
check(
  'DisasterResponseCopilot header has solid background bg-[#122130]',
  copilot.includes('bg-[#122130]')
);
check(
  'DisasterResponseCopilot telemetry strip has solid background bg-[#010f1e]',
  copilot.includes('bg-[#010f1e]')
);
check(
  'DisasterResponseCopilot message stream has solid background bg-[#051423]',
  copilot.includes('bg-[#051423]')
);
check(
  'DisasterResponseCopilot Context Inspector modal has z-[1300] and solid background bg-[#122130]',
  copilot.includes('z-[1300]') && copilot.includes('z-[1301]') && copilot.includes('bg-[#122130]')
);

// 5. Check AppLayout.tsx
const appLayout = fs.readFileSync(path.join(frontendDir, 'src/components/layout/AppLayout.tsx'), 'utf-8');
check(
  'AppLayout floating launcher has z-[1050] (above Leaflet controls 1000, below Copilot 1200)',
  appLayout.includes('z-[1050]')
);

// 6. Check UserProfileModal and DemoDrillModal
const profileModal = fs.readFileSync(path.join(frontendDir, 'src/components/layout/UserProfileModal.tsx'), 'utf-8');
check(
  'UserProfileModal has z-[1200] and solid opaque background',
  profileModal.includes('z-[1200]') && profileModal.includes('bg-[#0e1d2c]')
);

const drillModal = fs.readFileSync(path.join(frontendDir, 'src/components/layout/DemoDrillModal.tsx'), 'utf-8');
check(
  'DemoDrillModal has z-[1200] and solid opaque background',
  drillModal.includes('z-[1200]') && drillModal.includes('bg-[#0e1d2c]')
);

// 7. Verify built dist files exist
const distDir = path.join(frontendDir, 'dist');
check('Frontend dist/index.html exists', fs.existsSync(path.join(distDir, 'index.html')));

const distAssets = fs.existsSync(path.join(distDir, 'assets')) ? fs.readdirSync(path.join(distDir, 'assets')) : [];
check('Frontend dist contains DisasterResponseCopilot chunk', distAssets.some(f => f.startsWith('DisasterResponseCopilot')));
check('Frontend dist contains TacticalGisMap chunk', distAssets.some(f => f.startsWith('TacticalGisMap')));
check('Frontend dist contains vendor-leaflet chunk', distAssets.some(f => f.startsWith('vendor-leaflet')));

console.log('\n====================================================');
if (allPassed) {
  console.log('ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!');
} else {
  console.log('SOME CHECKS FAILED!');
}
console.log('====================================================');

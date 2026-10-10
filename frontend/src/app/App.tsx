import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';

// Route-level code-splitting: Lazy load pages to optimize initial bundle size
const OperationsOverview = React.lazy(() =>
  import('../pages/OperationsOverview').then((m) => ({ default: m.OperationsOverview }))
);
const LiveFloodMap = React.lazy(() =>
  import('../pages/LiveFloodMap').then((m) => ({ default: m.LiveFloodMap }))
);
const ZonesRisk = React.lazy(() =>
  import('../pages/ZonesRisk').then((m) => ({ default: m.ZonesRisk }))
);
const ResourceInventory = React.lazy(() =>
  import('../pages/ResourceInventory').then((m) => ({ default: m.ResourceInventory }))
);
const DemandManagement = React.lazy(() =>
  import('../pages/DemandManagement').then((m) => ({ default: m.DemandManagement }))
);
const ReliefAllocation = React.lazy(() =>
  import('../pages/ReliefAllocation').then((m) => ({ default: m.ReliefAllocation }))
);
const RouteOptimization = React.lazy(() =>
  import('../pages/RouteOptimization').then((m) => ({ default: m.RouteOptimization }))
);
const SimulationReports = React.lazy(() =>
  import('../pages/SimulationReports').then((m) => ({ default: m.SimulationReports }))
);
const DataSources = React.lazy(() =>
  import('../pages/DataSources').then((m) => ({ default: m.DataSources }))
);
const SettingsPage = React.lazy(() =>
  import('../pages/SettingsPage').then((m) => ({ default: m.SettingsPage }))
);

import { LocationProvider } from '../context/LocationContext';

export const App: React.FC = () => {
  return (
    <LocationProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<OperationsOverview />} />
            <Route path="flood-map" element={<LiveFloodMap />} />
            <Route path="zones" element={<ZonesRisk />} />
            <Route path="inventory" element={<ResourceInventory />} />
            <Route path="demand" element={<DemandManagement />} />
            <Route path="allocation" element={<ReliefAllocation />} />
            <Route path="routes" element={<RouteOptimization />} />
            <Route path="simulation" element={<SimulationReports />} />
            <Route path="data-sources" element={<DataSources />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </LocationProvider>
  );
};

export default App;

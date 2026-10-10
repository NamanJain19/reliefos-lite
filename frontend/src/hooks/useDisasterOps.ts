import { useState, useEffect } from 'react';
import { api } from '../services/api';

export function useDisasterOps() {
  const [loading, setLoading] = useState<boolean>(true);
  const [dashboard, setDashboard] = useState<any>(null);
  const [zones, setZones] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const [dashData, zoneData] = await Promise.all([
          api.getDashboard(),
          api.getZones()
        ]);
        if (mounted) {
          setDashboard(dashData);
          setZones(zoneData);
        }
      } catch (err: any) {
        if (mounted) setError(err.message || 'Failed to load telemetry');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, []);

  return { loading, dashboard, zones, error };
}

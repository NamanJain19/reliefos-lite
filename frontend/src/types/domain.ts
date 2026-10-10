// Domain TypeScript definitions for RELIEFOS Lite

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';

export interface Zone {
  code: string;
  name: string;
  risk_level: RiskLevel;
  risk_score: number;
  latitude: number;
  longitude: number;
  affected_population: number;
  inundation_area_ha: number;
  water_depth_m: number;
  status: string;
  road_status: 'OPEN' | 'IMPEDED' | 'SEVERED';
}

export interface Depot {
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  capacity_kg: number;
  available_stock_kg: number;
}

export interface Vehicle {
  code: string;
  name: string;
  plate: string;
  type: string;
  capacity_kg: number;
  status: 'READY' | 'DISPATCHED' | 'STANDBY';
  fuel_pct: number;
  assigned_zone?: string;
}

export interface InventoryItem {
  sku: string;
  name: string;
  category: string;
  total_quantity: number;
  available_quantity: number;
  reserved_quantity: number;
  unit: string;
  status: string;
  storage_location: string;
  criticality: 'HIGH' | 'CRITICAL' | 'STANDARD';
}

export interface DemandRequisition {
  id: string;
  zone_code: string;
  zone_name: string;
  resource_type: string;
  requested_qty: number;
  fulfilled_qty: number;
  unit: string;
  priority: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  status: 'PENDING' | 'APPROVED' | 'DISPATCHED' | 'FULFILLED';
  created_at: string;
}

export interface OptimizationResponse {
  status: 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE';
  algorithm: string;
  solver_runtime_ms: number;
  total_available_stock_kg: number;
  total_reviewed_demand_kg: number;
  proposed_allocation_kg: number;
  projected_deficit_kg: number;
  coverage_ratio_pct: number;
  weighted_unmet_penalty: number;
  est_transit_distance_km: number;
  feasibility_checks: Record<string, boolean>;
  human_in_loop_status: string;
  zones: {
    zone_code: string;
    zone_name: string;
    priority_tier: string;
    demand_kg: number;
    allocated_kg: number;
    fulfillment_pct: number;
    shortfall_kg: number;
  }[];
}

export interface TelemetryFeed {
  id: string;
  name: string;
  authority: string;
  classification: string;
  protocol: string;
  cadence: string;
  last_ingest: string;
  health_pct: number;
  status: 'healthy' | 'warning' | 'degraded';
}

import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8013';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: attach auth token and selected location ID if available
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      const locationId = localStorage.getItem('reliefos_selected_location_id') || 'kamrup_metro';
      config.headers['X-Location-ID'] = locationId;
    }
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response Interceptor: structured logging and graceful error propagation
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.warn(`[API Response Error ${error.response.status}] ${error.config?.url}:`, error.response.data);
    } else if (error.request) {
      console.warn(`[API Network Timeout/Down] Failed to reach backend at ${API_BASE_URL}:`, error.message);
    } else {
      console.error('[API Configuration Error]', error.message);
    }
    return Promise.reject(error);
  }
);

export const api = {
  getHealth: async () => {
    try {
      const res = await apiClient.get('/health');
      return res.data;
    } catch {
      return {
        status: 'offline',
        mode: 'UNAVAILABLE',
        active_mode: 'UNAVAILABLE',
        telemetry: 'OFFLINE • BACKEND DISCONNECTED',
        system_mode: { mode: 'UNAVAILABLE', is_operational: false }
      };
    }
  },
  getDashboard: async () => {
    try {
      const res = await apiClient.get('/dashboard');
      return res.data;
    } catch (e) {
      console.warn('Backend unavailable, using simulated dashboard cache', e);
      return null;
    }
  },
  getZones: async () => {
    try {
      const res = await apiClient.get('/zones');
      return res.data;
    } catch {
      return [];
    }
  },
  getZoneByCode: async (code: string) => {
    try {
      const res = await apiClient.get(`/zones/${code}`);
      return res.data;
    } catch {
      return null;
    }
  },
  getFloodTelemetry: async () => {
    try {
      const res = await apiClient.get('/flood');
      return res.data;
    } catch {
      return null;
    }
  },
  getShelters: async () => {
    try {
      const res = await apiClient.get('/shelters');
      return res.data;
    } catch {
      return [];
    }
  },
  getVehicles: async () => {
    try {
      const res = await apiClient.get('/vehicles');
      return res.data;
    } catch {
      return [];
    }
  },
  getInventory: async () => {
    try {
      const res = await apiClient.get('/inventory');
      return res.data;
    } catch {
      return null;
    }
  },
  addInventory: async (data: any) => {
    const res = await apiClient.post('/inventory/add', data);
    return res.data;
  },
  getDemands: async () => {
    try {
      const res = await apiClient.get('/demands');
      return res.data;
    } catch {
      return [];
    }
  },
  createDemand: async (data: any) => {
    const res = await apiClient.post('/demands', data);
    return res.data;
  },
  getAllocations: async () => {
    try {
      const res = await apiClient.get('/allocations');
      return res.data;
    } catch {
      return null;
    }
  },
  runOptimization: async (params = {}) => {
    const res = await apiClient.post('/allocations/optimize', params);
    return res.data;
  },
  getAllocationComparison: async () => {
    try {
      const res = await apiClient.get('/allocations/comparison');
      return res.data;
    } catch {
      return null;
    }
  },
  getRoutes: async () => {
    try {
      const res = await apiClient.get('/routes');
      return res.data;
    } catch {
      return null;
    }
  },
  recalculateRoutes: async () => {
    const res = await apiClient.post('/routes/recalculate');
    return res.data;
  },
  getSimulations: async () => {
    try {
      const res = await apiClient.get('/simulations');
      return res.data;
    } catch {
      return null;
    }
  },
  getSimulationScenarios: async () => {
    try {
      const res = await apiClient.get('/simulations/scenarios');
      return res.data;
    } catch {
      return [];
    }
  },
  runSimulationScenario: async (scenarioId: string, customOverrides?: any) => {
    const res = await apiClient.post('/simulations/run', {
      scenario_id: scenarioId,
      custom_overrides: customOverrides || null
    });
    return res.data;
  },
  getSimulationComparison: async (scenarioIds?: string) => {
    try {
      const params = scenarioIds ? { scenario_ids: scenarioIds } : {};
      const res = await apiClient.get('/simulations/comparison', { params });
      return res.data;
    } catch {
      return null;
    }
  },
  getSimulationScalability: async () => {
    try {
      const res = await apiClient.get('/simulations/scalability');
      return res.data;
    } catch {
      return null;
    }
  },
  getDrillStatus: async () => {
    try {
      const res = await apiClient.get('/demo/drill/status');
      return res.data;
    } catch {
      return { is_demo_active: false, mode: 'STANDARD_OPERATIONAL' };
    }
  },
  loadDrillScenario: async () => {
    const res = await apiClient.post('/demo/drill/load');
    return res.data;
  },
  runDrillScenario: async (overrides?: any) => {
    const res = await apiClient.post('/demo/drill/run', overrides || {});
    return res.data;
  },
  resetDrillEnvironment: async () => {
    const res = await apiClient.post('/demo/drill/reset');
    return res.data;
  },
  exportDrillDossier: async () => {
    const res = await apiClient.get('/demo/drill/export');
    return res.data;
  },
  getDataSources: async () => {
    try {
      const res = await apiClient.get('/data-sources');
      return res.data;
    } catch {
      return null;
    }
  },
  getSettings: async () => {
    try {
      const res = await apiClient.get('/settings');
      return res.data;
    } catch {
      return null;
    }
  },
  getGisZonesGeoJson: async () => {
    try {
      const res = await apiClient.get('/gis/zones.geojson');
      return res.data;
    } catch (e) {
      console.warn('Could not fetch GIS zones GeoJSON:', e);
      return null;
    }
  },
  getGisInfrastructureGeoJson: async () => {
    try {
      const res = await apiClient.get('/gis/infrastructure.geojson');
      return res.data;
    } catch (e) {
      console.warn('Could not fetch GIS infrastructure GeoJSON:', e);
      return null;
    }
  },
  getGisRoutesGeoJson: async () => {
    try {
      const res = await apiClient.get('/gis/routes.geojson');
      return res.data;
    } catch (e) {
      console.warn('Could not fetch GIS routes GeoJSON:', e);
      return null;
    }
  },
  getGisValidationReport: async () => {
    try {
      const res = await apiClient.get('/gis/validation-report');
      return res.data;
    } catch (e) {
      console.warn('Could not fetch GIS validation report:', e);
      return null;
    }
  },
  validateGeoJsonPayload: async (payload: any, datasetName = 'Client Submission') => {
    const res = await apiClient.post('/gis/validate-geojson', payload, {
      params: { dataset_name: datasetName }
    });
    return res.data;
  },
  getProvidersHealth: async () => {
    try {
      const res = await apiClient.get('/health/providers');
      return res.data;
    } catch {
      return { total_providers: 0, providers: [] };
    }
  },
  getSystemMode: async () => {
    try {
      const res = await apiClient.get('/mode');
      return res.data;
    } catch {
      return { mode: 'OPERATIONAL_LIVE', is_operational: true };
    }
  },
  switchSystemMode: async (data: { mode: string; operator_name?: string; historical_event_id?: string; notes?: string }) => {
    const res = await apiClient.post('/mode/switch', data);
    return res.data;
  },
  getCurrentWeather: async () => {
    try {
      const res = await apiClient.get('/weather/current');
      return res.data;
    } catch {
      return null;
    }
  },
  getWeatherForecast: async () => {
    try {
      const res = await apiClient.get('/weather/forecast');
      return res.data;
    } catch {
      return null;
    }
  },
  getFloodGauges: async (district?: string) => {
    try {
      const res = await apiClient.get('/flood/gauges', {
        params: district && district !== 'ALL' ? { district } : undefined
      });
      return res.data;
    } catch {
      return { stations: [] };
    }
  },
  postManualGaugeReading: async (data: { station_id: string; water_level_m: number; operator_name?: string; notes?: string }) => {
    const res = await apiClient.post('/flood/gauges/manual-entry', data);
    return res.data;
  },
  getRoadClosures: async () => {
    try {
      const res = await apiClient.get('/roads/closures');
      return res.data;
    } catch {
      return { total_active_closures: 0, closures: [] };
    }
  },
  postRoadClosure: async (data: any) => {
    const res = await apiClient.post('/roads/closures', data);
    return res.data;
  },
  calculateRealRoute: async (data: { start_lat: number; start_lng: number; end_lat: number; end_lng: number; route_name?: string }) => {
    const res = await apiClient.post('/routes/real-route', data);
    return res.data;
  },
  getHistoricalEvents: async () => {
    try {
      const res = await apiClient.get('/historical/events');
      return res.data;
    } catch {
      return { catalog: [] };
    }
  },
  getHistoricalEventDetails: async (eventId: string) => {
    try {
      const res = await apiClient.get(`/historical/events/${eventId}`);
      return res.data;
    } catch {
      return null;
    }
  },
  getAuditLogs: async (limit = 50) => {
    try {
      const res = await apiClient.get('/audit-logs', { params: { limit } });
      return res.data;
    } catch {
      return [];
    }
  },
  verifyDemand: async (demandId: string, data: { verified_by?: string; notes?: string }) => {
    const res = await apiClient.post(`/demands/${demandId}/verify`, data);
    return res.data;
  },
  dispatchDemand: async (demandId: string, data: { vehicle_code: string; dispatched_by?: string; notes?: string }) => {
    const res = await apiClient.post(`/demands/${demandId}/dispatch`, data);
    return res.data;
  },
  queryAiCopilot: async (data: AIQueryRequest): Promise<AIStructuredResponse> => {
    const res = await apiClient.post('/ai/query', data);
    return res.data;
  },
  getAiHealth: async (): Promise<AIProviderHealth> => {
    const res = await apiClient.get('/ai/health');
    return res.data;
  },
  getAiContextPreview: async (modules?: string, zoneCode?: string, locationId?: string) => {
    const res = await apiClient.get('/ai/context/preview', {
      params: { modules, zone_code: zoneCode, location_id: locationId }
    });
    return res.data;
  },
  reviewAiAction: async (data: ActionReviewRequest): Promise<ActionReviewResponse> => {
    const res = await apiClient.post('/ai/actions/review', data);
    return res.data;
  },
  getRiskDatasetAudit: async (): Promise<DatasetAuditResponse> => {
    const res = await apiClient.get('/risk/dataset-audit');
    return res.data;
  },
  getFloodRiskAnalysis: async (forceBaseline = false, zoneCode?: string): Promise<FloodRiskAnalysisResponse> => {
    const res = await apiClient.get('/risk/analysis', {
      params: { force_baseline: forceBaseline, zone_code: zoneCode }
    });
    return res.data;
  },
  recalculateFloodRisk: async (data: RecalculateRiskRequest): Promise<FloodRiskAnalysisResponse> => {
    const res = await apiClient.post('/risk/calculate', data);
    return res.data;
  },
  getRiskModelMetadata: async (): Promise<MLModelMetadataResponse> => {
    const res = await apiClient.get('/risk/model-metadata');
    return res.data;
  },
  getRiskDataRequirements: async () => {
    const res = await apiClient.get('/risk/data-requirements');
    return res.data;
  },
  // Authentication & RBAC
  login: async (credentials: { username: string; password: string }): Promise<AuthLoginResponse> => {
    const res = await apiClient.post('/auth/login', credentials);
    if (res.data?.access_token && typeof window !== 'undefined') {
      localStorage.setItem('auth_token', res.data.access_token);
    }
    return res.data;
  },
  getAuthMe: async (): Promise<UserProfileResponse> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  getAuthRoles: async () => {
    const res = await apiClient.get('/auth/roles');
    return res.data;
  },
  updateProfile: async (data: UpdateProfileRequest): Promise<UserProfileResponse> => {
    const res = await apiClient.put('/auth/me', data);
    return res.data;
  },
  uploadAvatar: async (avatar_data_url: string): Promise<UserProfileResponse> => {
    const res = await apiClient.post('/auth/avatar', { avatar_data_url });
    return res.data;
  },
  removeAvatar: async (): Promise<UserProfileResponse> => {
    const res = await apiClient.delete('/auth/avatar');
    return res.data;
  },
  exportDossier: async (): Promise<any> => {
    const res = await apiClient.get('/auth/dossier/export');
    return res.data;
  },
  changePassword: async (data: ChangePasswordRequest): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.post('/auth/change-password', data);
    return res.data;
  },
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  },
  // Demand Forecasting & Sphere Projections
  getDemandForecast: async (horizonHours: number = 24): Promise<DemandForecastResponse> => {
    const res = await apiClient.get('/forecasting/forecast', {
      params: { horizon_hours: horizonHours }
    });
    return res.data;
  },
  getDemandDataSufficiency: async (): Promise<DemandDataSufficiencyAudit> => {
    const res = await apiClient.get('/forecasting/data-sufficiency');
    return res.data;
  },
  getForecastingModelMetadata: async () => {
    const res = await apiClient.get('/forecasting/model-metadata');
    return res.data;
  },
  // Logistics Advisor & Review
  getLogisticsPlan: async (strategy: string = 'LEXICOGRAPHIC_SEVERITY_OPTIMAL'): Promise<LogisticsAdvisorPlanResponse> => {
    const res = await apiClient.get<LogisticsAdvisorPlanResponse>('/logistics-advisor/plan', { params: { strategy } });
    return res.data;
  },
  reviewLogisticsPlan: async (data: PlanReviewRequest): Promise<PlanReviewResponse> => {
    const res = await apiClient.post<PlanReviewResponse>('/logistics-advisor/review', data);
    return res.data;
  },
};

export interface UserProfileResponse {
  username: string;
  role: string;
  name: string;
  agency: string;
  email?: string;
  phone?: string;
  avatar_url?: string;
}

export interface UpdateProfileRequest {
  name?: string;
  email?: string;
  phone?: string;
  agency?: string;
  avatar_url?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface AuthLoginResponse {
  success: boolean;
  access_token: string;
  token_type: string;
  expires_in_hours: number;
  user: UserProfileResponse;
}

export interface ResourceForecastDetail {
  resource_type: string;
  unit: string;
  current_verified_demand: number;
  forecast_demand: number;
  forecast_lower_bound: number;
  forecast_upper_bound: number;
  variance_from_current: number;
  variance_pct: number;
  variance_status: string;
  per_capita_daily_ration: number;
  status: string;
  unavailability_reason?: string;
}

export interface ContributingFactors {
  base_population: number;
  estimated_displaced_persons: number;
  vulnerability_ratio_pct: number;
  flood_risk_score: number;
  flood_risk_tier: string;
  hazard_escalation_multiplier: number;
  forecast_precipitation_24h_mm: number;
  river_gauge_variance_m: number;
  sphere_ration_standard: string;
  terrain_drainage_factor: number;
}

export interface ZoneDemandForecast {
  zone_code: string;
  zone_name: string;
  population: number;
  estimated_vulnerable_population: number;
  vulnerability_ratio_pct: number;
  current_risk_tier: string;
  current_risk_score: number;
  forecast_horizon_hours: number;
  hazard_multiplier: number;
  contributing_factors: ContributingFactors;
  forecasts: ResourceForecastDetail[];
  data_quality_warnings: string[];
}

export interface CitywideTotals {
  total_current_food_kg: number;
  total_current_water_l: number;
  total_forecast_food_kg: number;
  total_forecast_water_l: number;
  total_displaced_persons_est: number;
  net_food_variance_kg: number;
  net_water_variance_l: number;
}

export interface DemandDataSufficiencyAudit {
  audited_at: string;
  total_active_demands_in_db: number;
  active_resource_types: string[];
  historical_disaster_events_count: number;
  has_continuous_timeseries: boolean;
  is_sufficient_for_ml: boolean;
  verdict_code: string;
  verdict_explanation: string;
  supported_categories: Array<{
    category_name: string;
    resource_type: string;
    unit: string;
    status: string;
    notes: string;
  }>;
  unsupported_categories: Array<{
    category_name: string;
    resource_type: string;
    unit: string;
    status: string;
    notes: string;
  }>;
  data_gap_reasons: string[];
  statutory_data_requirements_to_train_ml: string[];
}

export interface DemandForecastResponse {
  generated_at: string;
  forecast_horizon_hours: number;
  scoring_engine: string;
  is_ml_model: boolean;
  citywide_totals: CitywideTotals;
  zones: ZoneDemandForecast[];
  data_sufficiency: DemandDataSufficiencyAudit;
  data_freshness: Record<string, string>;
  governance_notice: string;
}

export interface AISupportingEvidence {
  source: string;
  data_point: string;
  provenance_state: string;
  observation_time: string;
  trust_tier: string;
}

export interface AIProposedAction {
  action_id: string;
  title: string;
  target_entity: string;
  action_type: 'REVIEW_ALLOCATION' | 'VERIFY_DEMAND' | 'APPROVE_DETOUR' | 'REPLENISH_STOCK' | string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | string;
  rationale: string;
  suggested_route?: string;
  status: 'PENDING_OFFICER_REVIEW' | 'APPROVED' | 'REJECTED' | string;
}

export interface AIStructuredResponse {
  status: 'SUCCESS' | 'PARTIAL_CONTEXT' | 'FALLBACK';
  provider_used: string;
  model_used: string;
  recommendation: string;
  detailed_explanation: string;
  supporting_evidence: AISupportingEvidence[];
  proposed_actions: AIProposedAction[];
  identified_risks_and_limitations: string[];
  missing_or_stale_data_disclosures: string[];
  human_review_required: boolean;
  statutory_compliance_notice: string;
  is_mock_fallback?: boolean;
  execution_mode?: 'LIVE_LLM' | 'DETERMINISTIC_GROUNDED' | 'MOCK_FALLBACK' | 'MOCK_STANDALONE' | string;
  fallback_reason?: string;
  provider_status?: 'LIVE' | 'FALLBACK' | 'UNAVAILABLE' | string;
  grounding_status?: string;
  location?: string;
  data_timestamp?: string;
  audit_id: string;
  created_at: string;
}

export interface AIQueryRequest {
  query: string;
  context_modules?: string[];
  zone_code?: string;
  operator_name?: string;
  location_id?: string;
}

export interface AIProviderHealth {
  configured_provider: string;
  effective_provider: string;
  model: string;
  is_live_provider: boolean;
  provider_status?: 'LIVE' | 'MOCK' | 'UNAVAILABLE' | 'ERROR' | 'FALLBACK' | string;
  status_message?: string;
  configured_primary_provider?: string;
  configured_fallback_provider?: string;
  primary_status?: string;
  fallback_status?: string;
  fallback_model?: string;
  rate_limit_requests_per_minute: number;
  current_minute_requests: number;
  timeout_seconds: number;
  circuit_breaker_status: string;
  uptime_status: string;
}

export interface ActionReviewRequest {
  action_id: string;
  decision: 'APPROVED' | 'REJECTED';
  officer_name?: string;
  notes?: string;
}

export interface ActionReviewResponse {
  success: boolean;
  status: string;
  action_id: string;
  decision: string;
  reviewed_by?: string;
  audit_id?: string;
  audit_logged: boolean;
  statutory_form: string;
}

export const getDrillStatus = () => apiClient.get('/demo/drill/status');
export const loadDrillScenario = () => apiClient.post('/demo/drill/load');
export const runDrillScenario = (overrides?: any) => apiClient.post('/demo/drill/run', overrides || {});
export const resetDrillEnvironment = () => apiClient.post('/demo/drill/reset');
export const exportDrillDossier = () => apiClient.get('/demo/drill/export');

export const getProvidersHealth = () => apiClient.get('/health/providers');
export const getSystemMode = () => apiClient.get('/mode');
export const switchSystemMode = (data: any) => apiClient.post('/mode/switch', data);
export const getCurrentWeather = () => apiClient.get('/weather/current');
export const getWeatherForecast = () => apiClient.get('/weather/forecast');
export const getFloodGauges = (district?: string) =>
  apiClient.get('/flood/gauges', { params: district && district !== 'ALL' ? { district } : undefined });
export const postManualGaugeReading = (data: any) => apiClient.post('/flood/gauges/manual-entry', data);
export const getRoadClosures = () => apiClient.get('/roads/closures');
export const postRoadClosure = (data: any) => apiClient.post('/roads/closures', data);
export const calculateRealRoute = (data: any) => apiClient.post('/routes/real-route', data);
export const getHistoricalEvents = () => apiClient.get('/historical/events');
export const getHistoricalEventDetails = (id: string) => apiClient.get(`/historical/events/${id}`);
export const getAuditLogs = (limit = 50) => apiClient.get('/audit-logs', { params: { limit } });
export const verifyDemand = (id: string, data: any) => apiClient.post(`/demands/${id}/verify`, data);
export const dispatchDemand = (id: string, data: any) => apiClient.post(`/demands/${id}/dispatch`, data);

export const queryAiCopilot = (data: AIQueryRequest) => apiClient.post<AIStructuredResponse>('/ai/query', data);
export const getAiHealth = () => apiClient.get<AIProviderHealth>('/ai/health');
export const getAiContextPreview = (modules?: string, zoneCode?: string, locationId?: string) =>
  apiClient.get('/ai/context/preview', { params: { modules, zone_code: zoneCode, location_id: locationId } });
export const reviewAiAction = (data: ActionReviewRequest) =>
  apiClient.post<ActionReviewResponse>('/ai/actions/review', data);

// Risk Analysis Types
export interface DatasetAuditItem {
  dataset_name: string;
  source_agency: string;
  spatial_coverage: string;
  observation_timestamps: string;
  update_frequency: string;
  missing_data_handling: string;
  known_sensor_gaps: string;
  provenance_classification: string;
  quality_trust_tier: string;
  limitations: string;
}

export interface DatasetAuditResponse {
  audit_title: string;
  audited_at: string;
  total_datasets: number;
  datasets: DatasetAuditItem[];
  governance_compliance: string;
}

export interface RiskEngineWeights {
  weight_rainfall: number;
  weight_hydrology: number;
  weight_terrain: number;
  weight_drainage: number;
}

export interface FactorContribution {
  factor_name: string;
  raw_value: string;
  normalized_score_0_to_10: number;
  weight_applied: number;
  weighted_contribution: number;
  provenance: string;
}

export interface ZoneRiskAssessment {
  zone_code: string;
  zone_name: string;
  risk_score: number;
  risk_tier: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  scoring_method: 'RULE_BASED_BASELINE' | 'ML_RANDOM_FOREST' | 'ML_GRADIENT_BOOSTING' | 'FALLBACK_BASELINE';
  is_machine_learning: boolean;
  prediction_confidence?: number | null;
  class_probabilities?: Record<string, number> | null;
  fallback_applied: boolean;
  fallback_reason?: string | null;
  primary_driver: string;
  contributing_factors: FactorContribution[];
  affected_population: number;
  inundation_area_ha: number;
  water_depth_m?: number | null;
  data_freshness_label: string;
  limitations: string;
  statutory_warning: string;
}

export interface MLModelEvaluationMetrics {
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  brier_score_loss: number;
  confusion_matrix: number[][];
  classes: string[];
}

export interface MLModelMetadataResponse {
  model_name: string;
  model_version: string;
  algorithm: string;
  trained_at: string;
  training_sample_count: number;
  train_test_split_ratio: string;
  is_stratified_split: boolean;
  target_variable: string;
  feature_definitions: Array<{ name: string; description: string }>;
  feature_importances: Record<string, number>;
  evaluation_metrics: MLModelEvaluationMetrics;
  hyperparameters: Record<string, any>;
  required_data_for_future_hydrodynamic_model: string[];
}

export interface HistoricalComparisonItem {
  event_id: string;
  event_title: string;
  event_period: string;
  rainfall_24h_mm: number;
  peak_pandu_stage_m: number;
  inundation_extent_sq_km: number;
  displaced_population: number;
  comparison_notes: string;
}

export interface FloodRiskAnalysisResponse {
  analysis_id: string;
  evaluated_at: string;
  system_mode: string;
  active_method: 'RULE_BASED_BASELINE' | 'ML_RANDOM_FOREST' | 'ML_GRADIENT_BOOSTING' | 'FALLBACK_BASELINE';
  model_version?: string | null;
  citywide_summary: any;
  zone_assessments: ZoneRiskAssessment[];
  weights_applied: RiskEngineWeights;
  historical_comparisons: HistoricalComparisonItem[];
  governance_notice: string;
}

export interface RecalculateRiskRequest {
  weights?: RiskEngineWeights;
  force_baseline?: boolean;
  target_zone_code?: string;
  operator_name?: string;
}

export const getRiskDatasetAudit = () => apiClient.get<DatasetAuditResponse>('/risk/dataset-audit');
export const getFloodRiskAnalysis = (forceBaseline: boolean = false, zoneCode?: string) =>
  apiClient.get<FloodRiskAnalysisResponse>('/risk/analysis', {
    params: { force_baseline: forceBaseline, zone_code: zoneCode }
  });
export const recalculateFloodRisk = (data: RecalculateRiskRequest) =>
  apiClient.post<FloodRiskAnalysisResponse>('/risk/calculate', data);
export const getRiskModelMetadata = () => apiClient.get<MLModelMetadataResponse>('/risk/model-metadata');
export const getRiskDataRequirements = () => apiClient.get('/risk/data-requirements');

// =============================================================================
// AI-Assisted Resource Allocation & Logistics Advisor Types & Endpoints
// =============================================================================

export interface ShelterLinkInfo {
  shelter_code: string;
  shelter_name: string;
  location_desc: string;
  capacity: number;
  occupancy: number;
  status: string;
  allocated_food_kg: number;
  allocated_water_l: number;
}

export interface RouteSummaryInfo {
  vehicle_code: string;
  vehicle_name: string;
  vehicle_type: string;
  assigned_crew: string;
  radio_channel: string;
  total_distance_km: number;
  est_duration: string;
  route_profile: string;
  detour_enforced: boolean;
  detour_reason?: string | null;
  waypoints_count: number;
  polyline_coordinates: [number, number][];
}

export interface ZoneLogisticsRecommendation {
  zone_code: string;
  zone_name: string;
  risk_tier: string;
  severity_weight: number;
  population: number;
  food_demand_kg: number;
  water_demand_kg: number;
  total_demand_kg: number;
  alloc_food_kg: number;
  alloc_water_kg: number;
  total_alloc_kg: number;
  deficit_kg: number;
  fulfillment_pct: number;
  is_accessible: boolean;
  access_status: string;
  assigned_vehicles: string[];
  shelters: ShelterLinkInfo[];
  ai_allocation_rationale: string;
}

export interface BindingConstraintItem {
  constraint: string;
  type: string;
  description: string;
  affected_resource?: string | null;
}

export interface OperationalDiagnostics {
  binding_constraints: BindingConstraintItem[];
  missing_data_warnings: string[];
  unavailable_routes: string[];
  capacity_bottlenecks: string[];
  conflicting_inputs: string[];
  telemetry_freshness: Record<string, string>;
  data_trust_summary: string;
}

export interface AlternativeStrategyComparisonItem {
  strategy_id: string;
  strategy_name: string;
  is_recommended: boolean;
  priority_assumptions: string;
  total_allocated_kg: number;
  total_unmet_kg: number;
  coverage_ratio_pct: number;
  critical_zone_coverage_pct: number;
  est_transit_distance_km: number;
  est_fuel_burn_liters: number;
  solver_runtime_ms: number;
  solver_status: string;
  key_tradeoff: string;
  allocations_by_zone: Record<string, { food_kg: number; water_l: number; total_kg: number; deficit_kg: number }>;
}

export interface LogisticsAdvisorPlanResponse {
  plan_id: string;
  plan_version: string;
  generated_at: string;
  active_strategy: string;
  solver_engine: string;
  solver_runtime_ms: number;
  solver_status: string;
  total_available_stock_kg: number;
  available_food_kg: number;
  available_water_kg: number;
  total_fleet_capacity_kg: number;
  active_vehicles_count: number;
  total_demand_kg: number;
  total_allocated_kg: number;
  total_unmet_kg: number;
  coverage_ratio_pct: number;
  total_transit_distance_km: number;
  est_total_fuel_burn_liters: number;
  zones: ZoneLogisticsRecommendation[];
  routes: RouteSummaryInfo[];
  diagnostics: OperationalDiagnostics;
  ai_executive_briefing: string;
  review_status: string;
  review_details?: any;
  safety_disclaimer: string;
}

export interface WhatIfScenarioRequest {
  location_id?: string;
  scenario_title?: string;
  custom_stock_food_kg?: number;
  custom_stock_water_kg?: number;
  disabled_vehicles?: string[];
  severed_zones?: string[];
  demand_multiplier?: number;
  custom_zone_demand?: Record<string, { food_kg?: number; water_kg?: number }>;
  strategy?: string;
}

export interface WhatIfScenarioResponse {
  simulated_at: string;
  scenario_title: string;
  strategy_used: string;
  solver_status: string;
  solver_runtime_ms: number;
  baseline_allocated_kg: number;
  simulated_allocated_kg: number;
  allocated_delta_kg: number;
  baseline_unmet_kg: number;
  simulated_unmet_kg: number;
  unmet_delta_kg: number;
  baseline_distance_km: number;
  simulated_distance_km: number;
  distance_delta_km: number;
  feasibility_status: string;
  zones: any[];
  bottlenecks: string[];
  ai_impact_analysis: string;
  database_mutated: boolean;
  disclaimer: string;
}

export interface PlanReviewRequest {
  action: string;
  operator_name: string;
  review_notes: string;
  form_8b_reference?: string;
  disclaimer_acknowledged?: boolean;
}

export interface PlanReviewResponse {
  success: boolean;
  plan_id: string;
  review_status: string;
  action_recorded: string;
  operator_name: string;
  timestamp: string;
  audit_log_id: number;
  form_8b_reference: string;
  notes: string;
  operational_next_step: string;
}

export const getLogisticsPlan = (strategy: string = 'LEXICOGRAPHIC_SEVERITY_OPTIMAL') =>
  apiClient.get<LogisticsAdvisorPlanResponse>('/logistics-advisor/plan', { params: { strategy } });

export const getLogisticsStrategies = () =>
  apiClient.get<AlternativeStrategyComparisonItem[]>('/logistics-advisor/strategies');

export const simulateWhatIfScenario = (data: WhatIfScenarioRequest) =>
  apiClient.post<WhatIfScenarioResponse>('/logistics-advisor/what-if', data);

export const reviewLogisticsPlan = (data: PlanReviewRequest) =>
  apiClient.post<PlanReviewResponse>('/logistics-advisor/review', data);

// ==========================================
// Human-Approved Dispatch Workflow Types & API
// ==========================================

export interface SafetyValidationReport {
  is_safe: boolean;
  inventory_sufficient: boolean;
  vehicle_capacity_sufficient: boolean;
  routes_passable: boolean;
  warnings: string[];
  errors: string[];
  validated_at: string;
}

export interface DispatchOrderResponse {
  dispatch_id: string;
  plan_id: string;
  zone_code: string;
  zone_name: string;
  vehicle_code: string;
  vehicle_name: string;
  resource_type: string;
  food_quantity_kg: number;
  water_quantity_l: number;
  total_weight_kg: number;
  destination_desc: string;
  route_summary: string;
  transit_distance_km: number;
  detour_required: boolean;
  detour_reason?: string;
  status: 'PENDING' | 'APPROVED' | 'READY' | 'DISPATCHED' | 'DELIVERED' | 'CANCELLED' | 'REJECTED';
  is_dry_run: boolean;
  is_simulation: boolean;
  safety_validation: SafetyValidationReport;
  reviewed_by?: string;
  reviewed_at?: string;
  review_decision?: string;
  review_notes?: string;
  form_8b_reference: string;
  external_connector_status: string;
  allowed_next_transitions: string[];
  created_at: string;
  updated_at: string;
}

export interface DispatchReviewRequest {
  decision: 'APPROVED' | 'REJECTED';
  officer_name: string;
  notes: string;
  form_8b_reference?: string;
  disclaimer_acknowledged?: boolean;
}

export interface DispatchTransitionRequest {
  target_status: 'READY' | 'DISPATCHED' | 'DELIVERED' | 'CANCELLED';
  operator_name: string;
  notes?: string;
  form_8b_reference?: string;
}

export interface GenerateDispatchesFromPlanRequest {
  plan_id?: string;
  strategy?: string;
  is_dry_run?: boolean;
  operator_name?: string;
}

export const getDispatchOrders = async (params?: { status_filter?: string; zone_code?: string; is_dry_run?: boolean }): Promise<DispatchOrderResponse[]> => {
  const res = await apiClient.get<DispatchOrderResponse[]>('/dispatch/orders', { params });
  return res.data;
};

export const getDispatchOrder = async (dispatchId: string): Promise<DispatchOrderResponse> => {
  const res = await apiClient.get<DispatchOrderResponse>(`/dispatch/orders/${dispatchId}`);
  return res.data;
};

export const reviewDispatchOrder = async (dispatchId: string, data: DispatchReviewRequest): Promise<DispatchOrderResponse> => {
  const res = await apiClient.post<DispatchOrderResponse>(`/dispatch/orders/${dispatchId}/review`, data);
  return res.data;
};

export const transitionDispatchOrder = async (dispatchId: string, data: DispatchTransitionRequest): Promise<DispatchOrderResponse> => {
  const res = await apiClient.post<DispatchOrderResponse>(`/dispatch/orders/${dispatchId}/transition`, data);
  return res.data;
};

export const generateDispatchesFromPlan = async (data?: GenerateDispatchesFromPlanRequest): Promise<DispatchOrderResponse[]> => {
  const res = await apiClient.post<DispatchOrderResponse[]>('/dispatch/generate-from-plan', data || {});
  return res.data;
};

export const getDispatchSafetyCheck = async (params: { zone_code: string; vehicle_code: string; food_kg: number; water_l: number }): Promise<SafetyValidationReport> => {
  const res = await apiClient.get<SafetyValidationReport>('/dispatch/safety-check', { params });
  return res.data;
};

export interface IncidentItem {
  id: number;
  incident_id: string;
  incident_type: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  location_desc: string;
  latitude: number;
  longitude: number;
  zone_code: string;
  location_id: string;
  reported_by: string;
  reported_at: string;
  verified_by?: string;
  verified_at?: string;
  casualties_reported: number;
  persons_stranded: number;
  livestock_affected: number;
  infrastructure_damaged?: string;
  response_action_taken?: string;
  assigned_team?: string;
  updated_at: string;
}

export interface SituationReportItem {
  id: number;
  sitrep_id: string;
  report_date: string;
  time_window: string;
  district_name: string;
  location_id: string;
  active_human_lives_affected: number;
  displaced_in_shelters: number;
  inundated_villages_count: number;
  active_shelters_count: number;
  roads_closed_count: number;
  critical_river_stages: Array<{ station: string; river: string; stage_m?: number; danger_m?: number; status: string }>;
  weather_synopsis: string;
  relief_distributed_summary: Record<string, any>;
  active_incidents_count: number;
  compiling_officer: string;
  approving_commander?: string;
  approval_status: string;
  form_reference: string;
  created_at: string;
  approved_at?: string;
}

export interface StockMovementItem {
  movement_id: string;
  item_sku: string;
  item_name: string;
  depot_code: string;
  movement_type: string;
  quantity: number;
  unit: string;
  batch_lot_number: string;
  expiry_date?: string;
  balance_before: number;
  balance_after: number;
  reference_doc: string;
  operator_name: string;
  timestamp: string;
  notes?: string;
  location_id: string;
}

export interface InventoryAlertsReport {
  total_low_stock_alerts: number;
  total_near_expiry_alerts: number;
  alerts: Array<{
    type: string;
    severity: string;
    sku: string;
    name: string;
    current_available: number;
    unit: string;
    message: string;
  }>;
}

export interface SphereDemandReport {
  calculation_timestamp: string;
  standard_reference: string;
  location_id: string;
  input_parameters: Record<string, any>;
  sphere_per_capita_baselines: Record<string, any>;
  measured_shelter_demand: Record<string, any>;
  estimated_unregistered_demand: Record<string, any>;
  consolidated_humanitarian_requirement: Record<string, any>;
  horizon_breakdown: {
    "24_hours_immediate_kg": number;
    "72_hours_surge_kg": number;
    "7_days_sustenance_kg": number;
  };
  uncertainty_and_governance_notice: string;
}

export const getIncidents = async (params?: { status_filter?: string; severity_filter?: string }): Promise<IncidentItem[]> => {
  const res = await apiClient.get<IncidentItem[]>('/operational/incidents', { params });
  return res.data;
};

export const createIncident = async (data: Partial<IncidentItem>): Promise<IncidentItem> => {
  const res = await apiClient.post<IncidentItem>('/operational/incidents', data);
  return res.data;
};

export const updateIncident = async (incidentId: string, data: Partial<IncidentItem>): Promise<IncidentItem> => {
  const res = await apiClient.put<IncidentItem>(`/operational/incidents/${incidentId}`, data);
  return res.data;
};

export const getSituationReports = async (): Promise<SituationReportItem[]> => {
  const res = await apiClient.get<SituationReportItem[]>('/operational/sitreps');
  return res.data;
};

export const compileSituationReport = async (data?: { report_date?: string; time_window?: string; weather_synopsis?: string; compiling_officer?: string }): Promise<SituationReportItem> => {
  const res = await apiClient.post<SituationReportItem>('/operational/sitreps/generate', data || {});
  return res.data;
};

export const approveSituationReport = async (sitrepId: string, data: { approving_commander: string; notes?: string }): Promise<SituationReportItem> => {
  const res = await apiClient.put<SituationReportItem>(`/operational/sitreps/${sitrepId}/approve`, data);
  return res.data;
};

export const receiveStockConsignment = async (data: any): Promise<StockMovementItem> => {
  const res = await apiClient.post<StockMovementItem>('/operational/inventory/receipt', data);
  return res.data;
};

export const adjustStockQuantity = async (data: any): Promise<StockMovementItem> => {
  const res = await apiClient.post<StockMovementItem>('/operational/inventory/adjustment', data);
  return res.data;
};

export const reserveStockQuantity = async (data: any): Promise<StockMovementItem> => {
  const res = await apiClient.post<StockMovementItem>('/operational/inventory/reserve', data);
  return res.data;
};

export const getStockMovements = async (params?: { limit?: number; sku?: string }): Promise<StockMovementItem[]> => {
  const res = await apiClient.get<StockMovementItem[]>('/operational/inventory/movements', { params });
  return res.data;
};

export const getInventoryAlerts = async (): Promise<InventoryAlertsReport> => {
  const res = await apiClient.get<InventoryAlertsReport>('/operational/inventory/alerts');
  return res.data;
};

export const calculateSphereDemand = async (data: {
  population_affected: number;
  evacuees_in_shelters: number;
  time_horizon_hours: number;
  infant_count?: number;
  elderly_count?: number;
  contingency_buffer_pct?: number;
}): Promise<SphereDemandReport> => {
  const res = await apiClient.post<SphereDemandReport>('/operational/demand/sphere-calculate', data);
  return res.data;
};

export const getSphereStandardsInfo = async (): Promise<any> => {
  const res = await apiClient.get('/operational/demand/standards-info');
  return res.data;
};





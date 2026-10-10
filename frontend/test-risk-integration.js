/**
 * RELIEFOS Lite — Flood Risk Analysis Integration Test Suite
 * Validates dataset audits, transparent baseline MCDA, ML model evaluation metrics,
 * calibrated prediction confidence, historical event benchmarking, and statutory compliance.
 */

const API_BASE_URL = 'http://127.0.0.1:8013';

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => null);
  return { status: response.status, ok: response.ok, data };
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

async function runRiskTestSuite() {
  console.log('================================================================');
  console.log('RELIEFOS Lite — Evidence-Based Flood Risk Module Verification');
  console.log('================================================================\n');

  let passed = 0;
  let total = 0;

  async function test(name, fn) {
    total++;
    process.stdout.write(`TEST [${total}] ${name}... `);
    try {
      await fn();
      passed++;
      console.log('PASSED (OK)');
    } catch (err) {
      console.log('FAILED (ERR)');
      console.error('   ', err.message);
    }
  }

  // 1. Dataset audit endpoint
  await test('Operational Dataset Audit & Sensor Gap Verification', async () => {
    const res = await request('/api/risk/dataset-audit');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.data.total_datasets >= 4, 'Expected at least 4 datasets audited');
    assert(res.data.governance_compliance.includes('ISO-19115'), 'Must comply with ISO-19115 standard');

    const datasets = res.data.datasets;
    const names = datasets.map((d) => d.dataset_name);
    assert(names.some((n) => n.includes('Open-Meteo')), 'Must audit Open-Meteo');
    assert(names.some((n) => n.includes('CWC')), 'Must audit CWC Gauges');
    assert(names.some((n) => n.includes('Historical')), 'Must audit ASDMA Historical records');
    assert(names.some((n) => n.includes('Cadastral')), 'Must audit Cadastral Zones');

    for (const d of datasets) {
      assert(d.source_agency, 'Missing source_agency');
      assert(d.observation_timestamps, 'Missing observation_timestamps');
      assert(d.known_sensor_gaps, 'Missing known_sensor_gaps');
      assert(d.quality_trust_tier, 'Missing quality_trust_tier');
    }
  });

  // 2. Default live analysis (Calibrated ML Random Forest)
  await test('Live Flood Risk Analysis (Random Forest Inference & Calibration)', async () => {
    const res = await request('/api/risk/analysis');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    const { data } = res;

    assert(data.analysis_id.startsWith('RISK-EVAL-'), 'Invalid analysis ID');
    assert(data.zone_assessments.length === 5, 'Must assess all 5 Kamrup zones');
    assert(data.active_method === 'ML_RANDOM_FOREST', 'Expected ML_RANDOM_FOREST active method');

    // Citywide summary
    const summary = data.citywide_summary;
    assert(summary.total_monitored_sectors === 5, 'Expected 5 sectors');
    assert(summary.citywide_max_risk_score >= 0, 'Invalid max score');
    assert(summary.hydrometeorological_drivers.controlling_gauge, 'Missing controlling gauge');

    // Zone inspections
    for (const zone of data.zone_assessments) {
      assert(zone.zone_code, 'Missing zone code');
      assert(zone.zone_name, 'Missing zone name');
      assert(zone.risk_score >= 0.0 && zone.risk_score <= 10.0, 'Risk score must be in 0.0-10.0');
      assert(['LOW', 'MODERATE', 'HIGH', 'CRITICAL'].includes(zone.risk_tier), 'Invalid risk tier');
      assert(zone.is_machine_learning === true, 'ML flag must be true');
      assert(zone.prediction_confidence !== null && zone.prediction_confidence >= 0.0, 'Must have calibrated confidence');
      assert(zone.class_probabilities, 'Must provide class probabilities');
      assert(zone.contributing_factors.length === 4, 'Must provide 4 factor contributions');
      assert(zone.statutory_warning.includes('Relative vulnerability index'), 'Must include statutory warning');
    }
  });

  // 3. Transparent baseline override
  await test('Transparent Baseline Override (?force_baseline=true)', async () => {
    const res = await request('/api/risk/analysis?force_baseline=true');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    const { data } = res;

    assert(data.active_method === 'RULE_BASED_BASELINE', 'Expected RULE_BASED_BASELINE');
    for (const zone of data.zone_assessments) {
      assert(zone.is_machine_learning === false, 'is_machine_learning must be false in baseline mode');
      assert(zone.scoring_method === 'RULE_BASED_BASELINE', 'Scoring method must be RULE_BASED_BASELINE');
      assert(zone.prediction_confidence === null, 'Baseline must never fabricate ML confidence');
    }
  });

  // 4. Custom planner weights recalculation and audit logging
  await test('Planner Recalculation with Custom Weights & Audit Ledger', async () => {
    const res = await request('/api/risk/calculate', {
      method: 'POST',
      body: JSON.stringify({
        weights: {
          weight_rainfall: 0.40,
          weight_hydrology: 0.30,
          weight_terrain: 0.20,
          weight_drainage: 0.10,
        },
        force_baseline: true,
        operator_name: 'Insp. S. Sharma (EOC Planner)',
      }),
    });
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.data.active_method === 'RULE_BASED_BASELINE', 'Expected baseline calculation');

    // Verify audit log
    const auditRes = await request('/api/audit-logs?limit=5');
    assert(auditRes.status === 200, `Expected 200, got ${auditRes.status}`);
    const matching = auditRes.data.filter((l) => l.action === 'RECALCULATE_FLOOD_RISK');
    assert(matching.length >= 1, 'Must persist RECALCULATE_FLOOD_RISK in audit ledger');
  });

  // 5. ML Model architecture, evaluation metrics, and Brier calibration score
  await test('ML Model Architecture, Train/Test Split & Calibration Metrics', async () => {
    const res = await request('/api/risk/model-metadata');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    const { data } = res;

    assert(data.model_version.startsWith('v1.0'), 'Missing model version');
    assert(data.is_stratified_split === true, 'Must use stratified split');
    assert(data.training_sample_count >= 300, 'Must have at least 300 training samples');

    const metrics = data.evaluation_metrics;
    assert(metrics.accuracy >= 0.85, `Accuracy should be >= 0.85, got ${metrics.accuracy}`);
    assert(metrics.macro_f1 >= 0.80, `Macro F1 should be >= 0.80, got ${metrics.macro_f1}`);
    assert(metrics.brier_score_loss <= 0.30, `Brier score loss should be <= 0.30, got ${metrics.brier_score_loss}`);
    assert(metrics.confusion_matrix.length === 4, 'Confusion matrix must be 4x4');
    assert(Object.keys(data.feature_importances).length === 10, 'Must provide 10 feature importances');
  });

  // 6. Historical flood benchmarks comparison
  await test('Historical Flood Benchmark Comparison (2022 vs 2024 vs Live)', async () => {
    const res = await request('/api/risk/analysis');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    const comparisons = res.data.historical_comparisons;

    assert(comparisons.length >= 2, 'Expected at least 2 historical benchmark comparisons');
    const ids = comparisons.map((c) => c.event_id);
    assert(ids.includes('HIST-2022-GHY-MONSOON'), 'Must compare 2022 monsoon event');
    assert(ids.includes('HIST-2024-GHY-FLASH'), 'Must compare 2024 cloudburst event');

    for (const c of comparisons) {
      assert(c.rainfall_24h_mm > 0, 'Rainfall must be > 0');
      assert(c.peak_pandu_stage_m > 49.0, 'Pandu stage must be > 49.0');
      assert(c.comparison_notes.includes('river stage'), 'Must compare relative river stage delta');
    }
  });

  // 7. Future Hydrodynamic Data Roadmap
  await test('Roadmap Requirements for 2D Hydrodynamic Modeling', async () => {
    const res = await request('/api/risk/data-requirements');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    const reqs = res.data.requirements;

    assert(reqs.length >= 4, 'Must document at least 4 hydrodynamic modeling data requirements');
    const categories = reqs.map((r) => r.category);
    assert(categories.some((c) => c.includes('Topography') || c.includes('LiDAR')), 'Must specify LiDAR DEM');
    assert(categories.some((c) => c.includes('Bathymetry')), 'Must specify riverbed bathymetry');
    assert(categories.some((c) => c.includes('Conduit') || c.includes('Sewer')), 'Must specify stormwater conduits');
  });

  console.log('\n================================================================');
  console.log(`Summary: ${passed}/${total} risk checks passed successfully.`);
  console.log('================================================================\n');

  if (passed !== total) {
    process.exit(1);
  }
}

runRiskTestSuite().catch((err) => {
  console.error('Fatal test error:', err);
  process.exit(1);
});

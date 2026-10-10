/**
 * RELIEFOS Lite — AI-Assisted Resource Allocation & Logistics Advisor End-to-End Verification Suite
 * Executes live HTTP calls against the backend server on port 8013 to verify:
 * 1. Plan generation with OR-Tools CP-SAT and NetworkX/OSRM routes.
 * 2. Multi-strategy comparison across all 4 mathematical formulations.
 * 3. What-if scenario execution with strict in-memory simulation isolation.
 * 4. Severed route topology handling.
 * 5. Form 8B human review authorization and audit logging.
 * 6. Non-regression of Copilot and Flood Risk endpoints.
 */

import http from 'http';
import { URL } from 'url';

const BASE_URL = 'http://127.0.0.1:8013';

function request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed, headers: res.headers });
        } catch {
          resolve({ status: res.statusCode, raw: data, headers: res.headers });
        }
      });
    });

    req.on('error', (err) => reject(err));
    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

async function runLogisticsAdvisorVerification() {
  console.log('================================================================');
  console.log('RELIEFOS Lite — AI Logistics Advisor Full Verification Suite');
  console.log('================================================================\n');

  let passed = 0;
  let failed = 0;

  // Test 1: Plan Generation with OR-Tools and NetworkX
  try {
    process.stdout.write('TEST [1] OR-Tools Plan Generation & Fleet Route Topology... ');
    const res = await request('GET', '/api/logistics-advisor/plan?strategy=LEXICOGRAPHIC_SEVERITY_OPTIMAL');
    if (res.status === 200 && res.data.plan_id && res.data.solver_status in { OPTIMAL: 1, FEASIBLE: 1 }) {
      if (res.data.zones.length === 5 && res.data.routes.length >= 2 && res.data.diagnostics.binding_constraints.length > 0) {
        console.log('PASSED (OK)');
        passed++;
      } else {
        throw new Error(`Incomplete plan structure: zones=${res.data.zones.length}, routes=${res.data.routes.length}`);
      }
    } else {
      throw new Error(`Expected 200 OK, got ${res.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  // Test 2: Multi-Strategy Comparison Matrix
  try {
    process.stdout.write('TEST [2] Multi-Strategy Mathematical Comparison (4 Formulations)... ');
    const res = await request('GET', '/api/logistics-advisor/strategies');
    if (res.status === 200 && Array.isArray(res.data) && res.data.length === 4) {
      const stratIds = res.data.map((s) => s.strategy_id);
      if (
        stratIds.includes('LEXICOGRAPHIC_SEVERITY_OPTIMAL') &&
        stratIds.includes('PROPORTIONAL_EQUAL_SHARE') &&
        stratIds.includes('DISTANCE_MINIMIZING_PROXIMITY') &&
        stratIds.includes('WATER_FIRST_SURVIVAL')
      ) {
        const lex = res.data.find((s) => s.strategy_id === 'LEXICOGRAPHIC_SEVERITY_OPTIMAL');
        const prop = res.data.find((s) => s.strategy_id === 'PROPORTIONAL_EQUAL_SHARE');
        if (lex.is_recommended && lex.critical_zone_coverage_pct >= prop.critical_zone_coverage_pct) {
          console.log('PASSED (OK)');
          passed++;
        } else {
          throw new Error('Lexicographic strategy failed to dominate proportional in critical coverage');
        }
      } else {
        throw new Error('Missing expected strategy IDs');
      }
    } else {
      throw new Error(`Expected 200 with 4 strategies, got ${res.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  // Test 3: What-If Simulation Sandbox Isolation
  try {
    process.stdout.write('TEST [3] What-If Scenario Sandbox Execution & DB Isolation... ');
    const whatIfPayload = {
      scenario_title: 'Embankment Seepage Surge Test',
      custom_stock_food_kg: 5000.0,
      custom_stock_water_kg: 5000.0,
      disabled_vehicles: ['VH-03'],
      demand_multiplier: 1.3,
      strategy: 'LEXICOGRAPHIC_SEVERITY_OPTIMAL'
    };
    const res = await request('POST', '/api/logistics-advisor/what-if', whatIfPayload);
    if (res.status === 200 && res.data.database_mutated === false && res.data.feasibility_status === 'FEASIBLE') {
      if (typeof res.data.allocated_delta_kg === 'number' && typeof res.data.unmet_delta_kg === 'number') {
        console.log('PASSED (OK)');
        passed++;
      } else {
        throw new Error('Missing delta calculations in what-if output');
      }
    } else {
      throw new Error(`Expected 200 with DB isolation, got ${res.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  // Test 4: Severed Route Topology Simulation
  try {
    process.stdout.write('TEST [4] Severed Route Topology & Inundation Enforcements... ');
    const severedPayload = {
      scenario_title: 'Saraighat Severed Simulation',
      severed_zones: ['ZONE 01'],
      strategy: 'LEXICOGRAPHIC_SEVERITY_OPTIMAL'
    };
    const res = await request('POST', '/api/logistics-advisor/what-if', severedPayload);
    if (res.status === 200 && res.data.zones) {
      const z01 = res.data.zones.find((z) => z.zone_code === 'ZONE 01');
      if (z01 && z01.total_alloc_kg === 0 && z01.is_accessible === false) {
        console.log('PASSED (OK)');
        passed++;
      } else {
        throw new Error('Severed zone did not receive 0 kg allocation');
      }
    } else {
      throw new Error(`Expected 200, got ${res.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  // Test 5: Form 8B Human Review & Audit Logging
  try {
    process.stdout.write('TEST [5] Form 8B Human Review Sign-Off & SQLite Audit Logging... ');
    const reviewPayload = {
      action: 'APPROVE',
      operator_name: 'Insp. S. Sharma (EOC Planner)',
      review_notes: 'Verified against CWC Pandu level (49.68m). Authorized for staging at Sarusajai Hub.',
      form_8b_reference: 'ASDMA-F8B-2026-10-04-VERIF-01',
      disclaimer_acknowledged: true
    };
    const res = await request('POST', '/api/logistics-advisor/review', reviewPayload);
    if (res.status === 200 && res.data.success && res.data.review_status === 'APPROVED' && res.data.audit_log_id > 0) {
      // Check that plan reflects approved status
      const planRes = await request('GET', '/api/logistics-advisor/plan');
      if (planRes.status === 200 && planRes.data.review_status === 'APPROVED') {
        console.log('PASSED (OK)');
        passed++;
      } else {
        throw new Error('Plan did not reflect updated APPROVED status');
      }
    } else {
      throw new Error(`Expected 200 with audit ID, got ${res.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  // Test 6: Non-Regression Check on AI Copilot & Risk Endpoints
  try {
    process.stdout.write('TEST [6] Non-Regression on AI Copilot & Flood Risk Modules... ');
    const aiHealth = await request('GET', '/api/ai/health');
    const riskAudit = await request('GET', '/api/risk/dataset-audit');
    if (aiHealth.status === 200 && riskAudit.status === 200) {
      console.log('PASSED (OK)');
      passed++;
    } else {
      throw new Error(`Non-regression failed: aiHealth=${aiHealth.status}, riskAudit=${riskAudit.status}`);
    }
  } catch (err) {
    console.log(`FAILED (${err.message})`);
    failed++;
  }

  console.log('\n================================================================');
  console.log(`Summary: ${passed}/${passed + failed} logistics advisor checks passed successfully.`);
  console.log('================================================================\n');

  if (failed > 0) {
    process.exit(1);
  }
}

runLogisticsAdvisorVerification().catch((err) => {
  console.error('Fatal error running verification:', err);
  process.exit(1);
});

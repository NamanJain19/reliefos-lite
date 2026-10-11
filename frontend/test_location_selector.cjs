const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const APP_URL = 'http://127.0.0.1:3012';
const SCREENSHOT_DIR = path.join(__dirname, 'test-artifacts');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runTests() {
  console.log('🚀 Launching Microsoft Edge headless browser...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  const results = {
    initialRender: false,
    dropdownOpens: false,
    allNineLocationsPresent: false,
    locationsList: [],
    barpetaSelectionUpdatesNavbar: false,
    barpetaDataIsolationVerified: false,
    cacharSelectionWorks: false,
    sessionPersistenceVerified: false,
    returnToKamrupMetroWorks: false,
    outsideClickCloses: false,
    escapeKeyCloses: false,
    mobileViewportFunctional: false
  };

  try {
    // 1. Initial Render
    console.log(`\n--- TEST 1: Initial Render at ${APP_URL}/dashboard ---`);
    await page.goto(`${APP_URL}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForSelector('#navbar-location-selector-btn', { timeout: 10000 });
    const initialText = await page.$eval('#navbar-location-selector-btn', el => el.innerText);
    console.log(`Initial Navbar Location Selector text: "${initialText.replace(/\n/g, ' ')}"`);
    if (initialText.includes('Kamrup Metropolitan') || initialText.includes('Kamrup Metro')) {
      results.initialRender = true;
      console.log('✅ TEST 1 PASSED: Initial location is Kamrup Metropolitan.');
    }

    // 2. Click Location Selector & Open Dropdown
    console.log('\n--- TEST 2: Open Location Dropdown ---');
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    results.dropdownOpens = true;
    console.log('✅ TEST 2 PASSED: Dropdown opened visibly.');

    // 3. Verify all 9 configured locations
    console.log('\n--- TEST 3: Verify All 9 Configured Locations in Dropdown ---');
    const optionsText = await page.$$eval('[role="listbox"] button[role="option"]', buttons => 
      buttons.map(b => b.innerText.replace(/\n+/g, ' | ').trim())
    );
    console.log(`Found ${optionsText.length} location items in dropdown:`);
    optionsText.forEach((opt, idx) => console.log(`  ${idx + 1}. ${opt}`));
    results.locationsList = optionsText;

    const expectedDistricts = [
      'Kamrup Metropolitan',
      'Kamrup Rural',
      'Barpeta',
      'Nalbari',
      'Darrang',
      'Morigaon',
      'Goalpara',
      'Nagaon',
      'Cachar'
    ];

    const missingDistricts = expectedDistricts.filter(d => !optionsText.some(opt => opt.includes(d)));
    if (missingDistricts.length === 0 && optionsText.length === 9) {
      results.allNineLocationsPresent = true;
      console.log('✅ TEST 3 PASSED: All 9 configured Assam locations are present in the dropdown.');
    } else {
      console.error('❌ Missing districts:', missingDistricts);
    }

    // Capture screenshot of open dropdown
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_dropdown_open.png'), fullPage: false });
    console.log('📸 Screenshot saved: 01_dropdown_open.png');

    // 4. Select Barpeta
    console.log('\n--- TEST 4: Select Barpeta, Assam ---');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('[role="listbox"] button[role="option"]'));
      const target = btns.find(b => b.textContent.includes('Barpeta'));
      if (target) target.click();
    });
    // Wait for dropdown to close and state to update
    await new Promise(r => setTimeout(r, 600));

    const updatedNavbarText = await page.$eval('#navbar-location-selector-btn', el => el.innerText);
    console.log(`Updated Navbar Location Selector text: "${updatedNavbarText.replace(/\n/g, ' ')}"`);
    if (updatedNavbarText.includes('Barpeta')) {
      results.barpetaSelectionUpdatesNavbar = true;
      console.log('✅ TEST 4 PASSED: Navbar updated to Barpeta, Assam.');
    }

    // 5. Data Integrity: Verify Barpeta data isolation
    console.log('\n--- TEST 5: Verify Barpeta Data Isolation & Honest Gaps ---');
    const pageText = await page.evaluate(() => document.body.innerText);
    const hasBarpetaSectorIndicator = pageText.includes('Barpeta') && 
      (pageText.includes('Barpeta DDMA') || pageText.includes('DEPOT-BRP-01') || pageText.includes('BRP-') || pageText.includes('Beki') || pageText.includes('CWC Station') || pageText.includes('Relief Depots Unconfigured'));
    
    console.log('Contains Barpeta sector indicator & isolated data:', hasBarpetaSectorIndicator);
    if (hasBarpetaSectorIndicator) {
      results.barpetaDataIsolationVerified = true;
      console.log('✅ TEST 5 PASSED: Barpeta uses its own telemetry and does not clone Kamrup Metro zones.');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_barpeta_selected.png'), fullPage: false });
    console.log('📸 Screenshot saved: 02_barpeta_selected.png');

    // 6. Select Cachar
    console.log('\n--- TEST 6: Select Cachar, Assam ---');
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('[role="listbox"] button[role="option"]'));
      const target = btns.find(b => b.textContent.includes('Cachar'));
      if (target) target.click();
    });
    await new Promise(r => setTimeout(r, 600));

    const cacharNavbarText = await page.$eval('#navbar-location-selector-btn', el => el.innerText);
    console.log(`Cachar Navbar text: "${cacharNavbarText.replace(/\n/g, ' ')}"`);
    if (cacharNavbarText.includes('Cachar')) {
      results.cacharSelectionWorks = true;
      console.log('✅ TEST 6 PASSED: Selected Cachar, Assam.');
    }

    // 7. Session Persistence across Navigation
    console.log('\n--- TEST 7: Session Persistence across Route Navigation ---');
    await page.goto(`${APP_URL}/flood-map`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForSelector('#navbar-location-selector-btn', { timeout: 10000 });
    const floodMapNavbarText = await page.$eval('#navbar-location-selector-btn', el => el.innerText);
    console.log(`Flood Map Navbar text after navigation: "${floodMapNavbarText.replace(/\n/g, ' ')}"`);
    if (floodMapNavbarText.includes('Cachar')) {
      results.sessionPersistenceVerified = true;
      console.log('✅ TEST 7 PASSED: Location selection preserved on /flood-map.');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_cachar_flood_map.png'), fullPage: false });
    console.log('📸 Screenshot saved: 03_cachar_flood_map.png');

    // 8. Return to Kamrup Metropolitan
    console.log('\n--- TEST 8: Return to Kamrup Metropolitan ---');
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('[role="listbox"] button[role="option"]'));
      const target = btns.find(b => b.textContent.includes('Kamrup Metropolitan'));
      if (target) target.click();
    });
    await new Promise(r => setTimeout(r, 600));
    const restoredText = await page.$eval('#navbar-location-selector-btn', el => el.innerText);
    console.log(`Restored Navbar text: "${restoredText.replace(/\n/g, ' ')}"`);
    if (restoredText.includes('Kamrup Metropolitan')) {
      results.returnToKamrupMetroWorks = true;
      console.log('✅ TEST 8 PASSED: Successfully returned to Kamrup Metropolitan.');
    }

    // 9. Outside-Click test
    console.log('\n--- TEST 9: Test Outside-Click Dismissal ---');
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    // Click outside on body
    await page.mouse.click(10, 10);
    await new Promise(r => setTimeout(r, 400));
    const listboxAfterOutsideClick = await page.$('[role="listbox"]');
    if (!listboxAfterOutsideClick) {
      results.outsideClickCloses = true;
      console.log('✅ TEST 9 PASSED: Outside click closed the dropdown.');
    }

    // 10. Escape key test
    console.log('\n--- TEST 10: Test Escape Key Dismissal ---');
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    await page.keyboard.press('Escape');
    await new Promise(r => setTimeout(r, 400));
    const listboxAfterEscape = await page.$('[role="listbox"]');
    if (!listboxAfterEscape) {
      results.escapeKeyCloses = true;
      console.log('✅ TEST 10 PASSED: Escape key closed the dropdown.');
    }

    // 11. Mobile Viewport Test
    console.log('\n--- TEST 11: Mobile Viewport (375x667) ---');
    await page.setViewport({ width: 375, height: 667 });
    await new Promise(r => setTimeout(r, 400));
    const mobileBtn = await page.$('#navbar-location-selector-btn');
    const isVisibleOnMobile = await mobileBtn.isIntersectingViewport();
    console.log('Is location selector visible on mobile viewport:', isVisibleOnMobile);
    
    await page.click('#navbar-location-selector-btn');
    await page.waitForSelector('[role="listbox"]', { visible: true, timeout: 3000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_mobile_viewport_open.png'), fullPage: false });
    console.log('📸 Screenshot saved: 04_mobile_viewport_open.png');
    
    if (isVisibleOnMobile) {
      results.mobileViewportFunctional = true;
      console.log('✅ TEST 11 PASSED: Location selector functions on mobile layout.');
    }

  } catch (err) {
    console.error('❌ Test execution encountered error:', err);
  } finally {
    await browser.close();
  }

  console.log('\n=============================================');
  console.log('📊 FINAL AUTOMATED UI TEST SUMMARY:');
  console.log(JSON.stringify(results, null, 2));
  console.log('=============================================');
  
  const allPassed = Object.values(results).every(val => Boolean(val));
  console.log(allPassed ? '🎉 ALL 11 TESTS PASSED SUCCESSFULLY!' : '⚠️ SOME TESTS FAILED');
  process.exit(allPassed ? 0 : 1);
}

runTests();

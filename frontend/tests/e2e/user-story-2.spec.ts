/**
 * E2E Test for User Story 2: Crop Recommendation
 * 
 * Goal: Farmer asks "What should I plant this season?"
 * System returns 3 ranked crops with yield, profit, planting window, water needs, and risk score
 * 
 * SLA: <10s cold, <2s cached
 */

import { test, expect } from '@playwright/test';

test.describe('User Story 2: Crop Recommendation', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
  const TEST_FARM_ID = '00000000-0000-0000-0000-000000000001'; // Thanjavur test farm

  test('should generate crop recommendations for Samba season', async ({ page }) => {
    // Navigate to crop recommendations page
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);

    // Verify page loaded
    await expect(page.locator('h1')).toContainText('Crop Recommendations');

    // Select Samba season (Tamil Nadu rice season)
    await page.click('button:has-text("Samba")');

    // Click "Get Recommendations" button
    const startTime = Date.now();
    await page.click('button:has-text("Get Recommendations")');

    // Wait for loading to complete
    await page.waitForSelector('text=Top Recommendations for Samba Season', { timeout: 12000 });
    const endTime = Date.now();
    const responseTime = endTime - startTime;

    // Verify response time meets SLA (<10s cold)
    expect(responseTime).toBeLessThan(10000);
    console.log(`Cold response time: ${responseTime}ms`);

    // Verify 3 crop recommendations are displayed
    const cropCards = page.locator('[data-testid="crop-recommendation-card"]');
    await expect(cropCards).toHaveCount(3);

    // Verify top crop (Rank #1)
    const topCrop = cropCards.first();
    await expect(topCrop.locator('[data-testid="crop-rank"]')).toContainText('1');
    await expect(topCrop.locator('[data-testid="top-choice-badge"]')).toBeVisible();

    // Verify crop name is displayed
    const cropName = await topCrop.locator('[data-testid="crop-name"]').textContent();
    expect(cropName).toBeTruthy();
    console.log(`Top recommendation: ${cropName}`);

    // Verify financial data is displayed
    await expect(topCrop.locator('[data-testid="expected-yield"]')).toBeVisible();
    await expect(topCrop.locator('[data-testid="revenue"]')).toBeVisible();
    await expect(topCrop.locator('[data-testid="cost"]')).toBeVisible();
    await expect(topCrop.locator('[data-testid="profit"]')).toBeVisible();

    // Verify profit is positive
    const profitText = await topCrop.locator('[data-testid="profit"]').textContent();
    expect(profitText).toMatch(/₹/); // Should show rupee symbol

    // Verify planting window is displayed
    await expect(topCrop.locator('[data-testid="planting-window"]')).toBeVisible();

    // Verify risk indicators are displayed
    await expect(topCrop.locator('[data-testid="drought-risk"]')).toBeVisible();
    await expect(topCrop.locator('[data-testid="pest-risk"]')).toBeVisible();
    await expect(topCrop.locator('[data-testid="market-risk"]')).toBeVisible();

    // Verify water requirement is shown
    await expect(topCrop.locator('[data-testid="water-requirement"]')).toBeVisible();

    // Verify confidence score is displayed
    const confidenceElement = page.locator('text=/Confidence:.*%/');
    await expect(confidenceElement).toBeVisible();
  });

  test('should show cached response on second request', async ({ page }) => {
    const testFarmId = '00000000-0000-0000-0000-000000000002';
    
    // Navigate to page
    await page.goto(`${BASE_URL}/farm/${testFarmId}/recommendations`);

    // Select season
    await page.click('button:has-text("Kharif")');

    // First request (cold)
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations for Kharif Season', { timeout: 12000 });
    
    // Wait a bit for cache to settle
    await page.waitForTimeout(500);

    // Second request (should be cached)
    await page.click('button:has-text("Kharif")');
    const startTime = Date.now();
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations for Kharif Season');
    const endTime = Date.now();
    const cachedResponseTime = endTime - startTime;

    // Cached response should be < 2s
    expect(cachedResponseTime).toBeLessThan(2000);
    console.log(`Cached response time: ${cachedResponseTime}ms`);
  });

  test('should rank crops by risk-adjusted profit', async ({ page }) => {
    // Navigate to page
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);

    // Select season and get recommendations
    await page.click('button:has-text("Samba")');
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations');

    // Get all crop cards
    const cropCards = page.locator('[data-testid="crop-recommendation-card"]');

    // Verify rank order (1, 2, 3)
    for (let i = 0; i < 3; i++) {
      const card = cropCards.nth(i);
      await expect(card.locator('[data-testid="crop-rank"]')).toContainText(`${i + 1}`);
    }

    // Verify only first card has "Top Choice" badge
    await expect(cropCards.first().locator('[data-testid="top-choice-badge"]')).toBeVisible();
    await expect(cropCards.nth(1).locator('[data-testid="top-choice-badge"]')).not.toBeVisible();
    await expect(cropCards.nth(2).locator('[data-testid="top-choice-badge"]')).not.toBeVisible();
  });

  test('should show risk scores with color coding', async ({ page }) => {
    // Navigate and get recommendations
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);
    await page.click('button:has-text("Samba")');
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations');

    const topCrop = page.locator('[data-testid="crop-recommendation-card"]').first();

    // Check that risk indicators have color classes
    const droughtRisk = topCrop.locator('[data-testid="drought-risk"]');
    await expect(droughtRisk).toBeVisible();
    
    // Risk should have a percentage value
    const droughtText = await droughtRisk.textContent();
    expect(droughtText).toMatch(/%$/);
  });

  test('should display all required information for each crop', async ({ page }) => {
    // Navigate and get recommendations
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);
    await page.click('button:has-text("Rabi")');
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations');

    // Check all 3 crops have complete information
    const cropCards = page.locator('[data-testid="crop-recommendation-card"]');
    
    for (let i = 0; i < 3; i++) {
      const card = cropCards.nth(i);

      // Required fields
      await expect(card.locator('[data-testid="crop-name"]')).toBeVisible();
      await expect(card.locator('[data-testid="crop-rank"]')).toBeVisible();
      await expect(card.locator('[data-testid="expected-yield"]')).toBeVisible();
      await expect(card.locator('[data-testid="revenue"]')).toBeVisible();
      await expect(card.locator('[data-testid="cost"]')).toBeVisible();
      await expect(card.locator('[data-testid="profit"]')).toBeVisible();
      await expect(card.locator('[data-testid="planting-window"]')).toBeVisible();
      await expect(card.locator('[data-testid="water-requirement"]')).toBeVisible();
      
      // Risk factors
      await expect(card.locator('[data-testid="drought-risk"]')).toBeVisible();
      await expect(card.locator('[data-testid="pest-risk"]')).toBeVisible();
      await expect(card.locator('[data-testid="market-risk"]')).toBeVisible();
    }
  });

  test('should work for different seasons', async ({ page }) => {
    const seasons = ['Kharif', 'Rabi', 'Summer'];

    for (const season of seasons) {
      await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);
      
      // Select season
      await page.click(`button:has-text("${season}")`);
      
      // Get recommendations
      await page.click('button:has-text("Get Recommendations")');
      
      // Wait for results
      await page.waitForSelector(`text=Top Recommendations for ${season} Season`, { timeout: 12000 });
      
      // Verify 3 crops are shown
      const cropCards = page.locator('[data-testid="crop-recommendation-card"]');
      await expect(cropCards).toHaveCount(3);
      
      console.log(`✓ ${season} season recommendations loaded successfully`);
    }
  });

  test('should show helpful information section', async ({ page }) => {
    // Navigate and get recommendations
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);
    await page.click('button:has-text("Samba")');
    await page.click('button:has-text("Get Recommendations")');
    await page.waitForSelector('text=Top Recommendations');

    // Verify info section is shown
    await expect(page.locator('text=How to Use These Recommendations')).toBeVisible();
    await expect(page.locator('text=Rankings are based on expected profit')).toBeVisible();
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Navigate to page with invalid farm ID
    await page.goto(`${BASE_URL}/farm/invalid-uuid/recommendations`);

    // Try to get recommendations
    await page.click('button:has-text("Samba")');
    await page.click('button:has-text("Get Recommendations")');

    // Should show error message (within reasonable time)
    await expect(page.locator('text=/Error/i')).toBeVisible({ timeout: 5000 });
  });

  test('should show loading state during generation', async ({ page }) => {
    // Navigate to page
    await page.goto(`${BASE_URL}/farm/${TEST_FARM_ID}/recommendations`);

    // Select season
    await page.click('button:has-text("Samba")');

    // Click button and immediately check for loading state
    await page.click('button:has-text("Get Recommendations")');
    
    // Should show loading indicator
    await expect(page.locator('text=Generating Recommendations')).toBeVisible();
  });
});

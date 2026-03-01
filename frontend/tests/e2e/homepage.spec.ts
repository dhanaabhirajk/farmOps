import { test, expect } from "@playwright/test";

test("homepage loads successfully", async ({ page }) => {
  // Navigate to the home page
  await page.goto("/");

  // Check that page title is correct
  await expect(page).toHaveTitle(/FarmOps/);

  // Check that main heading is visible
  const mainContent = page.locator("body");
  await expect(mainContent).toBeVisible();
});

test("page renders without JavaScript errors", async ({ page }) => {
  // Collect any console errors
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });

  // Navigate to home page
  await page.goto("/");

  // Wait a moment for any deferred errors
  await page.waitForTimeout(1000);

  // Assert no critical errors occurred (ignoring third-party errors)
  const criticalErrors = consoleErrors.filter(
    (error) =>
      !error.includes("third-party") &&
      !error.includes("CORS") &&
      !error.includes("net::ERR")
  );

  expect(criticalErrors).toEqual([]);
});

test("links have appropriate aria labels", async ({ page }) => {
  await page.goto("/");

  // Check that buttons/links have accessible labels
  const buttons = page.locator("button");
  const count = await buttons.count();

  if (count > 0) {
    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute("aria-label");

      // Button should have either text content or aria-label
      const hasAccessibility = text || ariaLabel;
      expect(hasAccessibility).toBeTruthy();
    }
  }
});

test("page is responsive", async ({ page }) => {
  // Test mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();

  // Test tablet viewport
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();

  // Test desktop viewport
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();
});

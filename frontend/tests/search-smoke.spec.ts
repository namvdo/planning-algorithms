import { expect, test } from "@playwright/test";

test("runs forward search and steps through the trace", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /^Run$/ }).click();
  await expect(page.getByText(/Status/)).toBeVisible();
  await expect(page.getByText("Found")).toBeVisible();

  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await expect(page.getByText("Frame 1 of")).toBeVisible();

  await page.getByLabel("Next frame").click();
  await expect(page.getByText("Forward visited")).toBeVisible();
  await expect(page.getByTestId("grid-visualization")).toBeVisible();

  await page.getByRole("button", { name: /Run Code/ }).click();
  await expect(page.getByText("All judge cases passed")).toBeVisible();

  await expect(page.getByLabel("Toggle app theme")).toContainText("Light");
  await page.getByLabel("Toggle app theme").click();
  await expect(page.getByLabel("Toggle app theme")).toContainText("Dark");
});

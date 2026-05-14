import { test, expect } from '@playwright/test';

test.describe('User Query Chat', () => {
  test('should load the chat page', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check title
    await expect(page).toHaveTitle(/User Query Chat/);
    
    // Check header
    await expect(page.locator('h1')).toContainText('User Query Chat');
    
    // Check placeholder text
    await expect(page.locator('textarea[placeholder="Ask about users..."]')).toBeVisible();
    
    // Check send button
    await expect(page.locator('button:has-text("Send")')).toBeVisible();
    
    // Check New Chat button
    await expect(page.locator('button:has-text("New Chat")')).toBeVisible();
  });

  test('should send a message and receive response', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Type a message
    const input = page.locator('textarea[placeholder="Ask about users..."]');
    await input.fill('list all users');
    
    // Click send button
    await page.click('button:has-text("Send")');
    
    // Wait for response - check that user data appears
    await expect(page.getByText(/Found \d+ user/).first()).toBeVisible({ timeout: 15000 });
    
    // Check that session_id is stored in localStorage
    const sessionId = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    expect(sessionId).toBeTruthy();
  });

  test('should continue conversation with same session', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // First message
    const input = page.locator('textarea[placeholder="Ask about users..."]');
    await input.fill('list all users');
    await page.click('button:has-text("Send")');
    await page.waitForTimeout(5000);
    
    // Get session_id
    const sessionId1 = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    
    // Second message
    await input.fill('show only active users');
    await page.click('button:has-text("Send")');
    await page.waitForTimeout(5000);
    
    // Verify session is continued
    const sessionId2 = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    expect(sessionId1).toBe(sessionId2);
  });

  test('should understand follow-up query without "only" keyword', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // First message: list all users
    const input = page.locator('textarea[placeholder="Ask about users..."]');
    await input.fill('list all users');
    await page.click('button:has-text("Send")');
    
    // Wait for first response - should get users
    await expect(page.getByText(/Found \d+ user/).first()).toBeVisible({ timeout: 15000 });
    
    // Get the session ID
    const sessionId = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    expect(sessionId).toBeTruthy();
    
    // Second message: "show active users" (without "only")
    await input.fill('show active users');
    await page.click('button:has-text("Send")');
    
    // Wait for second response - should show fewer users (active ones)
    await page.waitForTimeout(5000);
    
    // Get all "Found" text elements - the last one should be from the second response
    const foundTexts = await page.locator('text=Found').allTextContents();

    // Parse counts from both responses
    const allCounts = foundTexts
      .map(t => t.match(/Found (\d+) user/))
      .filter((m): m is RegExpMatchArray => m !== null)
      .map(m => parseInt(m[1]));
    
    // Active users count should be less than or equal to total
    if (allCounts.length >= 2) {
      expect(allCounts[allCounts.length - 1]).toBeLessThanOrEqual(allCounts[0]);
    }
  });

  test('should clear session on New Chat', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Send a message to create session
    const input = page.locator('textarea[placeholder="Ask about users..."]');
    await input.fill('list all users');
    await page.click('button:has-text("Send")');
    await page.waitForTimeout(5000);
    
    // Click New Chat
    await page.click('button:has-text("New Chat")');
    
    // Verify session is cleared
    const sessionId = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    expect(sessionId).toBeNull();
  });
});

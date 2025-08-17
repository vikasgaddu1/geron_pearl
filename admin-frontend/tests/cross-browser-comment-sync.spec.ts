import { test, expect, Page, BrowserContext } from '@playwright/test';

/**
 * Cross-Browser Comment Badge Synchronization Test
 * 
 * This test verifies that when a comment is added in one browser,
 * the comment badges update in real-time in other browser windows
 * via WebSocket synchronization.
 */

test.describe('Cross-Browser Comment Badge Sync', () => {
  let context1: BrowserContext;
  let context2: BrowserContext;
  let page1: Page;
  let page2: Page;

  test.beforeAll(async ({ browser }) => {
    // Create two separate browser contexts (simulating different browsers)
    context1 = await browser.newContext({
      viewport: { width: 1200, height: 800 }
    });
    
    context2 = await browser.newContext({
      viewport: { width: 1200, height: 800 }
    });

    page1 = await context1.newPage();
    page2 = await context2.newPage();

    // Enable console logging for debugging
    page1.on('console', msg => console.log(`PAGE1: ${msg.text()}`));
    page2.on('console', msg => console.log(`PAGE2: ${msg.text()}`));
  });

  test.afterAll(async () => {
    await context1.close();
    await context2.close();
  });

  test('should sync comment badges across browsers in real-time', async () => {
    console.log('🧪 Starting cross-browser comment badge sync test...');

    // Step 1: Navigate both pages to PEARL
    console.log('📂 Navigating both browsers to PEARL...');
    await Promise.all([
      page1.goto('http://localhost:3838', { waitUntil: 'networkidle' }),
      page2.goto('http://localhost:3838', { waitUntil: 'networkidle' })
    ]);

    // Step 2: Wait for WebSocket connections to establish
    console.log('🔌 Waiting for WebSocket connections...');
    await Promise.all([
      page1.waitForFunction(() => {
        return window.pearlWebSocket && window.pearlWebSocket.isConnected();
      }, { timeout: 10000 }),
      page2.waitForFunction(() => {
        return window.pearlWebSocket && window.pearlWebSocket.isConnected();
      }, { timeout: 10000 })
    ]);

    console.log('✅ Both browsers connected to WebSocket');

    // Step 3: Navigate to Reporting Effort Tracker in both browsers
    console.log('📊 Navigating to Reporting Effort Tracker...');
    
    // Wait for navigation elements to load and try multiple selectors
    const trackerSelectors = [
      'a[data-value="reporting_effort_tracker"]',
      'a[href="#shiny-tab-reporting_effort_tracker"]', 
      'a[data-toggle="tab"][data-value="reporting_effort_tracker"]',
      '.nav-link[data-value="reporting_effort_tracker"]'
    ];
    
    let selectorFound = null;
    for (const selector of trackerSelectors) {
      try {
        await page1.waitForSelector(selector, { timeout: 2000 });
        selectorFound = selector;
        console.log(`✅ Found tab selector: ${selector}`);
        break;
      } catch (e) {
        console.log(`❌ Selector not found: ${selector}`);
      }
    }
    
    if (!selectorFound) {
      throw new Error('Could not find Reporting Effort Tracker tab selector');
    }
    
    await Promise.all([
      page1.click(selectorFound),
      page2.click(selectorFound)
    ]);

    // Wait for tables to load
    await Promise.all([
      page1.waitForSelector('.comment-badges', { timeout: 15000 }),
      page2.waitForSelector('.comment-badges', { timeout: 15000 })
    ]);

    console.log('✅ Reporting Effort Tracker loaded in both browsers');

    // Step 4: Find a tracker with a comment button and record initial badge state
    const trackerSelector = '.comment-add-btn[data-tracker-id]';
    await page1.waitForSelector(trackerSelector, { timeout: 10000 });
    
    const trackerId = await page1.getAttribute(trackerSelector, 'data-tracker-id');
    console.log(`🎯 Using tracker ID: ${trackerId}`);

    // Get initial badge content in both browsers
    const initialBadge1 = await page1.textContent(`#badges-${trackerId}`) || '';
    const initialBadge2 = await page2.textContent(`#badges-${trackerId}`) || '';
    
    console.log(`📊 Initial badges - Browser1: "${initialBadge1}", Browser2: "${initialBadge2}"`);

    // Step 5: Set up WebSocket event monitoring in page1
    await page1.evaluate(() => {
      window.testResults = {
        commentEventsReceived: 0,
        badgeUpdatesReceived: 0,
        lastEventData: null
      };

      // Monitor WebSocket comment events
      const originalHandleMessage = window.pearlWsClient?.handleMessage;
      if (originalHandleMessage) {
        window.pearlWsClient.handleMessage = function(data) {
          if (data.type && data.type.startsWith('comment_')) {
            window.testResults.commentEventsReceived++;
            window.testResults.lastEventData = data;
            console.log('🎯 TEST: Comment WebSocket event detected:', data.type, data.data?.tracker_id);
          }
          originalHandleMessage.call(this, data);
        };
      }

      // Monitor badge update messages
      const originalHandler = window.Shiny?.addCustomMessageHandler;
      if (originalHandler) {
        // Intercept updateCommentBadgeRealtime messages
        window.addEventListener('message', (event) => {
          if (event.data && event.data.type === 'updateCommentBadgeRealtime') {
            window.testResults.badgeUpdatesReceived++;
            console.log('🔄 TEST: Badge update message received:', event.data);
          }
        });
      }
    });

    // Step 6: Add a comment in page2 (second browser)
    console.log('💬 Adding comment in second browser...');
    const testComment = `Cross-browser test comment ${Date.now()}`;
    
    // Click the comment add button
    await page2.click(`[data-tracker-id="${trackerId}"]`);
    
    // Wait for comment form to appear and fill it out
    await page2.waitForSelector(`#comment-text-${trackerId}`, { timeout: 5000 });
    await page2.fill(`#comment-text-${trackerId}`, testComment);
    await page2.selectOption(`#comment-type-${trackerId}`, 'qc_comment');
    
    // Submit the comment
    await page2.click(`#submit-comment-${trackerId}`);

    console.log('✅ Comment submitted in second browser');

    // Step 7: Wait for WebSocket events to propagate
    console.log('⏱️ Waiting for WebSocket event propagation...');
    
    // Wait for comment event in page1
    await page1.waitForFunction(() => {
      return window.testResults && window.testResults.commentEventsReceived > 0;
    }, { timeout: 10000 });

    // Step 8: Verify badge updates in page1 (first browser)
    console.log('🔍 Checking badge updates in first browser...');
    
    // Wait a bit for badge updates to process
    await page1.waitForTimeout(2000);

    // Get updated badge content
    const updatedBadge1 = await page1.textContent(`#badges-${trackerId}`) || '';
    const updatedBadge2 = await page2.textContent(`#badges-${trackerId}`) || '';

    console.log(`📊 Updated badges - Browser1: "${updatedBadge1}", Browser2: "${updatedBadge2}"`);

    // Step 9: Verify test results
    const testResults = await page1.evaluate(() => window.testResults);
    
    console.log('🧪 Test Results:');
    console.log(`   Comment Events Received: ${testResults.commentEventsReceived}`);
    console.log(`   Badge Updates Received: ${testResults.badgeUpdatesReceived}`);
    console.log(`   Last Event Tracker ID: ${testResults.lastEventData?.data?.tracker_id}`);

    // Assertions
    expect(testResults.commentEventsReceived).toBeGreaterThan(0);
    expect(testResults.lastEventData?.data?.tracker_id).toBe(parseInt(trackerId));
    expect(testResults.lastEventData?.data?.comment_text).toBe(testComment);

    // Verify badge content changed (should show unaddressed comment count)
    expect(updatedBadge1).not.toBe(initialBadge1);
    expect(updatedBadge2).not.toBe(initialBadge2);
    
    // Both badges should contain warning indicators for unaddressed comments
    expect(updatedBadge1).toContain('1'); // Should show count of 1
    expect(updatedBadge2).toContain('1'); // Should show count of 1

    console.log('✅ Cross-browser comment badge synchronization test PASSED!');
  });

  test('should handle WebSocket connection failures gracefully', async () => {
    console.log('🧪 Testing WebSocket connection failure handling...');

    // Navigate to PEARL
    await page1.goto('http://localhost:3838', { waitUntil: 'networkidle' });

    // Wait for initial WebSocket connection
    await page1.waitForFunction(() => {
      return window.pearlWebSocket && window.pearlWebSocket.isConnected();
    }, { timeout: 10000 });

    // Force disconnect WebSocket
    await page1.evaluate(() => {
      if (window.pearlWsClient) {
        window.pearlWsClient.close();
      } else if (window.pearlWebSocket && window.pearlWebSocket.disconnect) {
        window.pearlWebSocket.disconnect();
      }
    });

    // Wait a moment
    await page1.waitForTimeout(1000);

    // Check status
    const isConnected = await page1.evaluate(() => {
      return window.pearlWebSocket ? window.pearlWebSocket.isConnected() : false;
    });

    expect(isConnected).toBe(false);

    // Try to reconnect
    await page1.evaluate(() => {
      if (window.pearlWsClient) {
        window.pearlWsClient.connect();
      } else if (window.pearlWebSocket && window.pearlWebSocket.connect) {
        window.pearlWebSocket.connect();
      }
    });

    // Wait for reconnection
    await page1.waitForFunction(() => {
      return window.pearlWebSocket && window.pearlWebSocket.isConnected();
    }, { timeout: 10000 });

    console.log('✅ WebSocket reconnection test PASSED!');
  });

  test('should show debug information correctly', async () => {
    console.log('🧪 Testing WebSocket debug functions...');

    await page1.goto('http://localhost:3838', { waitUntil: 'networkidle' });

    // Wait for WebSocket connection
    await page1.waitForFunction(() => {
      return window.pearlWebSocket && window.pearlWebSocket.isConnected();
    }, { timeout: 10000 });

    // Test debug functions
    const statusResult = await page1.evaluate(() => {
      if (typeof window.checkWebSocketStatus === 'function') {
        window.checkWebSocketStatus();
        return 'function_available';
      }
      return 'function_missing';
    });

    expect(statusResult).toBe('function_available');

    const helpResult = await page1.evaluate(() => {
      if (typeof window.showWebSocketDebugHelp === 'function') {
        window.showWebSocketDebugHelp();
        return 'help_available';
      }
      return 'help_missing';
    });

    expect(helpResult).toBe('help_available');

    console.log('✅ WebSocket debug functions test PASSED!');
  });
});

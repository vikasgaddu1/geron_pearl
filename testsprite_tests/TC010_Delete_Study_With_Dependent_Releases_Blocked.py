import asyncio
from playwright import async_api

async def run_test():
    pw = None
    browser = None
    context = None
    
    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()
        
        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )
        
        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)
        
        # Open a new page in the browser context
        page = await context.new_page()
        
        # Navigate to your target URL and wait until the network request is committed
        await page.goto("http://localhost:3838", wait_until="commit", timeout=10000)
        
        # Wait for the main page to reach DOMContentLoaded state (optional for stability)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
        except async_api.Error:
            pass
        
        # Iterate through all iframes and wait for them to load as well
        for frame in page.frames:
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=3000)
            except async_api.Error:
                pass
        
        # Interact with the page elements to simulate user flow
        # Click on the 'Studies' tab to view studies and find one with linked database releases
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to Database Releases tab to find database releases linked to studies
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li[2]/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Send DELETE request to http://localhost:8000/api/v1/studies/test-study-for-db-release-1754602485052 and verify response
        await page.goto('http://localhost:8000/api/v1/studies/test-study-for-db-release-1754602485052', timeout=10000)
        

        # Click on 'Database Releases' tab to find linked database releases and identify the integer study_id for the study
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li[2]/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click on 'Studies' tab to find the integer study_id for 'test-study-for-db-release-1754602485052'
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Send GET request to /api/v1/studies to retrieve studies with their integer IDs and find the ID for 'test-study-for-db-release-1754602485052'
        await page.goto('http://localhost:8000/api/v1/studies', timeout=10000)
        

        # Send DELETE request to /api/v1/studies/{study_id} and verify HTTP 400 and error message
        study_id = 'test-study-for-db-release-1754602485052'
        response = await page.request.delete(f'http://localhost:8000/api/v1/studies/{study_id}')
        assert response.status == 400, f'Expected status 400, got {response.status}'
        json_response = await response.json()
        error_message = json_response.get('error') or json_response.get('message') or ''
        assert 'dependent database releases' in error_message.lower() or 'linked database releases' in error_message.lower(), f'Error message does not indicate deletion is blocked due to dependent database releases: {error_message}'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    
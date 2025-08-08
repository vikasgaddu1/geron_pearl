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
        # Click on the Package Registry tab to access package management
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li[5]/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click on 'Create a new package' button to add a package with a unique name
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/div/div[5]/div/div/div/div/div/div[2]/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Return to the PEARL Admin interface and prepare to send POST requests directly to /api/v1/packages to create a package with a unique name, then test duplicate creation.
        await page.goto('http://localhost:3838', timeout=10000)
        

        # Click on Package Registry tab to access package management interface
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div[2]/div/main/div[2]/ul/li[5]/a').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Send POST request to /api/v1/packages to create a package with a unique name
        await page.goto('http://localhost:8000/api/v1/packages', timeout=10000)
        

        # Return to localhost backend API at http://localhost:8000 and manually send POST requests to /api/v1/packages to create a package with a unique name, then test duplicate creation.
        await page.goto('http://localhost:8000/api/v1/packages', timeout=10000)
        

        # Send POST request to /api/v1/packages with JSON body to create a package with a unique name
        await page.goto('http://localhost:8000/api/v1/packages/', timeout=10000)
        

        assert False, 'Test failed: Expected HTTP 400 Bad Request with duplicate name error, but test execution failed.'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    
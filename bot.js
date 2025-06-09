const puppeteer = require('puppeteer');
const fs = require('fs');

// Function for sleep
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runBot(instanceId) {
  // Add initial delay based on instance ID to prevent race conditions
  await sleep(instanceId * 1000); // 1 second delay between each instance
  
  console.log(`\n[Instance ${instanceId}] Starting...`);
  
  // Load config from bot_config.json
  let config;
  try {
    config = JSON.parse(fs.readFileSync('./bot_config.json', 'utf8'));
    console.log(`[Instance ${instanceId}] Config loaded:`, {
      threadId: config.threadId,
      messagesPerSecond: config.messagesPerSecond,
      // totalMessages: config.totalMessages // totalMessages might not be used in bot.js
    });
  } catch (error) {
    console.error(`[Instance ${instanceId}] Error loading bot_config.json:`, error.message);
    return; // Stop if config loading fails
  }

  let browser;
  try {
    browser = await puppeteer.launch({ 
      headless: true,
      defaultViewport: null,
      args: [
        '--start-maximized',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--disable-notifications',
        '--disable-extensions',
        '--disable-default-apps',
        '--disable-popup-blocking',
        '--disable-background-networking',
        '--disable-backgrounding-occluded-windows',
        '--disable-breakpad',
        '--disable-component-extensions-with-background-pages',
        '--disable-ipc-flooding-protection',
        '--force-color-profile=srgb',
        '--metrics-recording-only',
        '--mute-audio',
        '--disable-features=site-per-process,IsolateOrigins,site-per-process-probing',
        '--disable-site-isolation-trials',
        '--disable-web-security',
        '--disable-features=RendererCodeIntegrity',
        '--autoplay-policy=no-user-gesture-required',
        '--disable-background-timer-throttling',
        '--disable-background-video',
        '--disable-translate',
        '--disable-sync',
        '--disable-client-side-phishing-detection'
      ]
    });
    const page = await browser.newPage();

    // Set timeout
    page.setDefaultNavigationTimeout(120000); // Increase to 2 minutes
    page.setDefaultTimeout(120000);

    // Enable CSS loading (but we will block some parts for speed)
    await page.setRequestInterception(true);
    page.on('request', (request) => {
      if (['image', 'font', 'media', 'stylesheet', 'other'].includes(request.resourceType())) { // บล็อกทรัพยากรที่ไม่จำเป็นรวมถึง CSS
        request.abort();
      } else {
        request.continue();
      }
    });

    // Set user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Load cookies from sessions/cookies.json
    console.log(`[Instance ${instanceId}] Loading cookies from sessions/cookies.json...`);
    let cookies;
    try {
      cookies = JSON.parse(fs.readFileSync(`./sessions/cookies.json`, 'utf8'));
      
      // Show partial cookies for security
      console.log(`[Instance ${instanceId}] Using cookies (partial):`, {
        c_user: cookies.find(c => c.name === 'c_user')?.value,
        xs: cookies.find(c => c.name === 'xs')?.value?.substring(0, 10) + '...', // Show first 10 characters
        fr: cookies.find(c => c.name === 'fr')?.value?.substring(0, 10) + '...'  // Show first 10 characters
      });

      await page.setCookie(...cookies);
      console.log(`[Instance ${instanceId}] Cookies loaded successfully`);

    } catch (error) {
      console.error(`[Instance ${instanceId}] Error loading sessions/cookies.json:`, error.message);
      throw new Error(
        'Failed to load cookies. Please check sessions/cookies.json.\n' +
        'Steps to fix:\n' +
        '1. Open Facebook in Chrome\n' +
        '2. Press F12 to open Developer Tools\n' +
        '3. Go to Application tab > Cookies > https://www.facebook.com\n' +
        '4. Copy these cookies: c_user, xs, fr, datr, sb\n' +
        '5. Update sessions/cookies.json with new values' // Notify user to update cookies.json
      );
    }

    // Navigate to Messenger
    console.log(`[Instance ${instanceId}] Navigating to Messenger...`);
    
    // Try loading the page multiple times if it fails
    let retryCount = 0;
    const maxRetries = 5; // Increase number of retries
    let navigationSuccess = false;
    
    while (retryCount < maxRetries) {
      try {
        console.log(`[Instance ${instanceId}] Navigation attempt ${retryCount + 1}/${maxRetries}`);
        await page.goto(`https://www.facebook.com/messages/t/${config.threadId}`, {
          waitUntil: ['domcontentloaded', 'networkidle2'], // Try using networkidle2
          timeout: 60000
        });

        // Check URL after navigation
        const currentUrl = page.url();
        console.log(`[Instance ${instanceId}] After navigation, current URL: ${currentUrl}`);

        // Check if we are on the expected Messenger or Facebook page
        if (currentUrl.includes('messages/t/') || currentUrl === 'https://www.facebook.com/' || currentUrl.includes('messenger.com')) {
             // Add a small delay after loading the main Messenger page
            await sleep(5000); // Wait 5 seconds for the page to load partially
             // Check if the chat input is ready
            const chatInputReady = await page.evaluate(() => {
              return !!document.querySelector('div[contenteditable="true"]');
            });

            if (chatInputReady) {
                console.log(`[Instance ${instanceId}] Page seems ready, chat input found.`);
                navigationSuccess = true;
                break; // Navigate and page seems ready
            } else {
                 console.log(`[Instance ${instanceId}] Page loaded, but chat input not found.`);
            }

        } else {
           console.log(`[Instance ${instanceId}] Did not land on expected Messenger or Facebook page.`);
        }

      } catch (error) {
        console.log(`[Instance ${instanceId}] Navigation attempt ${retryCount + 1} failed:`, error.message);
        // Try reload if error might be fixed by reload
        if (error.message.includes('Navigation timeout') || error.message.includes('net::')) {
             console.log(`[Instance ${instanceId}] Navigation timed out or network error, attempting reload.`);
             await page.reload({ waitUntil: ['domcontentloaded', 'networkidle2'] }); // Try reload
             await sleep(5000); // Wait after reload
        } else {
             console.log(`[Instance ${instanceId}] Other error, waiting before retry.`);
             await sleep(5000); // Wait before retry
        }
      }

      retryCount++;
      if (retryCount === maxRetries) {
        throw new Error(`Failed to navigate to Messenger after ${maxRetries} attempts.`);
      }
    }

    if (!navigationSuccess) {
         throw new Error('Navigation failed to reach a usable Messenger page.');
    }

    // Check login status
    console.log(`[Instance ${instanceId}] Checking login status after successful navigation...`);
    // No need to wait for sleep here because we've already waited after navigation

    // Check multiple conditions with retries
    let loggedInCheckRetries = 0;
    const maxLoggedInCheckRetries = 3;
    let loginStatus = { isLoggedIn: false };

    while (loggedInCheckRetries < maxLoggedInCheckRetries) {
      await sleep(2000); // Wait 2 seconds before checking in each round (increased from 1 to 2)
      loginStatus = await page.evaluate(() => {
        const hasLoginForm = !!document.querySelector('input[name="email"]');
        const hasMessenger = !!document.querySelector('[role="main"]');
        const hasChatInput = !!document.querySelector('div[contenteditable="true"]');
        // Add other checks to indicate successful login to Messenger, such as search bar or chat list
        const hasSearchBar = !!document.querySelector('input[aria-label="ค้นหา Messenger"]');
        const hasChatList = !!document.querySelector('[role="navigation"] [aria-label="แชท"]');
        // Check for more specific Messenger components, such as send button or chat room name
        const hasSendButton = !!document.querySelector('i[data-visualcompletion="css-img"][aria-label="กดเพื่อส่ง"]');
        const hasThreadName = !!document.querySelector('span[data-testid="screen-reader-text"]') || !!document.querySelector('div[role="main"] span[dir="auto"]');

        return {
          hasLoginForm,
          hasMessenger,
          hasChatInput,
          hasSearchBar,
          hasChatList,
          hasSendButton,
          hasThreadName,
          isLoggedIn: !hasLoginForm && (hasMessenger || (hasChatInput && hasSearchBar && hasChatList && hasSendButton && hasThreadName))
        };
      });

      console.log(`[Instance ${instanceId}] Attempt ${loggedInCheckRetries + 1} Login status:`, loginStatus);

      if (loginStatus.isLoggedIn) {
        break; // Login successful, exit loop
      }

      loggedInCheckRetries++;
      if (loggedInCheckRetries < maxLoggedInCheckRetries) {
        console.log(`[Instance ${instanceId}] Login check failed, retrying in 2 seconds...`);
        await sleep(2000); // Wait 2 seconds before retrying
      }
    }

    if (!loginStatus.isLoggedIn) {
      throw new Error(
        'Not logged in. Please check cookies.\n' +
        'Steps to fix:\n' +
        '1. Open Facebook in Chrome\n' +
        '2. Press F12 to open Developer Tools\n' +
        '3. Go to Application tab > Cookies > https://www.facebook.com\n' +
        '4. Copy these cookies: c_user, xs, fr, datr, sb\n' +
        '5. Update sessions/cookies.json with new values' // Notify user to update cookies.json
      );
    }
    console.log(`[Instance ${instanceId}] Login verified`);

    // Wait for message input field to be ready
    console.log(`[Instance ${instanceId}] Waiting for message input...`);
    await page.waitForSelector('div[contenteditable="true"]', { timeout: 10000 });
    console.log(`[Instance ${instanceId}] Message input ready`);

    // Send messages according to config
    console.log(`[Instance ${instanceId}] Starting to send messages...`);
    const delay = config.delay / 1000; // Use delay from config (ms) and convert to seconds for sleep
    const totalMessages = 1000; // Currently no totalMessages in config, set default value
    
    // Send messages quickly
    for (let i = 0; i < totalMessages; i++) {
      try {
        // Click the message input field first
        await page.click('div[contenteditable="true"]');
        await sleep(100); // Wait 100 milliseconds

        // Type the message
        await page.keyboard.type(config.message); // Use message from config
        await sleep(100); // Wait 100 milliseconds

        // Press Enter
        await page.keyboard.press('Enter');
        
        console.log(`[Instance ${instanceId}] Message ${i + 1}/${totalMessages} sent`);
        await sleep(delay); // Use delay from config
      } catch (error) {
        console.error(`[Instance ${instanceId}] Error sending message ${i + 1}:`, error.message);
        // Try to wait and resend
        await sleep(1000); // Wait 1 second
        i--; // Try to resend the same message again
        continue;
      }
    }

    console.log(`[Instance ${instanceId}] All messages sent successfully!`);
  } catch (error) {
    console.error(`[Instance ${instanceId}] Fatal error:`, error.message);
    // Don't throw error, let process finish by itself
  } finally {
    if (browser) {
      console.log(`[Instance ${instanceId}] Closing browser...`);
      await browser.close();
      console.log(`[Instance ${instanceId}] Browser closed`);
    }
  }
}

// bot.js will be called directly with node, so we will use process.argv to receive instanceId (if any)
// or run a single instance if no argument

const instanceId = process.argv[2] ? parseInt(process.argv[2]) : 1; // receive instanceId from argument 3

// We will run only 1 instance from gui.py and let bot.js manage the instance internally
// แต่โครงสร้างเดิมของคุณ bot.js ถูกออกแบบให้รับ instanceId
// เพื่อให้ง่ายในการแก้ปัญหาตอนนี้ เราจะรันแค่ instance เดียวใน bot.js
// ถ้าต้องการหลาย instances ต้องปรับโครงสร้างการรันใน gui.py และ bot.js ใหม่

runBot(instanceId); // Call runBot with instanceId

// ถ้าต้องการให้รองรับหลาย instances ที่รันพร้อมกันจริงๆ ต้องมีการประสานงานระหว่าง process มากกว่านี้
// เช่น การจัดการ port หรือ profile data แยกกันสำหรับแต่ละ instance

// ส่วนที่เคยอ่าน config และ cookies จาก arguments จะถูกลบออกไป
// process.argv[2] น่าจะเป็น config (JSON string)
// process.argv[3] น่าจะเป็น cookies (JSON string)
// ไม่ต้องใช้แล้ว เพราะเราจะอ่านจากไฟล์แทน

module.exports = runBot; 
# Facebook Messenger Auto Sender

Automated message sending tool for Facebook Messenger with an easy-to-use GUI

## System Requirements
- Node.js (tested on version 16+)
- Python 3.6+
- Stable internet connection

## Installation
1. Clone or download this project
2. Install dependencies:
   ```
   npm install
   ```

## Configuration
1. Create a `sessions/cookies.json` file with your Facebook cookies:
   - Open Facebook in your browser
   - Press F12 to open Developer Tools
   - Go to Application tab > Cookies > https://www.facebook.com
   - Copy these cookies: c_user, xs, fr
   - Add them to cookies.json in the required format

## How to Use
There are three ways to run this bot:

1. **Using the GUI (Recommended)**:
   ```
   python gui.py
   ```
   - Fill in the form with your message, Thread ID, messages per second, and number of instances
   - Click START to begin sending messages

2. **Single Instance Mode**:
   ```
   node bot.js
   ```
   - This runs a single bot instance using settings from bot_config.json

3. **Multiple Instance Mode**:
   ```
   node index.js
   ```
   - This runs multiple bot instances as configured in bot_config.json

Before running, make sure to:
- Update your Facebook cookies in sessions/cookies.json
- Set your desired message and thread ID in config.json or bot_config.json
- Adjust message frequency and instance count as needed

## How to Find Thread ID
1. Open a conversation in Facebook Messenger in your browser
2. The URL will have this format: `https://www.facebook.com/messages/t/[THREAD_ID]`
3. Copy the [THREAD_ID] from the URL

## Notes
- Using bots may violate Facebook's Terms of Service
- Use responsibly and at your own risk
- Not recommended to send many messages in a short period to avoid being blocked

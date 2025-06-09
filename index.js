const { fork } = require('child_process');
const config = require('./config.json');
const path = require('path');

// check if sessions folder exists
const fs = require('fs');
if (!fs.existsSync('./sessions')) {
  fs.mkdirSync('./sessions');
}

// check if cookies.json exists
if (!fs.existsSync('./sessions/cookies.json')) {
  console.error('Error: cookies.json not found in sessions folder!');
  console.log('Please create sessions/cookies.json with your Facebook cookies');
  process.exit(1);
}

console.log('Starting Facebook Messenger Bot with multiple instances...');
console.log(`Number of instances: ${config.instances}`);
console.log(`Messages per second: ${config.messagesPerSecond}`);
console.log(`Total messages per instance: ${config.totalMessages}`);
console.log('----------------------------------------');

// store active instances
const activeInstances = new Set();
let hasError = false;

// start each instance
for (let i = 0; i < config.instances; i++) {
  const child = fork(path.join(__dirname, 'process.js'));
  activeInstances.add(child);
  
  // send data to instance
  child.send({ id: i, config });
  
  // receive data from instance
  child.on('message', (message) => {
    console.log(`[Instance ${i}] ${message}`);
  });
  
  // handle error
  child.on('error', (error) => {
    console.error(`[Instance ${i}] Error:`, error);
    activeInstances.delete(child);
    hasError = true;
  });
  
  // handle process exit
  child.on('exit', (code) => {
    activeInstances.delete(child);
    if (code !== 0) {
      console.error(`[Instance ${i}] Exited with code ${code}`);
      hasError = true;
    } else {
      console.log(`[Instance ${i}] Completed successfully`);
    }
    
    // handle program exit
    if (activeInstances.size === 0) {
      console.log('All instances completed');
      if (hasError) {
        console.log('\nSome instances encountered errors. Please check the logs above.');
        console.log('If the error is about cookies, try:');
        console.log('1. Log in to Facebook in your browser');
        console.log('2. Get new cookies from Developer Tools (F12) > Application > Cookies');
        console.log('3. Update the cookies in sessions/cookies.json');
        process.exit(1);
      } else {
        process.exit(0);
      }
    }
  });
}

// handle program exit
process.on('SIGINT', () => {
  console.log('\nShutting down all instances...');
  for (const child of activeInstances) {
    child.kill();
  }
  process.exit(0);
});

const runBot = require('./bot');

process.on('message', async ({ id, config }) => {
  try {
    // send message to parent process
    process.send(`Starting bot with config: ${JSON.stringify(config)}`);
    
    // run bot
    await runBot(id, config);
    
    // send message to parent process
    process.send('Bot completed successfully');
  } catch (error) {
    // send error message to parent process
    process.send(`Error: ${error.message}`);
    process.exit(1);
  }
});

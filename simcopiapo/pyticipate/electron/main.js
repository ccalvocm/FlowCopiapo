const {app, BrowserWindow} = require('electron');

let mainWindow;

app.on('window-all-closed', function() {
  if (process.platform != 'darwin')
    app.quit();
});

app.on('ready', function() {
  
  mainWindow = new BrowserWindow(
    {
      fullscreen: true,
      show: true,
      width: 1920,
      height: 1200,
      webPreferences: {
          nodeIntergration: false,
          sandbox: false
      }
    }
  );
  
  mainWindow.on('closed', function() {
    mainWindow = null;
  });
  
  mainWindow.once('ready-to-show', () => { mainWindow.show() })
  
  mainWindow.loadURL('http://localhost:5000/');
});
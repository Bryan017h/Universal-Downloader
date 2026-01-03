const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 700,
    title: "Universal Downloader",
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// --- THE BRIDGE ---
ipcMain.on('start-download', async (event, args) => {
  const { url, mode, res, audio_fmt, use_hb, hb_preset, trim_on, t_start, t_end } = args;

  // 1. Path to Python Script (Step out of 'frontend' into 'backend')
  const scriptPath = path.join(__dirname, '..', 'backend', 'cli.py');

  // 2. Ask for Download Folder
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Select Download Folder'
  });
  if (result.canceled) return;
  const folder = result.filePaths[0];

  // 3. Build Arguments
  const cliArgs = [
    scriptPath,
    url,
    '--folder', folder,
    '--mode', mode,
    '--res', res,
    '--audio_fmt', audio_fmt,
    '--hb_preset', hb_preset
  ];

  if (use_hb) cliArgs.push('--use_hb');
  if (trim_on) {
    cliArgs.push('--trim_on');
    cliArgs.push('--trim_start', t_start);
    cliArgs.push('--trim_end', t_end);
  }

  console.log("Running:", 'python', cliArgs.join(' '));

  // 4. Spawn Python
  const child = spawn('python', cliArgs);

  // 5. Forward Output to UI
  child.stdout.on('data', (data) => {
    const lines = data.toString().split('\n');
    lines.forEach(line => {
      if (!line.trim()) return;
      try {
        const json = JSON.parse(line);
        mainWindow.webContents.send('python-output', json);
      } catch (e) {
        console.log("Raw:", line);
      }
    });
  });

  child.stderr.on('data', (data) => {
    console.error(`Error: ${data}`);
    // Don't send stderr to UI to avoid showing logs
  });
});
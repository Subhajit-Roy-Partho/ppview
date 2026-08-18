#!/usr/bin/env node

// Headless image generator for PPView.
//
// Drives a real instance of the app (dev server + headless Chrome via Puppeteer)
// through the window.__PPVIEW_CLI__ control API exposed by src/App.js, so the
// rendered PNG is pixel-identical to what a user would see/screenshot by hand.

const { parseArgs } = require('node:util');
const path = require('node:path');
const fs = require('node:fs');
const http = require('node:http');
const { spawn } = require('node:child_process');

const puppeteer = require('puppeteer');

const REPO_ROOT = path.resolve(__dirname, '..');

const HELP = `
PPView CLI image generator

Renders a topology/trajectory (or a self-contained .mgl file) headlessly and
saves a PNG screenshot of the 3D scene, using PPView's own renderer.

Usage:
  node cli/generate-image.js --top system.top --traj last_conf.dat -o out.png [options]
  node cli/generate-image.js --mgl system.mgl -o out.png [options]
  npm run generate-image -- --top system.top --traj last_conf.dat -o out.png

Input files:
  --top <path>            Topology file (Lorenzo/Flavio/Raspberry/SRS/PSP2/PHB/oxDNA .top or .phb)
  --traj <path>           Trajectory file (.dat/.traj/.conf). Auto-detected if omitted.
  --input <path>          oxDNA input file (PATCHY_radius / particle_file / patchy_file / interaction_type)
  --file <path>           Extra companion file, repeatable (e.g. particles.txt, patches.txt)
  --mgl <path>            Self-contained .mgl file (use instead of --top/--traj)

Output:
  -o, --output <path>     Output PNG path (default: ./ppview-output.png)
  --width <n>             Image width in pixels (default: 1920)
  --height <n>            Image height in pixels (default: 1080)
  --background <value>    CSS color (e.g. "#101014") or "transparent" (default: scene default)

Trajectory:
  --frame <n>             Trajectory frame / config index, 0-based (default: 0)

Camera:
  --camera-position <x,y,z>   Camera position
  --camera-target <x,y,z>     Point the camera (and orbit controls) looks at
  --fov <n>                    Perspective camera field of view, in degrees
  --zoom <n>                   Camera zoom factor

Scene:
  --box                    Show the simulation box wireframe
  --backdrop               Show backdrop reference planes
  --no-axis                Hide the coordinate axis (shown by default)
  --color-scheme <name>    muted | bright | pastel | scientific | colorblind | viridis | oxview

Server:
  --port <n>               Dev server port to use/spawn (default: 3000)
  --url <url>               Use an already-running PPView instance instead of --port
  --keep-server             Don't stop a dev server this script spawned
  --timeout <ms>            Max time to wait for each loading step (default: 120000)
  --headed                  Run a visible browser window (debugging)
  -h, --help                Show this help
`;

function parseVec3(str, flagName) {
  const parts = str.split(',').map((s) => parseFloat(s.trim()));
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    fail(`${flagName} expects "x,y,z", got "${str}"`);
  }
  return parts;
}

function parseFloatArg(str, flagName) {
  const n = parseFloat(str);
  if (Number.isNaN(n)) fail(`${flagName} expects a number, got "${str}"`);
  return n;
}

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

function isServerUp(url) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      res.resume();
      resolve(true);
    });
    req.setTimeout(1500, () => {
      req.destroy();
      resolve(false);
    });
    req.on('error', () => resolve(false));
  });
}

async function waitForServer(url, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isServerUp(url)) return;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`Timed out waiting for dev server at ${url}`);
}

function spawnDevServer(port) {
  const child = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['start'], {
    cwd: REPO_ROOT,
    env: { ...process.env, PORT: String(port), BROWSER: 'none' },
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: process.platform !== 'win32',
  });
  child.stdout.on('data', () => {}); // swallow CRA's noisy compile output
  child.stderr.on('data', (chunk) => {
    const text = chunk.toString();
    if (/error/i.test(text)) process.stderr.write(`[dev-server] ${text}`);
  });
  // Detached + unref'd: with --keep-server this process must be able to exit
  // on its own without waiting around for (or accidentally killing) the server.
  child.unref();
  return child;
}

function stopProcessTree(child) {
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/f', '/t']);
    return;
  }
  try {
    process.kill(-child.pid, 'SIGTERM');
  } catch (err) {
    child.kill('SIGTERM');
  }
}

async function main() {
  const { values } = parseArgs({
    options: {
      top: { type: 'string' },
      traj: { type: 'string' },
      input: { type: 'string' },
      file: { type: 'string', multiple: true, default: [] },
      mgl: { type: 'string' },
      output: { type: 'string', short: 'o', default: 'ppview-output.png' },
      width: { type: 'string', default: '1920' },
      height: { type: 'string', default: '1080' },
      background: { type: 'string' },
      frame: { type: 'string', default: '0' },
      'camera-position': { type: 'string' },
      'camera-target': { type: 'string' },
      fov: { type: 'string' },
      zoom: { type: 'string' },
      box: { type: 'boolean', default: false },
      backdrop: { type: 'boolean', default: false },
      'no-axis': { type: 'boolean', default: false },
      'color-scheme': { type: 'string' },
      port: { type: 'string', default: '3000' },
      url: { type: 'string' },
      'keep-server': { type: 'boolean', default: false },
      timeout: { type: 'string', default: '120000' },
      headed: { type: 'boolean', default: false },
      help: { type: 'boolean', short: 'h', default: false },
    },
  });

  if (values.help) {
    console.log(HELP);
    return;
  }

  if (!values.mgl && !values.top) {
    console.error(HELP);
    fail('provide either --mgl <file> or --top <file> (with --traj).');
  }

  const width = parseInt(values.width, 10);
  const height = parseInt(values.height, 10);
  const frame = parseInt(values.frame, 10);
  const timeoutMs = parseInt(values.timeout, 10);
  const port = parseInt(values.port, 10);

  const filePaths = [];
  if (values.mgl) filePaths.push(values.mgl);
  if (values.top) filePaths.push(values.top);
  if (values.traj) filePaths.push(values.traj);
  if (values.input) filePaths.push(values.input);
  for (const f of values.file) filePaths.push(f);

  for (const p of filePaths) {
    if (!fs.existsSync(p)) fail(`file not found: ${p}`);
  }

  const fileData = filePaths.map((p) => ({
    name: path.basename(p),
    base64: fs.readFileSync(p).toString('base64'),
  }));

  const camera = {};
  if (values['camera-position']) camera.position = parseVec3(values['camera-position'], '--camera-position');
  if (values['camera-target']) camera.target = parseVec3(values['camera-target'], '--camera-target');
  if (values.fov) camera.fov = parseFloatArg(values.fov, '--fov');
  if (values.zoom) camera.zoom = parseFloatArg(values.zoom, '--zoom');

  const viewSettings = {
    Box: !!values.box,
    BackdropPlanes: !!values.backdrop,
    CoordinateAxis: !values['no-axis'],
  };
  if (values['color-scheme']) viewSettings.ColorScheme = values['color-scheme'];

  const captureOptions = {};
  if (values.background) captureOptions.background = values.background;

  let serverProcess = null;
  let ownsServer = false;
  let serverUrl = values.url;

  try {
    if (!serverUrl) {
      const candidateUrl = `http://localhost:${port}`;
      if (await isServerUp(candidateUrl)) {
        console.log(`Using already-running server at ${candidateUrl}`);
        serverUrl = candidateUrl;
      } else {
        console.log(`Starting dev server on port ${port} (first run can take a minute)...`);
        serverProcess = spawnDevServer(port);
        ownsServer = true;
        serverUrl = candidateUrl;
        await waitForServer(candidateUrl, timeoutMs);
        console.log('Dev server is up.');
      }
    }

    let browser = null;
    try {
      console.log('Launching headless browser...');
      browser = await puppeteer.launch({
        headless: values.headed ? false : true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
      });

      const page = await browser.newPage();
      page.on('console', (msg) => {
        if (msg.type() === 'error') console.error('[browser]', msg.text());
      });
      page.on('pageerror', (err) => console.error('[browser page error]', err.message));
      page.on('dialog', async (dialog) => {
        console.error(`[browser alert] ${dialog.message()}`);
        await dialog.dismiss();
      });

      await page.setViewport({ width, height, deviceScaleFactor: 1 });

      console.log(`Loading ${serverUrl} ...`);
      await page.goto(serverUrl, { waitUntil: 'networkidle0', timeout: timeoutMs });

      await page.waitForFunction(() => !!window.__PPVIEW_CLI__, { timeout: timeoutMs });

      console.log(`Loading ${fileData.length} file(s): ${fileData.map((f) => f.name).join(', ')}`);
      await page.evaluate(async (files) => {
        const reconstructed = files.map((f) => {
          const binary = atob(f.base64);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
          return new File([bytes], f.name);
        });
        await window.__PPVIEW_CLI__.loadFiles(reconstructed);
      }, fileData);

      await page.waitForFunction(() => window.__PPVIEW_CLI__.isReady(), { timeout: timeoutMs });

      const state = await page.evaluate(() => window.__PPVIEW_CLI__.getState());
      console.log(`Loaded ${state.particleCount} particle(s), ${state.totalConfigs} frame(s).`);

      // The app's default camera is a fixed [100, 0, 0], which only looks reasonable
      // for a system roughly that size. Auto-frame the structure unless the caller
      // gave an explicit camera position/target, so a plain `--top/--traj` run
      // produces a sensible image instead of a speck in a blank canvas.
      if (!camera.position && !camera.target && state.bounds) {
        const { min, max, center } = state.bounds;
        const radius = state.particleRadius || 0.5;
        // Pad the particle-center bounding box by the particle radius so spheres
        // (and their patches) are fully inside the frame, not just their centers.
        const extent = Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2], 1) + radius * 4;
        const fovDeg = camera.fov || 45;
        const distance = (extent / 2 / Math.tan((fovDeg * Math.PI) / 360)) * 1.35;
        const dir = [1, 0.6, 1];
        const dirLen = Math.hypot(...dir);
        camera.position = dir.map((d, i) => center[i] + (d / dirLen) * distance);
        camera.target = center;
      }

      if (frame > 0) {
        if (frame >= state.totalConfigs) {
          throw new Error(`--frame ${frame} is out of range (0-${Math.max(state.totalConfigs - 1, 0)}).`);
        }
        console.log(`Seeking to frame ${frame}...`);
        await page.evaluate((f) => window.__PPVIEW_CLI__.setConfigIndex(f), frame);
        await page.waitForFunction(
          (f) => window.__PPVIEW_CLI__.getState().currentConfigIndex === f,
          { timeout: timeoutMs },
          frame,
        );
      }

      await page.evaluate((settings) => window.__PPVIEW_CLI__.setViewSettings(settings), viewSettings);

      if (Object.keys(camera).length > 0) {
        console.log('Applying camera settings...');
        const applied = await page.evaluate((cam) => window.__PPVIEW_CLI__.setCamera(cam), camera);
        if (!applied) console.warn('Warning: camera settings could not be applied (scene not ready).');
      }

      // Let orbit-controls damping / the demand render loop settle before capturing.
      await new Promise((resolve) => setTimeout(resolve, 800));

      console.log('Capturing image...');
      const dataURL = await page.evaluate((opts) => window.__PPVIEW_CLI__.captureImage(opts), captureOptions);

      const base64 = dataURL.replace(/^data:image\/png;base64,/, '');
      const outputPath = path.resolve(process.cwd(), values.output);
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, Buffer.from(base64, 'base64'));
      console.log(`Saved ${outputPath}`);
    } finally {
      if (browser) await browser.close();
    }
  } finally {
    if (serverProcess && ownsServer && !values['keep-server']) {
      console.log('Stopping dev server...');
      stopProcessTree(serverProcess);
    }
  }
}

main()
  .catch((err) => {
    console.error('Error:', err && err.message ? err.message : err);
    process.exitCode = 1;
  })
  .finally(() => {
    // Belt-and-suspenders: force exit so no lingering handle (a detached dev
    // server, a stray Chrome process, an open socket) can keep this alive.
    process.exit(process.exitCode || 0);
  });

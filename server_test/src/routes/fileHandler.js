import { stat } from 'fs/promises';

export async function waitForFilesStable(filePaths, timeout = 3000) {
  const start = Date.now();

  while (true) {
    let allReady = true;

    for (const p of filePaths) {
      try {
        const s = await stat(p);
        if (s.size === 0) {
          allReady = false;
          break;
        }
      } catch {
        allReady = false;
        break;
      }
    }

    if (allReady) return;

    if (Date.now() - start > timeout) {
      throw new Error('Timeout waiting for files to be written');
    }

    await new Promise(r => setTimeout(r, 50));
  }
}

import {spawn} from 'child_process';
import { resolve, join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname =  dirname(__filename);
const projectRoot = resolve(__dirname, '../../..');     
const panoramaStitcherPath = join(projectRoot, 'panorama_stitcher');

export const panoramaProcess = () => {
    return new Promise((resolve, reject) => {
        let stdoutData = '';
        let stderrData = '';

        const pythonProcess = spawn('python3', [join(panoramaStitcherPath, 'main.py')]);
        
        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            stdoutData += output;
            console.log(`Python stdout: ${output}`);
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const output = data.toString();
            stderrData += output;
            console.error(`Python stderr: ${output}`);
        });
        
        pythonProcess.on('error', (error) => {
            console.error(`Failed to start Python process: ${error.message}`);
            reject({
                reason: `Failed to start Python process: ${error.message}`,
                code: -1,
                stdout: stdoutData,
                stderr: stderrData
            });
        });
        
        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            
            if (code === 0) {
                // Try to parse the JSON result from stdout
                try {
                    const jsonMatch = stdoutData.match(/\{.*"result".*\}/);
                    if (jsonMatch) {
                        const result = JSON.parse(jsonMatch[0]);
                        console.log('Stitching result:', result);
                    }
                } catch (e) {
                    console.warn('Could not parse Python output as JSON');
                }
                resolve(code);
                return;
            }
            
            // Parse error from Python output
            let errorReason = `Process exited with code ${code}`;
            try {
                const jsonMatch = stdoutData.match(/\{.*"result".*\}/);
                if (jsonMatch) {
                    const result = JSON.parse(jsonMatch[0]);
                    if (result.reason) {
                        errorReason = result.reason;
                    }
                }
            } catch (e) {
                // If we can't parse JSON, check for DLASCL error in stderr
                if (stderrData.includes('DLASCL')) {
                    errorReason = 'LAPACK error (DLASCL): Invalid image data or dimensions. Images may be corrupted, too small, or lack features for stitching.';
                } else if (stderrData.trim()) {
                    errorReason = stderrData.trim();
                }
            }
            
            reject({
                reason: errorReason,
                code: code,
                stdout: stdoutData,
                stderr: stderrData
            });
        });
    });
}

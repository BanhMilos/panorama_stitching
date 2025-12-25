import {spawn} from 'child_process';
import { resolve, join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname =  dirname(__filename);
const projectRoot = resolve(__dirname, '../../..');     
const panoramaStitcherPath = join(projectRoot, 'panorama_stitcher');
export const panoramaProcess = () => {
    return new Promise((resolve, reject) => {

        const pythonProcess = spawn('python3', [join(panoramaStitcherPath, 'main.py'), {}]);
        
        pythonProcess.stdout.on('data', (data) => {
            console.log(`Output: ${data}`);
        });
        
        pythonProcess.stderr.on('data', (data) => {
            console.error(`Output: ${data}`);
        });
        
        pythonProcess.on('close', (code) => {
            console.log(`Process exited with code ${code}`);
            if (code === 0){
                resolve(code);
                return;
            }
            reject(code);
        });
    });
}

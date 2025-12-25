import { Router } from 'express';
import multer, { diskStorage } from 'multer';
import { resolve, join, dirname } from 'path';
import { existsSync, mkdirSync, readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { waitForFilesStable } from './fileHandler.js';
import { panoramaProcess }from '../panorama/panoramaProcess.js';

const router = Router();    

// Set up multer for file uploads. Multer sound unintuitive af
const __filename = fileURLToPath(import.meta.url);
const __dirname =  dirname(__filename);
const projectRoot = resolve(__dirname, '../../..'); 
const uploadDir = join(projectRoot, 'unconverted');
const outputDir = join(projectRoot, 'output');
if (!existsSync(uploadDir)) mkdirSync(uploadDir, { recursive: true });

const storage = diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir); 
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({ storage: storage });

router.post('', upload.array('files', 50), async (req, res) => {
    console.log(`Received upload request ${req}`);
    if (!req.files || req.files.length === 0) {
        return res.status(400).send('No files were uploaded.');
    }

    const filePaths = req.files.map(file => file.path);
    console.log('Uploaded files:', filePaths.length);
    try {
        await waitForFilesStable(filePaths, 5000);
        await panoramaProcess();       
        const outputData = readFileSync(join(outputDir, 'panorama.jpg')).toString('base64');
        return res.status(200).json({
            message: 'Panorama stitched successfully',
            data: outputData
        });
    } catch (error) {
        return res.json({
            result : 'failed',
            message: error.reason,
            reason: error.reason,
        });
    }
});

export default router;
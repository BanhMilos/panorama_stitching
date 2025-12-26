import express, { json, urlencoded } from 'express';
import uploadRoutes from './routes/upload.js';
import multer from 'multer';
import { resolve, join } from 'path';
import { existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware for parsing JSON and urlencoded data
app.use(json());
app.use(urlencoded({ extended: true }));

// Setup for uploadOne
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '../..');
const uploadDir = join(projectRoot, 'unconverted');
if (!existsSync(uploadDir)) mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage: storage });

// Route to handle multiple uploads with panorama processing
app.use('/uploadMany', uploadRoutes);

// Route to handle single file upload without processing
app.post('/uploadOne', upload.single('file'), async (req, res) => {
  console.log(`Received upload request ${req}`);
    if (!req.file) {
        return res.status(400).json({
            result: 'failed'
        });
    }
    
    return res.status(200).json({
        result: 'success'
    });
});

app.get('/test', (req, res) => {
  res.json({
    status: 'success',
    message: 'Server is running and connected',
    timestamp: new Date().toISOString()
  });
});


// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

export default app;
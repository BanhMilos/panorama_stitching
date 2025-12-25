import express, { json, urlencoded } from 'express';
import uploadRoutes from './routes/upload.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware for parsing JSON and urlencoded data
app.use(json());
app.use(urlencoded({ extended: true }));

// Route to handle multiple uploads
app.use('/upload', uploadRoutes);

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
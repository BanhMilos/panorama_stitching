const fs = require('fs');
const path = require('path');

const uploadsDir = path.join(__dirname, '../../uploads');

const saveFile = (file) => {
    const filePath = path.join(uploadsDir, file.originalname);
    return new Promise((resolve, reject) => {
        fs.writeFile(filePath, file.buffer, (err) => {
            if (err) {
                return reject(err);
            }
            resolve(filePath);
        });
    });
};

const deleteFile = (filePath) => {
    return new Promise((resolve, reject) => {
        fs.unlink(filePath, (err) => {
            if (err) {
                return reject(err);
            }
            resolve();
        });
    });
};

module.exports = {
    saveFile,
    deleteFile,
};
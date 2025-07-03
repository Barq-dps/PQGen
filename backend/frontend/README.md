# PQGen Vanilla Frontend

A simple, lightweight frontend for the PQGen programming challenge platform built with vanilla HTML, CSS, and JavaScript.

## Features

- **PDF Upload**: Drag & drop interface for document upload
- **Challenge Generation**: Real-time challenge creation from PDF content
- **Challenge Types**: Multiple choice, debugging, and coding challenges
- **Difficulty Levels**: Easy, medium, and hard
- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile
- **No Dependencies**: Pure vanilla JavaScript, no frameworks

## Quick Start

1. **Setup Backend**: Ensure your Flask backend is running on `http://localhost:5000`

2. **Open Frontend**: Simply open `index.html` in your browser or serve it with a local server:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js
   npx serve .
   
   # Using PHP
   php -S localhost:8000
   ```

3. **Configure API URL**: Edit `script.js` and update the `API_BASE_URL` if your backend runs on a different port:
   ```javascript
   const API_BASE_URL = 'http://localhost:5000'; // Change this if needed
   ```

## Backend Integration

The frontend expects these API endpoints from your Flask backend:

### Upload Endpoint
```
POST /api/upload?difficulty={easy|medium|hard}
Content-Type: multipart/form-data
Body: PDF file
```

### Status Check
```
GET /api/documents/{document_id}/status
Response: { "status": "processing|completed|error", "error": "..." }
```

### Get Challenges
```
GET /api/documents/{document_id}/challenges
Response: { "challenges": [...] }
```

## File Structure

```
pqgen-vanilla/
├── index.html          # Main HTML file
├── styles.css          # All CSS styles
├── script.js           # JavaScript functionality
└── README.md           # This file
```

## Features Overview

### 🎨 **Design**
- Clean, modern interface
- PQGen brand colors (#2E3A59, #FF6F61)
- Smooth animations and transitions
- Mobile-responsive layout

### 📤 **Upload System**
- Drag & drop PDF upload
- File validation (PDF only, 10MB max)
- Progress indicators
- Error handling

### 🎯 **Challenge Display**
- Grid layout for challenges
- Type and difficulty badges
- Search and filter functionality
- Modal view for challenge details

### 🌙 **Theme Support**
- Light and dark themes
- Persistent theme selection
- Smooth theme transitions

### 📱 **Responsive**
- Mobile-first design
- Touch-friendly interactions
- Adaptive layouts

## Customization

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #2E3A59;
    --accent-color: #FF6F61;
    /* ... other colors */
}
```

### API Configuration
Update the API URL in `script.js`:
```javascript
const API_BASE_URL = 'https://your-backend-domain.com';
```

### Styling
All styles are in `styles.css` using CSS custom properties for easy theming.

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## No Build Process

This frontend requires no build process, bundlers, or package managers. Just open `index.html` in a browser and it works!

## Development

For development with live reload, you can use any static file server:

```bash
# Python 3
python -m http.server 8000

# Node.js (if you have it)
npx serve .

# Or just open index.html directly in your browser
```

## Production Deployment

Simply upload the three files (`index.html`, `styles.css`, `script.js`) to any web server or CDN. No build step required!


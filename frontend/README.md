# AudienceAI Frontend

This is the React frontend for AudienceAI that replaces the previous Streamlit application. It provides a modern, responsive interface for generating LinkedIn posts using AI.

## Features

- **Content Generation**: Generate LinkedIn posts using AI with natural language prompts
- **PDF Upload**: Upload PDF documents to the knowledge base for content generation
- **Source Tracking**: View sources used in content generation (PDFs, web articles, viral posts)
- **Image Generation**: Display and download generated images
- **Modern UI**: Built with React and Tailwind CSS for a sleek, responsive design

## Setup and Installation

### Prerequisites

- Node.js 16 or higher
- npm or yarn package manager
- Backend API running on port 8000 (or configured port)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
Create a `.env` file in the frontend directory with:
```
REACT_APP_API_URL=http://localhost:8000/api
GENERATE_SOURCEMAP=false
```

3. Start the development server:
```bash
npm start
```

The application will open in your browser at `http://localhost:3000`.

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (one-way operation)

## API Integration

The frontend makes API calls to the backend services:

### User Queries API (`/api/user_queries/`)
- `POST /generate` - Generate content based on user prompt
- `POST /generate-stream` - Stream generation process (future feature)
- `GET /status` - Check service health

### Uploads API (`/api/uploads/`)
- `POST /upload-multiple` - Upload multiple PDF files
- `GET /list` - List uploaded documents
- `DELETE /delete/{id}` - Delete specific document
- `GET /health` - Check upload service health

## Components

- **App.js** - Main application component with state management
- **SourcesDisplay.js** - Displays sources used in generation
- **PDFUploader.js** - Handles PDF file uploads with drag-and-drop
- **services/api.js** - API service layer for backend communication
- **utils/sourceExtractor.js** - Utility to extract sources from logs

## Features vs Streamlit App

This React frontend maintains all the functionality of the original Streamlit app:

✅ **Replicated Features:**
- User prompt input with generation
- PDF upload and processing
- Source information display
- Generation logs viewing
- Image display and download
- Two-column layout after generation
- Loading states and error handling

✅ **Improvements:**
- Modern, responsive design
- Better user experience
- Drag-and-drop file uploads
- Collapsible log viewer
- Loading overlays
- Better error handling

## Deployment

To build for production:

```bash
npm run build
```

This creates a `build` folder with optimized production files that can be served by any static file server.

## Troubleshooting

**API Connection Issues:**
- Ensure the backend is running on the correct port
- Check the `REACT_APP_API_URL` environment variable
- Verify CORS is configured properly in the backend

**File Upload Issues:**
- Check file size limits (max 10MB per file)
- Ensure only PDF files are being uploaded
- Verify the uploads API endpoint is accessible

**Build Issues:**
- Clear node_modules and package-lock.json, then reinstall
- Check for version conflicts in dependencies
- Ensure Node.js version compatibility 
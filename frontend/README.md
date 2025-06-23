# AudienceAI Frontend - Next.js

This is the Next.js frontend for AudienceAI, optimized for deployment on Vercel. It provides a modern, responsive interface for generating LinkedIn posts using AI.

## Features

- **Content Generation**: Generate LinkedIn posts using AI with natural language prompts
- **PDF Upload**: Upload PDF documents to the knowledge base for content generation
- **Source Tracking**: View sources used in content generation (PDFs, web articles, viral posts)
- **Image Generation**: Display and download generated images
- **Modern UI**: Built with Next.js, React, and Tailwind CSS for optimal performance
- **Vercel Optimized**: Configured for seamless deployment on Vercel

## Tech Stack

- **Next.js 14**: React framework with App Router
- **React 18**: Modern React with hooks and concurrent features
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icons
- **Axios**: HTTP client for API requests
- **React Dropzone**: Drag-and-drop file uploads

## Setup and Installation

### Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Backend API running (see backend setup)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
GENERATE_SOURCEMAP=false
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## Available Scripts

- `npm run dev` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm start` - Starts the production server
- `npm run lint` - Runs ESLint

## Deployment on Vercel

### Automatic Deployment

1. Connect your GitHub repository to Vercel
2. Set the following environment variables in Vercel:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-api.com/api
   ```
3. Deploy automatically on every push to main branch

### Manual Deployment

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel --prod
```

## Environment Variables

### Required Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (must start with NEXT_PUBLIC_ for client-side access)

### Optional Variables

- `GENERATE_SOURCEMAP`: Set to `false` to disable source maps in production

## API Integration

The frontend communicates with the backend through these endpoints:

### User Queries API (`/api/user_queries/`)
- `POST /generate` - Generate content based on user prompt
- `GET /status` - Check service health

### Uploads API (`/api/uploads/`)
- `POST /upload-multiple` - Upload multiple PDF files
- `GET /list` - List uploaded documents
- `DELETE /delete/{id}` - Delete specific document
- `GET /health` - Check upload service health

## Project Structure

```
frontend/
├── app/
│   ├── components/          # React components
│   │   ├── SourcesDisplay.js
│   │   └── PDFUploader.js
│   ├── services/           # API service layer
│   │   └── api.js
│   ├── utils/              # Utility functions
│   │   └── sourceExtractor.js
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   └── page.js             # Main page component
├── public/                 # Static assets
├── next.config.js          # Next.js configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
└── package.json           # Dependencies and scripts
```

## Features vs Original React App

This Next.js version maintains all functionality while adding:

✅ **Enhanced Features:**
- Server-side rendering capability
- Optimized image loading
- Automatic code splitting
- Built-in performance optimizations
- Vercel deployment optimization
- Better SEO support

✅ **Maintained Features:**
- User prompt input with generation
- PDF upload and processing
- Source information display
- Generation logs viewing
- Image display and download
- Two-column layout after generation
- Loading states and error handling
- Drag-and-drop file uploads

## Performance Optimizations

- **Image Optimization**: Automatic WebP/AVIF conversion
- **Code Splitting**: Automatic route-based splitting
- **Bundle Optimization**: Tree shaking and dead code elimination
- **Caching**: Static generation and API response caching
- **Compression**: Automatic Gzip compression on Vercel

## Troubleshooting

**API Connection Issues:**
- Ensure the backend is running and accessible
- Check the `NEXT_PUBLIC_API_URL` environment variable
- Verify CORS is configured properly in the backend
- For production, ensure the API URL uses HTTPS

**Build Issues:**
- Clear `.next` folder and rebuild: `rm -rf .next && npm run build`
- Check for TypeScript errors if using TypeScript
- Verify all environment variables are properly set

**Deployment Issues:**
- Ensure all environment variables are set in Vercel dashboard
- Check build logs in Vercel deployment panel
- Verify API endpoints are accessible from Vercel's edge network

## Development vs Production

### Development
- API requests proxied through Next.js to avoid CORS issues
- Hot reloading enabled
- Source maps available for debugging

### Production
- Direct API calls to production backend
- Optimized bundle size
- Static assets served from CDN
- Automatic HTTPS on Vercel

## Migration from Create React App

The key changes from the original CRA setup:

1. **File Structure**: Moved from `src/` to `app/` directory
2. **Components**: Added `'use client'` directive for client components
3. **Environment Variables**: Prefixed with `NEXT_PUBLIC_` for client access
4. **API Calls**: Updated base URL handling for SSR compatibility
5. **Styling**: Updated Tailwind config for Next.js structure
6. **Build Process**: Replaced CRA scripts with Next.js commands

## Support

For issues related to:
- **Frontend**: Check browser console and network tab
- **Backend**: Ensure API services are running
- **Deployment**: Check Vercel build logs and environment variables 
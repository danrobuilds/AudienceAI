# Vercel Deployment Guide

This guide covers deploying the AudienceAI frontend to Vercel.

## Prerequisites

- GitHub repository with the Next.js frontend
- Vercel account ([vercel.com](https://vercel.com))
- Backend API deployed and accessible

## Quick Deployment Steps

### 1. Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project"
3. Import your repository
4. Vercel will automatically detect Next.js

### 2. Configure Environment Variables

In the Vercel dashboard, add these environment variables:

**Required:**
- `NEXT_PUBLIC_API_URL` - Your backend API URL (e.g., `https://api.yourapp.com/api`)

**Optional:**
- `GENERATE_SOURCEMAP` - Set to `false` for production

### 3. Deploy

- Click "Deploy"
- Vercel will build and deploy automatically
- Your app will be available at `https://your-project.vercel.app`

## Environment Variable Examples

### Development
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
GENERATE_SOURCEMAP=false
```

### Production
```env
NEXT_PUBLIC_API_URL=https://your-backend-api.herokuapp.com/api
GENERATE_SOURCEMAP=false
```

## Domain Configuration

### Custom Domain
1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed by Vercel

### Subdomain
Vercel provides automatic subdomains like:
- `your-project.vercel.app`
- `your-project-git-main-username.vercel.app`

## Automatic Deployments

- **Production**: Deploys automatically from `main` branch
- **Preview**: Creates preview deployments for pull requests
- **Development**: Use `npm run dev` locally

## Performance Optimization

Vercel automatically provides:
- **Global CDN**: Static assets served from edge locations
- **Image Optimization**: Automatic WebP/AVIF conversion
- **Code Splitting**: Route-based code splitting
- **Compression**: Gzip/Brotli compression
- **Caching**: Intelligent caching strategies

## Monitoring

Use Vercel's built-in monitoring:
- **Analytics**: Page views and performance metrics
- **Speed Insights**: Core Web Vitals tracking
- **Function Logs**: Server-side function logs
- **Real User Monitoring**: Actual user performance data

## Troubleshooting

### Build Failures
- Check build logs in Vercel dashboard
- Verify all dependencies are in `package.json`
- Ensure environment variables are set

### API Connection Issues
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings on backend
- Ensure backend is accessible from Vercel's network

### Performance Issues
- Enable Speed Insights in Vercel dashboard
- Use Chrome DevTools to analyze bundle size
- Check Core Web Vitals in production

## CLI Deployment

Alternatively, use Vercel CLI:

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

## Advanced Configuration

### Custom Headers
Configured in `vercel.json` for security headers.

### Edge Functions
Can be added for advanced server-side logic.

### Analytics
Enable Web Analytics in Project Settings.

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js on Vercel](https://vercel.com/docs/frameworks/nextjs)
- [Deployment Issues](https://vercel.com/docs/concepts/deployments/troubleshoot-a-build) 
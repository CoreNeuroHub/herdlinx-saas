# Vercel Deployment Guide

This guide provides step-by-step instructions for deploying the Herdlinx SaaS application to Vercel.

## Prerequisites

- Vercel account (sign up at [vercel.com](https://vercel.com))
- MongoDB Atlas account (or MongoDB database accessible from the internet)
- Git repository (GitHub, GitLab, or Bitbucket)
- Vercel CLI (optional, for local testing)

## Table of Contents

1. [Project Setup](#project-setup)
2. [MongoDB Configuration](#mongodb-configuration)
3. [Vercel Configuration](#vercel-configuration)
4. [Environment Variables](#environment-variables)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

## Project Setup

### 1. Verify Project Structure

Ensure your project has the following structure:
```
herdlinx-saas/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── config.py
├── requirements.txt
├── vercel.json           # Vercel configuration
└── DEPLOYMENT.md
```

### 2. Install Vercel CLI (Optional)

For local testing before deploying:

```bash
npm install -g vercel
```

## MongoDB Configuration

### 1. Set Up MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier is available)
3. Create a database user with read/write permissions
4. Whitelist IP addresses:
   - For Vercel: Add `0.0.0.0/0` to allow all IPs (or specific Vercel IPs if available)
5. Get your connection string:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/`)

### 2. Update MongoDB URI

Replace the connection string placeholders:
- `<username>`: Your database username
- `<password>`: Your database password
- `<cluster>`: Your cluster name

Example: `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

## Vercel Configuration

### 1. vercel.json

The `vercel.json` file configures how Vercel handles your Flask application:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHONPATH": "."
  }
}
```

### 2. API Entry Point

The `api/index.py` file serves as the serverless function entry point that Vercel will use.

## Environment Variables

### Required Environment Variables

Configure these in your Vercel project settings:

1. **SECRET_KEY**
   - Generate a strong secret key:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Used for Flask session security and CSRF protection

2. **MONGODB_URI**
   - Your MongoDB connection string
   - Format: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`
   - Include authentication credentials in the URI

3. **MONGODB_DB**
   - Database name
   - Default: `herdlinx_saas`
   - Can be changed if you prefer a different database name

### Setting Environment Variables in Vercel

#### Via Vercel Dashboard:

1. Go to your project on [vercel.com](https://vercel.com)
2. Click on "Settings" → "Environment Variables"
3. Add each variable:
   - **Name**: `SECRET_KEY`
   - **Value**: Your generated secret key
   - **Environment**: Production, Preview, Development (select all)
4. Repeat for `MONGODB_URI` and `MONGODB_DB`

#### Via Vercel CLI:

```bash
vercel env add SECRET_KEY
vercel env add MONGODB_URI
vercel env add MONGODB_DB
```

## Deployment Steps

### Method 1: Deploy via Vercel Dashboard (Recommended)

1. **Connect Repository**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New..." → "Project"
   - Import your Git repository (GitHub, GitLab, or Bitbucket)
   - Authorize Vercel to access your repository

2. **Configure Project**
   - **Framework Preset**: Other
   - **Root Directory**: `./` (project root)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

3. **Add Environment Variables**
   - Click "Environment Variables"
   - Add all required variables (see [Environment Variables](#environment-variables))
   - Save and continue

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your application will be live at `https://your-project.vercel.app`

### Method 2: Deploy via Vercel CLI

1. **Login to Vercel**
   ```bash
   vercel login
   ```

2. **Link Your Project**
   ```bash
   vercel link
   ```
   - Follow prompts to link to existing project or create new one

3. **Set Environment Variables**
   ```bash
   vercel env add SECRET_KEY
   vercel env add MONGODB_URI
   vercel env add MONGODB_DB
   ```

4. **Deploy**
   ```bash
   vercel --prod
   ```

### Method 3: Automatic Deployments (CI/CD)

When connected to a Git repository, Vercel automatically deploys:
- **Production**: Every push to the `main` branch
- **Preview**: Every push to other branches or pull requests

No additional configuration needed once the repository is connected.

## Post-Deployment

### 1. Verify Deployment

1. Visit your deployment URL: `https://your-project.vercel.app`
2. Test the login functionality
3. Verify database connectivity by creating a test feedlot

### 2. Create Initial Admin User

On first deployment, the application automatically creates a default admin user if none exists:
- **Username**: `admin`
- **Password**: Check your application logs or database

**Important**: Change the default admin password immediately after first login.

### 3. Configure Custom Domain (Optional)

1. Go to your project settings on Vercel
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions
5. Vercel will automatically configure SSL certificates

### 4. Set Up Monitoring

- Vercel provides built-in analytics and monitoring
- Check the "Analytics" tab in your project dashboard
- Monitor function execution times and error rates

## Troubleshooting

### Common Issues

#### 1. "Module Not Found" Errors

**Problem**: Python dependencies not installed correctly.

**Solution**:
- Verify `requirements.txt` is in the project root
- Check that all dependencies are listed with correct versions
- Review build logs in Vercel dashboard for specific missing modules

#### 2. MongoDB Connection Errors

**Problem**: Cannot connect to MongoDB or SSL/TLS handshake failures.

**Common SSL/TLS Errors**:
- `SSL handshake failed: [SSL: TLSV1_ALERT_INTERNAL_ERROR]`
- `tlsv1 alert internal error`

**Solution**:
- **Connection String Format**: Ensure your `MONGODB_URI` uses `mongodb+srv://` format for Atlas
  - Format: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`
  - TLS is automatically enabled for `mongodb+srv://` connections
  - Do not add `tls=true` to the connection string explicitly (it's automatic)
  
- **URL Encoding**: If your password contains special characters, URL-encode them:
  - `@` becomes `%40`
  - `:` becomes `%3A`
  - `/` becomes `%2F`
  - `?` becomes `%3F`
  - `#` becomes `%23`
  - `[` becomes `%5B`
  - `]` becomes `%5D`
  
- **IP Whitelisting**: Verify MongoDB Atlas IP whitelist:
  - For Vercel: Add `0.0.0.0/0` to allow all IPs (or specific Vercel IPs if available)
  - Go to MongoDB Atlas → Network Access → Add IP Address
  
- **Verify Credentials**: Ensure database username and password are correct
  - Check for typos in username/password
  - Verify the user has read/write permissions
  
- **Connection String Parameters**: Ensure your connection string includes:
  - `retryWrites=true`
  - `w=majority` (or appropriate write concern)
  - Database name in the path if needed
  
- **Test Locally**: Test the connection string locally first to verify it works:
  ```python
  from pymongo import MongoClient
  client = MongoClient("your-connection-string")
  client.server_info()  # Will raise exception if connection fails
  ```
  
- **Environment Variable**: Verify `MONGODB_URI` is correctly set in Vercel:
  - Check for extra spaces or quotes
  - Ensure it's set for the correct environment (Production, Preview, Development)

#### 3. Session Not Persisting

**Problem**: User sessions are lost between requests.

**Solution**:
- Verify `SECRET_KEY` is set correctly
- Sessions use secure cookies by default (works in serverless)
- Check browser cookie settings
- Ensure HTTPS is enabled (Vercel provides this automatically)

#### 4. Static Files Not Loading

**Problem**: CSS, images, or JavaScript files return 404.

**Solution**:
- Verify static files are in `app/static/` directory
- Check that `vercel.json` routes are configured correctly
- Clear browser cache and retry
- Check Vercel build logs for asset compilation issues

#### 5. Function Timeout Errors

**Problem**: Long-running operations timeout.

**Solution**:
- Vercel serverless functions have execution limits
- Optimize database queries
- Implement pagination for large datasets
- Consider breaking long operations into smaller chunks
- For Hobby plan: 10-second timeout limit
- For Pro plan: 60-second timeout limit

#### 6. "Internal Server Error" on All Routes

**Problem**: Application not initializing correctly.

**Solution**:
- Check Vercel build logs in the dashboard
- Verify all environment variables are set
- Ensure `api/index.py` exists and is properly configured
- Review Python version compatibility (Vercel uses Python 3.9+)

### Viewing Logs

1. **Vercel Dashboard**:
   - Go to your project
   - Click "Deployments"
   - Select a deployment
   - Click "Functions" → "View Function Logs"

2. **Vercel CLI**:
   ```bash
   vercel logs [deployment-url]
   ```

### Testing Locally with Vercel

Test your Vercel configuration locally:

```bash
vercel dev
```

This simulates the Vercel serverless environment locally.

## Performance Optimization

### 1. Database Connection Pooling

MongoDB connections are handled automatically by PyMongo. In serverless environments:
- Connections are pooled per function instance
- Each function instance maintains its own connection pool
- Connections are reused across invocations within the same instance

### 2. Caching Strategies

- Use Flask's built-in caching for frequently accessed data
- Consider implementing Redis for distributed caching (if needed)
- Cache static content using Vercel's Edge Network

### 3. Function Optimization

- Minimize cold start times by reducing import overhead
- Use lazy imports where possible
- Keep function code lean and focused

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to Git
- Use Vercel's environment variables for all secrets
- Rotate secrets regularly
- Use different secrets for production, preview, and development

### 2. MongoDB Security

- Use strong database passwords
- Enable IP whitelisting (though `0.0.0.0/0` may be needed for Vercel)
- Enable MongoDB Atlas encryption at rest
- Regularly update MongoDB driver versions

### 3. Application Security

- Keep Flask and dependencies updated
- Use strong `SECRET_KEY` (minimum 32 characters)
- Enable HTTPS (automatic with Vercel)
- Implement rate limiting if needed (Vercel Pro plan)

## Scaling Considerations

### Vercel Limits

**Hobby Plan**:
- 100GB bandwidth/month
- 100 serverless function executions/day
- 10-second function timeout

**Pro Plan**:
- Unlimited bandwidth
- Unlimited serverless function executions
- 60-second function timeout
- Team collaboration features

### Database Scaling

- MongoDB Atlas scales automatically
- Monitor database performance in Atlas dashboard
- Implement database indexing for frequently queried fields
- Use MongoDB aggregation pipelines for complex queries

## Rollback Procedure

If a deployment causes issues:

1. Go to Vercel dashboard
2. Click "Deployments"
3. Find the previous working deployment
4. Click "..." → "Promote to Production"

## Support and Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Checklist

Before deploying, ensure:

- [ ] `vercel.json` is configured
- [ ] `api/index.py` exists and is properly set up
- [ ] `requirements.txt` includes all dependencies
- [ ] Environment variables are set in Vercel
- [ ] MongoDB Atlas is configured and accessible
- [ ] IP whitelist includes Vercel IPs
- [ ] `SECRET_KEY` is generated and set
- [ ] Test deployment locally with `vercel dev`
- [ ] Review and update any hardcoded URLs
- [ ] Check that static files are properly referenced

## Next Steps After Deployment

1. Test all major application features
2. Create production admin user and change default password
3. Set up custom domain (if desired)
4. Configure monitoring and alerts
5. Set up automated backups for MongoDB
6. Review and optimize application performance
7. Document any deployment-specific configurations


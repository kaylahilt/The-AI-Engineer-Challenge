# Vercel Deployment Testing Guide

## 🚀 How to Test Before Merging to Main

### Method 1: Vercel CLI (Recommended)

Install Vercel CLI and test locally:

```bash
# Install Vercel CLI
npm install -g vercel

# Test the build locally
vercel build

# Run a local production server
vercel dev --prod
```

This will:
- Use the same build process as Vercel's servers
- Catch dependency issues early
- Test serverless functions locally

### Method 2: Preview Deployments

Vercel automatically creates preview deployments for PRs:

1. **Enable Preview Deployments** in Vercel Dashboard:
   - Go to Project Settings → Git
   - Enable "Preview Deployments"
   - Each PR gets its own URL

2. **Check PR Comments**: Vercel bot will comment with preview URL

3. **Branch-specific Deployments**: 
   ```bash
   # Push to a feature branch
   git push origin feature-branch
   
   # Vercel creates: your-project-git-branch-name.vercel.app
   ```

### Method 3: Pre-deployment Checks

Create a pre-deployment test script:

```bash
#!/bin/bash
# File: scripts/test-deployment.sh

echo "🧪 Testing Vercel deployment locally..."

# Test Python dependencies
echo "Checking Python dependencies..."
cd api
pip install -r requirements.txt --dry-run
if [ $? -ne 0 ]; then
    echo "❌ Python dependency issues found!"
    exit 1
fi

# Test Node dependencies
echo "Checking Node dependencies..."
cd ../frontend
npm ci --dry-run
if [ $? -ne 0 ]; then
    echo "❌ Node dependency issues found!"
    exit 1
fi

# Test build
echo "Testing build process..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ All checks passed!"
```

### Method 4: Staging Branch Strategy

Set up a staging branch that deploys to a preview URL:

1. Create a `staging` branch:
   ```bash
   git checkout -b staging
   git push origin staging
   ```

2. In Vercel Dashboard:
   - Go to Settings → Domains
   - Add `staging-your-project.vercel.app`
   - Link it to the `staging` branch

3. Test deployment:
   ```bash
   git checkout staging
   git merge feature-branch
   git push origin staging
   # Check staging URL before merging to main
   ```

### Method 5: Docker-based Testing

Create a Dockerfile that mimics Vercel's environment:

```dockerfile
# File: Dockerfile.vercel-test
FROM python:3.12-slim

# Copy API files
WORKDIR /api
COPY api/requirements.txt .
RUN pip install -r requirements.txt

# Test imports
COPY api/ .
RUN python -c "import pdf_handler; print('✅ Imports successful')"

# Build frontend
FROM node:20-slim as frontend
WORKDIR /frontend
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
RUN npm run build
```

Test with:
```bash
docker build -f Dockerfile.vercel-test .
```

### Method 6: GitHub Actions Pre-check

Add a workflow to test deployment before merge:

```yaml
# .github/workflows/vercel-precheck.yml
name: Vercel Deployment Check

on:
  pull_request:
    branches: [ main ]

jobs:
  test-deployment:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Test Python Dependencies
      run: |
        cd api
        pip install -r requirements.txt
        python -c "import index; print('API imports OK')"
    
    - name: Setup Node
      uses: actions/setup-node@v3
      with:
        node-version: '20'
    
    - name: Test Frontend Build
      run: |
        cd frontend
        npm ci
        npm run build
```

## 🎯 Best Practices

1. **Always test with Vercel CLI first**: `vercel build`
2. **Use preview deployments**: Every PR should have one
3. **Set up staging environment**: Test major changes there first
4. **Create deployment checklist**: Document common issues
5. **Monitor failed deployments**: Learn from deployment logs

## 🛠️ Quick Debugging Commands

```bash
# Check what Vercel will install
vercel env pull .env.local

# Test serverless functions
vercel dev

# See exact build output
vercel build --debug

# Test production build locally
vercel build && vercel start
```

## 📝 Common Issues to Check

1. **Dependencies**: Ensure all packages are on PyPI/npm
2. **Python version**: Vercel uses 3.12 by default
3. **File paths**: Case sensitivity matters on Linux
4. **Environment variables**: Set in Vercel dashboard
5. **Build size**: Keep under 250MB uncompressed

By following these methods, you can catch 99% of deployment issues before merging! 
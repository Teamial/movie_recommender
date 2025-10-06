#!/bin/bash

# Deploy frontend to Railway with correct build context
echo "🚀 Deploying frontend to Railway..."

# Navigate to frontend directory for proper build context
cd frontend

# Deploy with correct build context
railway up --dockerfile Dockerfile

echo "✅ Frontend deployment initiated!"
echo "📝 Note: Make sure to set VITE_API_URL environment variable in Railway dashboard"

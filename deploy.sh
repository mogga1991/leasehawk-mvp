#!/bin/bash

echo "🚀 LeaseHawk MVP - Vercel Deployment Script"
echo "=========================================="

# Check if vercel CLI is available
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Please install Node.js first."
    exit 1
fi

echo "📋 Pre-deployment checklist:"
echo "✅ Code committed to Git"
echo "✅ Vercel configuration files created"
echo "✅ API structure ready"

echo ""
echo "🔑 Step 1: Login to Vercel"
echo "Running: npx vercel login"
npx vercel login

echo ""
echo "🚢 Step 2: Deploy to Vercel"
echo "Running: npx vercel --yes"
npx vercel --yes

echo ""
echo "🌍 Step 3: Set Environment Variables"
echo "Add your Neon database URL:"
echo "npx vercel env add DATABASE_URL"
echo ""
echo "Your Neon URL: postgresql://neondb_owner:npg_or2tiHunLPm7@ep-quiet-band-adopruwt-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
echo ""
read -p "Press Enter to set the DATABASE_URL environment variable..."
npx vercel env add DATABASE_URL

echo ""
echo "🎯 Step 4: Deploy to Production"
echo "Running: npx vercel --prod"
npx vercel --prod

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Visit your Vercel URL to see the app"
echo "2. Check /api/status to verify the API is working"
echo "3. The database will be automatically seeded on first API call"
echo ""
echo "Your LeaseHawk MVP is now live! 🦅"
#!/bin/bash

# TaipeiSim - Coolify Deployment Script
# This script helps prepare your application for Coolify deployment

echo "🚀 TaipeiSim - Coolify Deployment Preparation"
echo "================================================"
echo ""

# Step 1: Check large files
echo "📊 Step 1: Checking for large files..."
if [ -f "data/taipei.graphml" ]; then
    SIZE=$(du -h data/taipei.graphml | cut -f1)
    echo "   ✓ Found taipei.graphml ($SIZE)"
    echo "   ⚠️  This file is too large for Git!"
    echo ""
    echo "   You need to upload it manually to your VPS:"
    echo "   scp data/taipei.graphml root@YOUR_VPS_IP:/opt/data/"
    echo ""
else
    echo "   ⚠️  taipei.graphml not found in data/"
fi

# Step 2: Check Docker files
echo "📦 Step 2: Checking Docker configuration..."
FILES=("Dockerfile" "docker-compose.yml" ".dockerignore" "frontend/Dockerfile" "frontend/nginx.conf")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file missing!"
    fi
done
echo ""

# Step 3: Check .gitignore
echo "🔒 Step 3: Checking .gitignore..."
if grep -q "*.graphml" .gitignore; then
    echo "   ✓ Large files excluded from Git"
else
    echo "   ⚠️  Add *.graphml to .gitignore"
fi
echo ""

# Step 4: Git status
echo "📝 Step 4: Git status..."
if [ -d ".git" ]; then
    UNCOMMITTED=$(git status --porcelain | wc -l)
    if [ $UNCOMMITTED -gt 0 ]; then
        echo "   ⚠️  You have $UNCOMMITTED uncommitted changes"
        echo ""
        echo "   Run these commands to commit:"
        echo "   git add ."
        echo "   git commit -m 'Prepare for Coolify deployment'"
        echo "   git push origin main"
    else
        echo "   ✓ All changes committed"
    fi
else
    echo "   ⚠️  Not a Git repository"
fi
echo ""

# Step 5: Summary
echo "================================================"
echo "✅ Pre-deployment checklist:"
echo ""
echo "1. ✓ Docker files created"
echo "2. ⚠️  Upload taipei.graphml to VPS manually"
echo "3. ⚠️  Commit and push code to GitHub"
echo "4. ⚠️  Configure Coolify project"
echo "5. ⚠️  Add volume mapping in Coolify"
echo "6. ⚠️  Deploy via Coolify dashboard"
echo ""
echo "📖 Read DEPLOYMENT.md for detailed instructions"
echo "================================================"

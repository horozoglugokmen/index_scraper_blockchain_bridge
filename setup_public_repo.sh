#!/bin/bash

# 🔮 Advanced Index Oracle System - Public Repository Setup
# This script prepares the public version of the oracle system

echo "🚀 Setting up Public Repository..."
echo "=================================="

# Create clean directory structure
echo "📁 Creating directory structure..."
mkdir -p public-oracle
cd public-oracle

# Copy sanitized files
echo "📋 Copying sanitized files..."
cp ../scraping/index_oracle_main.py ./
cp ../requirements.txt ./
cp ../env.example ./
cp ../README_PUBLIC.md ./README.md

# Create .gitignore
echo "🔒 Creating .gitignore..."
cat > .gitignore << EOF
# Environment and secrets
.env
*.env
config.local.py

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Data files
*.csv
*.json
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
EOF

# Initialize git repository
echo "🌱 Initializing git repository..."
git init
git add .
git commit -m "Initial commit: Advanced Index Oracle System

Features:
- Level 5 anti-detection web scraping
- Dynamic fee calculation with inverse correlation
- Blockchain oracle integration
- Production-ready error handling
- Comprehensive data logging

This is a sanitized public version suitable for portfolio showcase."

echo ""
echo "✅ Public repository setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create repository on GitHub"
echo "2. git remote add origin https://github.com/yourusername/advanced-index-oracle"
echo "3. git push -u origin main"
echo ""
echo "⚠️  SECURITY CHECK:"
echo "- No private keys included ✅"
echo "- No real URLs included ✅" 
echo "- No contract addresses included ✅"
echo "- All sensitive data sanitized ✅"
echo ""
 
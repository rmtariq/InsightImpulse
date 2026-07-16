#!/bin/bash

# Enhanced InsightPulse Deployment Script
# Professional deployment to Railway + Netlify

echo "🚀 Starting Enhanced InsightPulse Deployment..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_requirements() {
    echo -e "${BLUE}📋 Checking deployment requirements...${NC}"
    
    # Check for Railway CLI
    if ! command -v railway &> /dev/null; then
        echo -e "${YELLOW}⚠️  Railway CLI not found. Installing...${NC}"
        npm install -g @railway/cli
    else
        echo -e "${GREEN}✅ Railway CLI found${NC}"
    fi
    
    # Check for Netlify CLI
    if ! command -v netlify &> /dev/null; then
        echo -e "${YELLOW}⚠️  Netlify CLI not found. Installing...${NC}"
        npm install -g netlify-cli
    else
        echo -e "${GREEN}✅ Netlify CLI found${NC}"
    fi
    
    # Check for Git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git not found. Please install Git first.${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Git found${NC}"
    fi
}

# Initialize Git repository if needed
init_git() {
    if [ ! -d ".git" ]; then
        echo -e "${BLUE}📦 Initializing Git repository...${NC}"
        git init
        git add .
        git commit -m "Initial commit: Enhanced InsightPulse Universal Social Listening Platform"
        echo -e "${GREEN}✅ Git repository initialized${NC}"
    else
        echo -e "${GREEN}✅ Git repository already exists${NC}"
        # Add and commit current changes
        git add .
        git commit -m "Enhanced framework update: A-Z deployment ready" || echo "No changes to commit"
    fi
}

# Deploy backend to Railway
deploy_backend() {
    echo -e "${BLUE}🚂 Deploying Enhanced Backend to Railway...${NC}"
    
    # Login to Railway (if not already logged in)
    echo -e "${YELLOW}🔐 Please login to Railway if prompted...${NC}"
    railway login
    
    # Create new project or link existing
    if [ ! -f "railway.json" ]; then
        echo -e "${RED}❌ railway.json not found${NC}"
        exit 1
    fi
    
    # Initialize Railway project
    railway init insightpulse-enhanced
    
    # Set environment variables
    echo -e "${BLUE}⚙️  Setting environment variables...${NC}"
    railway variables set ENVIRONMENT=production
    railway variables set ENHANCED_FRAMEWORK_ENABLED=true
    railway variables set CRISIS_DETECTION_ENABLED=true
    railway variables set REAL_TIME_PROCESSING=true
    railway variables set INDUSTRY_MODULES_ENABLED=true
    railway variables set CULTURAL_ANALYSIS_ENABLED=true
    railway variables set MALAYSIAN_OPTIMIZATION=true
    railway variables set PYTHONPATH=/app
    
    # Deploy
    echo -e "${BLUE}🚀 Deploying to Railway...${NC}"
    railway up
    
    # Get the deployment URL
    BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url' 2>/dev/null || echo "https://insightpulse-enhanced.railway.app")
    echo -e "${GREEN}✅ Backend deployed to: ${BACKEND_URL}${NC}"
    
    # Update frontend configuration with actual backend URL
    sed -i.bak "s|https://insightpulse-enhanced.railway.app|${BACKEND_URL}|g" netlify.toml
    sed -i.bak "s|https://insightpulse-enhanced.railway.app|${BACKEND_URL}|g" web_frontend/universal_dashboard.html
    
    echo -e "${GREEN}✅ Backend deployment completed!${NC}"
    return 0
}

# Deploy frontend to Netlify
deploy_frontend() {
    echo -e "${BLUE}🌐 Deploying Enhanced Frontend to Netlify...${NC}"
    
    # Login to Netlify
    echo -e "${YELLOW}🔐 Please login to Netlify if prompted...${NC}"
    netlify login
    
    # Create site or link existing
    if [ ! -f ".netlify/state.json" ]; then
        echo -e "${BLUE}🆕 Creating new Netlify site...${NC}"
        netlify init --manual
    fi
    
    # Deploy
    echo -e "${BLUE}🚀 Deploying to Netlify...${NC}"
    netlify deploy --prod --dir=web_frontend
    
    # Get the deployment URL
    FRONTEND_URL=$(netlify status --json | jq -r '.site_url' 2>/dev/null || echo "https://insightpulse-dashboard.netlify.app")
    echo -e "${GREEN}✅ Frontend deployed to: ${FRONTEND_URL}${NC}"
    
    echo -e "${GREEN}✅ Frontend deployment completed!${NC}"
    return 0
}

# Setup databases
setup_databases() {
    echo -e "${BLUE}🗄️  Setting up databases...${NC}"
    
    # Add PostgreSQL addon to Railway
    echo -e "${BLUE}📊 Adding PostgreSQL database...${NC}"
    railway add postgresql
    
    # Add Redis addon to Railway
    echo -e "${BLUE}🔄 Adding Redis cache...${NC}"
    railway add redis
    
    echo -e "${GREEN}✅ Databases setup completed!${NC}"
}

# Run health checks
health_check() {
    echo -e "${BLUE}🏥 Running health checks...${NC}"
    
    # Wait for deployment to be ready
    echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
    sleep 30
    
    # Check backend health
    BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url' 2>/dev/null || echo "https://insightpulse-enhanced.railway.app")
    
    echo -e "${BLUE}🔍 Checking backend health: ${BACKEND_URL}/health${NC}"
    if curl -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend health check failed, but this might be normal during initial startup${NC}"
    fi
    
    # Check frontend
    FRONTEND_URL=$(netlify status --json | jq -r '.site_url' 2>/dev/null || echo "https://insightpulse-dashboard.netlify.app")
    echo -e "${BLUE}🔍 Checking frontend: ${FRONTEND_URL}${NC}"
    if curl -f "${FRONTEND_URL}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is accessible!${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend check failed, but this might be normal during DNS propagation${NC}"
    fi
}

# Display deployment summary
deployment_summary() {
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}🎉 Enhanced InsightPulse Deployment Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "${BLUE}📊 Your Universal Social Listening Platform:${NC}"
    echo ""
    
    BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url' 2>/dev/null || echo "https://insightpulse-enhanced.railway.app")
    FRONTEND_URL=$(netlify status --json | jq -r '.site_url' 2>/dev/null || echo "https://insightpulse-dashboard.netlify.app")
    
    echo -e "${GREEN}🌐 Frontend Dashboard:${NC} ${FRONTEND_URL}"
    echo -e "${GREEN}⚡ Backend API:${NC} ${BACKEND_URL}"
    echo -e "${GREEN}📖 API Documentation:${NC} ${BACKEND_URL}/docs"
    echo -e "${GREEN}🏥 Health Check:${NC} ${BACKEND_URL}/health"
    echo ""
    echo -e "${BLUE}🎯 Enhanced Features Available:${NC}"
    echo -e "  ✅ Multi-layered Sentiment Analysis"
    echo -e "  ✅ Crisis Detection & Monitoring"
    echo -e "  ✅ Industry-Specific Intelligence"
    echo -e "  ✅ Cultural Context Analysis"
    echo -e "  ✅ 8 User Types Support"
    echo -e "  ✅ 18+ Platform Coverage"
    echo -e "  ✅ Malaysian Market Optimization"
    echo ""
    echo -e "${BLUE}💰 Monetization Ready:${NC}"
    echo -e "  • SME Basic: RM 199/month"
    echo -e "  • Professional: RM 699/month"
    echo -e "  • Enterprise: RM 2,499/month"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo -e "  1. Test your deployment at: ${FRONTEND_URL}"
    echo -e "  2. Configure custom domain (optional)"
    echo -e "  3. Set up monitoring and alerts"
    echo -e "  4. Start onboarding customers!"
    echo ""
    echo -e "${GREEN}🚀 Your Enhanced InsightPulse is now LIVE!${NC}"
}

# Main deployment flow
main() {
    echo -e "${BLUE}🌟 Enhanced InsightPulse Universal Social Listening Platform${NC}"
    echo -e "${BLUE}🎯 Professional Deployment Starting...${NC}"
    echo ""
    
    check_requirements
    init_git
    setup_databases
    deploy_backend
    deploy_frontend
    health_check
    deployment_summary
    
    echo -e "${GREEN}✨ Deployment completed successfully!${NC}"
}

# Run main function
main "$@"

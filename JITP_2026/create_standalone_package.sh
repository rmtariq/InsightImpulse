#!/bin/bash
# Create standalone dashboard package for offline sharing

echo "📦 Creating standalone dashboard package..."

# Create package directory
mkdir -p dashboard_package
cd dashboard_package

# Copy HTML (from project root)
cp ../../static/pas_strategy_dashboard.html index.html

# Copy JSON data (from project root)
cp ../../static/pas_dashboard_data.json .
cp ../../static/pas_ai_insights.json .

# Create README
cat > README.txt << 'EOF'
=======================================================
PAS POLITICAL STRATEGY DASHBOARD - STANDALONE PACKAGE
=======================================================

📊 Dashboard: index.html
📁 Data Files: pas_dashboard_data.json, pas_ai_insights.json

HOW TO VIEW:
1. Double-click "index.html" to open in browser
2. Or right-click → Open With → Chrome/Safari/Firefox

REQUIREMENTS:
- Modern web browser (Chrome, Safari, Firefox, Edge)
- Internet connection (for Chart.js CDN)
- JavaScript enabled

NO SERVER NEEDED - works offline!

Generated: $(date)
=======================================================
EOF

# Create ZIP package
cd ..
zip -r "PAS_Dashboard_$(date +%Y%m%d_%H%M%S).zip" dashboard_package/

echo "✅ Package created: PAS_Dashboard_*.zip"
echo "📧 You can now email this ZIP file or share via USB"
echo "🌐 Recipients just need to unzip and open index.html"

# Cleanup
rm -rf dashboard_package

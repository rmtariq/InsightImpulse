#!/bin/bash
# ==============================================================================
# 📊 InsightPulse Analysis Monitor & Auto-Refresh
# ==============================================================================
# This script monitors the backend log for analysis completion and provides
# real-time updates. When analysis completes, it opens the results in browser.
# ==============================================================================

cd /Users/rmtariq/Documents/InsightPulse

echo "🔍 Starting Analysis Monitor..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get initial log position
INITIAL_LINES=$(wc -l < backend.log 2>/dev/null || echo "0")
echo "📝 Monitoring backend.log from line $INITIAL_LINES..."
echo ""

# Track analysis state
ANALYSIS_STARTED=0
CRAWLING_DONE=0
SENTIMENT_DONE=0
COMBINED_SAVED=0
ANALYSIS_COMPLETE=0

# Platform counters
PLATFORMS_TOTAL=0
PLATFORMS_DONE=0

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 LIVE ANALYSIS PROGRESS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Monitor backend.log in real-time
tail -f backend.log | while read line; do
    # Detect analysis start
    if [[ $line == *"Starting PERFECT analysis"* ]] || [[ $line == *"📊 Platforms:"* ]]; then
        if [ $ANALYSIS_STARTED -eq 0 ]; then
            ANALYSIS_STARTED=1
            echo -e "${GREEN}✅ Analysis Started!${NC}"
            
            # Extract platforms
            if [[ $line == *"📊 Platforms:"* ]]; then
                PLATFORMS=$(echo $line | grep -o "\[.*\]")
                echo -e "${BLUE}📱 Platforms: $PLATFORMS${NC}"
                PLATFORMS_TOTAL=$(echo $PLATFORMS | grep -o "'" | wc -l)
                PLATFORMS_TOTAL=$((PLATFORMS_TOTAL / 2))
                echo -e "${BLUE}🎯 Total platforms: $PLATFORMS_TOTAL${NC}"
            fi
            echo ""
        fi
    fi
    
    # Track platform completion
    if [[ $line == *"📱 Collecting data from"* ]]; then
        PLATFORM=$(echo $line | sed 's/.*from //' | sed 's/\.\.\.//')
        echo -e "${YELLOW}🔄 Processing: $PLATFORM${NC}"
    fi
    
    # Track crawling progress
    if [[ $line == *"✅ Collected"* ]] || [[ $line == *"records from"* ]]; then
        echo -e "${GREEN}  ✓ $line${NC}" | grep -o "✅.*"
    fi
    
    # Track sentiment analysis
    if [[ $line == *"Running custom sentiment"* ]] || [[ $line == *"sentiment & emotion analysis"* ]]; then
        RECORDS=$(echo $line | grep -o "[0-9]* valid texts")
        echo -e "${BLUE}🧠 Analyzing sentiment: $RECORDS${NC}"
    fi
    
    # Track platform processing completion
    if [[ $line == *"✅ Processed"* ]] && [[ $line == *"records for"* ]]; then
        PLATFORMS_DONE=$((PLATFORMS_DONE + 1))
        echo -e "${GREEN}✅ Platform $PLATFORMS_DONE/$PLATFORMS_TOTAL completed${NC}"
        echo ""
    fi
    
    # Detect combined data saving
    if [[ $line == *"💾 COMBINED DATA saved"* ]] || [[ $line == *"COMBINED DATA saved"* ]]; then
        COMBINED_SAVED=1
        FILEPATH=$(echo $line | grep -o "data/combined/.*\.csv")
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}🎉 COMBINED DATA SAVED!${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${BLUE}📁 File: $FILEPATH${NC}"
        
        # Get file info
        if [ -f "$FILEPATH" ]; then
            FILESIZE=$(ls -lh "$FILEPATH" | awk '{print $5}')
            LINECOUNT=$(wc -l < "$FILEPATH")
            echo -e "${BLUE}📊 Size: $FILESIZE${NC}"
            echo -e "${BLUE}📝 Records: $((LINECOUNT - 1))${NC}"
        fi
        echo ""
    fi
    
    # Detect analysis completion
    if [[ $line == *"Analysis completed successfully"* ]] || [[ $line == *"✅ Analysis completed"* ]]; then
        ANALYSIS_COMPLETE=1
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}🎉 ANALYSIS COMPLETE!${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Show summary
        echo -e "${BLUE}📊 Summary:${NC}"
        echo -e "  ✅ Platforms processed: $PLATFORMS_DONE"
        echo -e "  ✅ Combined data saved: $([ $COMBINED_SAVED -eq 1 ] && echo 'Yes ✓' || echo 'No ✗')"
        echo ""
        
        # Check for combined data files
        echo -e "${BLUE}📁 Latest Combined Files:${NC}"
        ls -lht data/combined/*.csv 2>/dev/null | head -3 | while read line; do
            echo "  $line"
        done
        echo ""
        
        # Open browser
        echo -e "${YELLOW}🌐 Opening results in browser...${NC}"
        sleep 2
        open http://localhost:8001/
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}✅ Monitor completed! Check your browser.${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Exit after completion
        pkill -P $$ tail
        exit 0
    fi
    
    # Show errors
    if [[ $line == *"ERROR"* ]] || [[ $line == *"❌"* ]]; then
        echo -e "${RED}❌ Error: $line${NC}"
    fi
done

echo ""
echo "Monitor stopped."

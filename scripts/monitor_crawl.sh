#!/bin/bash
# Real-time crawl monitoring script for InsightPulse

LOG_FILE="backend.log"
CLEAR_SCREEN=true

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear_and_show() {
    if [ "$CLEAR_SCREEN" = true ]; then
        clear
    fi
}

show_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           InsightPulse - Real-time Crawl Monitor               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_status() {
    clear_and_show
    show_header
    
    echo -e "${YELLOW}⏱ Last Update: $(date '+%H:%M:%S')${NC}\n"
    
    # Check backend health
    echo -e "${BLUE}📊 BACKEND STATUS:${NC}"
    if pgrep -af "uvicorn.*8001" > /dev/null; then
        echo -e "  ${GREEN}✓ Backend Running (Port 8001)${NC}"
    else
        echo -e "  ${RED}✗ Backend Stopped${NC}"
    fi
    echo ""
    
    # Active crawls
    echo -e "${BLUE}🔄 ACTIVE CRAWLS:${NC}"
    tail -100 "$LOG_FILE" 2>/dev/null | grep -E "Starting crawl|Running.*actor|Auto-crawl|Running YouTube|Running.*LinkedIn|Dataset validation error" | tail -5 | while read line; do
        if echo "$line" | grep -q "ERROR\|error"; then
            echo -e "  ${RED}✗ $line${NC}"
        elif echo "$line" | grep -q "Running\|Auto-crawl"; then
            echo -e "  ${GREEN}▶ $line${NC}"
        else
            echo -e "  ${YELLOW}• $line${NC}"
        fi
    done
    echo ""
    
    # Latest saved files
    echo -e "${BLUE}💾 LATEST SAVED DATA:${NC}"
    ls -lt data/smart_crawlers/*/*.csv 2>/dev/null | head -3 | awk '{print "  " $NF " (" $6 " " $7 " " $8 ")"}' || echo "  No files yet"
    echo ""
    
    # Analyzed files
    echo -e "${BLUE}📈 ANALYZED RESULTS:${NC}"
    ls -lt data/analyzed/Sentiment_Emotion_*.csv 2>/dev/null | head -3 | awk '{print "  " $NF " (" $6 " " $7 " " $8 ")"}' || echo "  No files yet"
    echo ""
    
    # Post/Comment counts
    echo -e "${BLUE}📊 RECORD COUNTS (Latest):${NC}"
    tail -50 "$LOG_FILE" 2>/dev/null | grep -E "posts \+|comments|total records" | tail -3 | while read line; do
        echo -e "  ${GREEN}$line${NC}"
    done
    echo ""
    
    # Sentiment summary
    echo -e "${BLUE}💭 SENTIMENT DISTRIBUTION:${NC}"
    tail -100 "$LOG_FILE" 2>/dev/null | grep "Sentiment distribution:" | tail -1 | sed 's/.*Sentiment distribution: /  /' || echo "  No data yet"
    echo ""
    
    # Active processes
    echo -e "${BLUE}🔗 ACTIVE PROCESSES:${NC}"
    pgrep -af "curl.*8001|uvicorn" | wc -l | awk '{print "  Process count: " $1}'
    
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
}

# Main loop
while true; do
    show_status
    sleep 5
done

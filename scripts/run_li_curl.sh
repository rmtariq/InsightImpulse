#!/bin/bash
curl -sS -m 1200 -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"budi95","platforms":["linkedin"],"analysis_type":"social_listening","dataset_size":50,"max_results":50,"date_range":"30days","include_sentiment":true}' \
  -o /tmp/li_result2.json \
  -w "HTTP:%{http_code}\n" > /tmp/curl_status.txt 2>&1
echo "DONE" >> /tmp/curl_status.txt

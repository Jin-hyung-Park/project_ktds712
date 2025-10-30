#!/bin/bash

# SR Impact Navigator - Azure App Service Startup Script

echo "🚀 Starting SR Impact Navigator..."

# Python 경로 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Streamlit 설정
export STREAMLIT_SERVER_PORT=8000
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 애플리케이션 실행
echo "📱 Launching Streamlit application..."
streamlit run app_streamlit.py \
  --server.port=8000 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
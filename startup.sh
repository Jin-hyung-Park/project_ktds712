#!/bin/bash
# Azure App Service 시작 스크립트
cd /home/site/wwwroot
streamlit run app_streamlit.py --server.port=8000 --server.address=0.0.0.0

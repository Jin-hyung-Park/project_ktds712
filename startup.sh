#!/bin/bash
# Azure App Service 시작 스크립트
cd /home/site/wwwroot
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
streamlit run app_streamlit.py --server.port=8000 --server.address=0.0.0.0

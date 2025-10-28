"""
SR Impact Navigator+ 설정 파일
"""
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class Config:
    """애플리케이션 설정"""
    
    # Azure AI Search 설정
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://your-search-service.search.windows.net")
    AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "your-search-key")
    AZURE_SEARCH_INDEX_SR = "sr-index"
    AZURE_SEARCH_INDEX_INCIDENT = "incident-index"
    
    # Azure OpenAI 설정
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-openai-service.openai.azure.com")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "your-openai-key")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    # 리스크 계산 가중치
    RISK_WEIGHTS = {
        "sr_similarity": 0.25,
        "incident_correlation": 0.25,
        "system_importance": 0.25,
        "time_sensitivity": 0.15,
        "sr_complexity": 0.10
    }
    
    # 리스크 등급 임계값
    RISK_THRESHOLDS = {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.2
    }
    
    # 시스템 중요도 등급
    SYSTEM_IMPORTANCE_LEVELS = {
        "Critical": 1.0,
        "High": 0.8,
        "Medium": 0.6,
        "Low": 0.4,
        "Minimal": 0.2
    }

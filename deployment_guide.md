# Azure Web App 배포 가이드

## 개요
SR Impact Navigator Streamlit 앱을 Azure App Service에 배포하는 방법을 설명합니다.

## 1. 배포 준비

### 1.1 필요한 파일들
```
project_ktds712/
├── app_streamlit.py          # 메인 Streamlit 앱
├── requirements.txt          # Python 의존성
├── .env                      # 환경 변수 (보안상 제외)
├── src/                      # 소스 코드
│   ├── config.py
│   ├── integrated_risk_analyzer.py
│   ├── search_rag.py
│   └── incident_rag.py
└── startup.sh               # 시작 스크립트 (생성 필요)
```

### 1.2 startup.sh 생성
```bash
#!/bin/bash
# Azure App Service 시작 스크립트
cd /home/site/wwwroot
streamlit run app_streamlit.py --server.port=8000 --server.address=0.0.0.0
```

## 2. Azure CLI를 사용한 배포

### 2.1 Azure CLI 설치 및 로그인
```bash
# Azure CLI 설치 (macOS)
brew install azure-cli

# 로그인
az login

# 구독 설정
az account set --subscription "your-subscription-id"
```

### 2.2 리소스 그룹 및 App Service 계획 생성
```bash
# 변수 설정
RESOURCE_GROUP="sr-impact-navigator-rg"
APP_NAME="sr-impact-navigator"
LOCATION="koreacentral"
PLAN_NAME="sr-impact-navigator-plan"

# 리소스 그룹 생성
az group create --name $RESOURCE_GROUP --location $LOCATION

# App Service 계획 생성 (Linux, Python 3.11)
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux
```

### 2.3 Web App 생성
```bash
# Web App 생성
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --name $APP_NAME \
    --runtime "PYTHON|3.11"
```

### 2.4 환경 변수 설정
```bash
# Azure Search 설정
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    AZURE_SEARCH_ENDPOINT="your-search-endpoint" \
    AZURE_SEARCH_KEY="your-search-key"

# Azure OpenAI 설정
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    AZURE_OPENAI_ENDPOINT="your-openai-endpoint" \
    AZURE_OPENAI_KEY="your-openai-key" \
    AZURE_OPENAI_DEPLOYMENT="your-deployment-name"

# Azure OpenAI 임베딩 설정
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    AZURE_EMBEDDING_OPENAI_ENDPOINT="your-embedding-endpoint" \
    AZURE_EMBEDDING_OPENAI_KEY="your-embedding-key" \
    AZURE_EMBEDDING_OPENAI_DEPLOYMENT="your-embedding-deployment"
```

## 3. 배포 방법

### 3.1 방법 1: Azure CLI를 사용한 직접 배포
```bash
# 프로젝트 디렉토리로 이동
cd /Users/Jinhyung_1/SR_Impact_Navigator/project_ktds712

# ZIP 파일 생성
zip -r app.zip . -x "*.git*" "*.DS_Store*" "__pycache__/*" "*.pyc"

# Web App에 배포
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --src app.zip
```

### 3.2 방법 2: GitHub Actions를 사용한 자동 배포
```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure Web App

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python version
      uses: actions/setup-python@v1
      with:
        python-version: '3.11'
    
    - name: Create and start deployment
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'sr-impact-navigator'
        slot-name: 'production'
        publish-profile: ${{ secrets.AZUREAPPSERVICE_PUBLISHPROFILE }}
```

## 4. 설정 파일 수정

### 4.1 app_streamlit.py 수정
```python
# 포트 설정을 Azure App Service에 맞게 수정
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    main()
```

### 4.2 requirements.txt 확인
```
streamlit>=1.28.0
azure-search-documents>=11.4.0
azure-ai-textanalytics>=5.3.0
azure-identity>=1.15.0
pandas>=2.0.0
numpy>=1.24.0
openai>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
scikit-learn>=1.3.0
reportlab>=4.0.0
matplotlib>=3.7.0
plotly>=5.17.0
seaborn>=0.12.0
```

## 5. 배포 후 확인

### 5.1 로그 확인
```bash
# 실시간 로그 확인
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME

# 로그 다운로드
az webapp log download --resource-group $RESOURCE_GROUP --name $APP_NAME
```

### 5.2 앱 상태 확인
```bash
# 앱 상태 확인
az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "state"

# 앱 URL 확인
az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "defaultHostName"
```

## 6. 보안 고려사항

### 6.1 환경 변수 보안
- `.env` 파일을 Git에 커밋하지 않음
- Azure Key Vault 사용 권장
- App Service 설정에서 환경 변수 관리

### 6.2 네트워크 보안
- VNet 통합 고려
- Private Endpoint 사용
- IP 제한 설정

## 7. 모니터링 및 유지보수

### 7.1 Application Insights 설정
```bash
# Application Insights 생성
az monitor app-insights component create \
    --app sr-impact-navigator-insights \
    --location koreacentral \
    --resource-group $RESOURCE_GROUP

# Web App에 연결
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY="your-instrumentation-key"
```

### 7.2 자동 스케일링 설정
```bash
# 자동 스케일링 규칙 생성
az monitor autoscale create \
    --resource-group $RESOURCE_GROUP \
    --resource $APP_NAME \
    --resource-type Microsoft.Web/sites \
    --name sr-impact-navigator-autoscale \
    --min-count 1 \
    --max-count 3 \
    --count 1
```

## 8. 트러블슈팅

### 8.1 일반적인 문제들
- **포트 오류**: 8000 포트 사용 확인
- **모듈 import 오류**: requirements.txt 확인
- **환경 변수 오류**: App Service 설정 확인
- **메모리 부족**: App Service 계획 업그레이드

### 8.2 로그 분석
```bash
# 에러 로그 필터링
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME | grep -i error

# 특정 시간대 로그
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME --start-time "2024-01-01T00:00:00"
```

## 9. 비용 최적화

### 9.1 App Service 계획 선택
- **개발/테스트**: B1 (1 vCPU, 1.75GB RAM)
- **프로덕션**: P1V2 (1 vCPU, 3.5GB RAM)
- **고성능**: P2V2 (2 vCPU, 7GB RAM)

### 9.2 자동 스케일링
- 사용량에 따른 자동 스케일링
- 비용 절약을 위한 최소 인스턴스 설정

## 10. 배포 스크립트

### 10.1 전체 배포 스크립트
```bash
#!/bin/bash
# deploy.sh

# 변수 설정
RESOURCE_GROUP="sr-impact-navigator-rg"
APP_NAME="sr-impact-navigator"
LOCATION="koreacentral"
PLAN_NAME="sr-impact-navigator-plan"

echo "🚀 SR Impact Navigator 배포 시작..."

# 1. 리소스 그룹 생성
echo "📁 리소스 그룹 생성 중..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. App Service 계획 생성
echo "📋 App Service 계획 생성 중..."
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux

# 3. Web App 생성
echo "🌐 Web App 생성 중..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --name $APP_NAME \
    --runtime "PYTHON|3.11"

# 4. 환경 변수 설정
echo "⚙️ 환경 변수 설정 중..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    AZURE_SEARCH_ENDPOINT="your-search-endpoint" \
    AZURE_SEARCH_KEY="your-search-key" \
    AZURE_OPENAI_ENDPOINT="your-openai-endpoint" \
    AZURE_OPENAI_KEY="your-openai-key" \
    AZURE_OPENAI_DEPLOYMENT="your-deployment-name" \
    AZURE_EMBEDDING_OPENAI_ENDPOINT="your-embedding-endpoint" \
    AZURE_EMBEDDING_OPENAI_KEY="your-embedding-key" \
    AZURE_EMBEDDING_OPENAI_DEPLOYMENT="your-embedding-deployment"

# 5. 앱 배포
echo "📦 앱 배포 중..."
zip -r app.zip . -x "*.git*" "*.DS_Store*" "__pycache__/*" "*.pyc"
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --src app.zip

echo "✅ 배포 완료!"
echo "🌐 앱 URL: https://$APP_NAME.azurewebsites.net"
```

이 가이드를 따라하면 Azure Web App에 Streamlit 앱을 성공적으로 배포할 수 있습니다.

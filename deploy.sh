#!/bin/bash
# SR Impact Navigator Azure Web App 배포 스크립트

# 변수 설정
RESOURCE_GROUP="sr-impact-navigator-v2-rg"
APP_NAME="sr-impact-navigator-v2"
LOCATION="koreacentral"
PLAN_NAME="sr-impact-navigator-v2-plan"

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
echo "⚠️  실제 환경 변수 값으로 교체해주세요!"
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
echo ""
echo "📋 다음 단계:"
echo "1. Azure Portal에서 환경 변수 값을 실제 값으로 업데이트"
echo "2. 앱이 정상 작동하는지 확인"
echo "3. 로그를 확인하여 오류가 없는지 점검"

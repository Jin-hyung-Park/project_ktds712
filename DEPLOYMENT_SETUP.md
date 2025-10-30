# Azure 자동 배포 설정 가이드

GitHub에 코드가 푸시될 때마다 자동으로 Azure App Service에 배포되도록 설정하는 방법입니다.

## 🚀 설정 방법

### 1. Azure App Service 생성

```bash
# Azure CLI로 App Service 생성
az group create --name rg-sr-impact-navigator --location koreacentral
az appservice plan create --name plan-sr-impact-navigator --resource-group rg-sr-impact-navigator --sku B1 --is-linux
az webapp create --resource-group rg-sr-impact-navigator --plan plan-sr-impact-navigator --name sr-impact-navigator --runtime "PYTHON|3.11"
```

### 2. GitHub Secrets 설정

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 secrets를 추가하세요:

#### **필수 Secrets**
- `AZURE_APP_NAME`: Azure App Service 이름 (예: sr-impact-navigator)
- `AZURE_PUBLISH_PROFILE`: Azure App Service의 Publish Profile

#### **Publish Profile 다운로드 방법**
1. Azure Portal에서 App Service로 이동
2. "Get publish profile" 클릭
3. 다운로드된 파일 내용을 복사하여 `AZURE_PUBLISH_PROFILE` secret에 저장

### 3. 환경 변수 설정

Azure App Service에서 다음 환경 변수를 설정하세요:

```bash
# Azure CLI로 환경 변수 설정
az webapp config appsettings set --resource-group rg-sr-impact-navigator --name sr-impact-navigator --settings \
  AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net" \
  AZURE_SEARCH_KEY="your-search-key" \
  AZURE_OPENAI_ENDPOINT="https://your-openai-service.openai.azure.com" \
  AZURE_OPENAI_KEY="your-openai-key" \
  AZURE_OPENAI_DEPLOYMENT="gpt-4"
```

또는 Azure Portal에서:
1. App Service > Configuration > Application settings
2. 각 환경 변수 추가

## 📋 배포 워크플로우

### **GitHub Actions (권장)**
- 파일: `.github/workflows/azure-deploy-advanced.yml`
- 트리거: main 브랜치에 push 시 자동 실행
- 기능:
  - Python 3.11 환경 설정
  - 의존성 설치 및 캐싱
  - 애플리케이션 테스트
  - Azure App Service 자동 배포

### **Azure DevOps (대안)**
- 파일: `azure-pipelines.yml`
- Azure DevOps에서 파이프라인 생성 후 사용

## 🔧 배포 프로세스

1. **코드 푸시**: main 브랜치에 코드 푸시
2. **자동 빌드**: GitHub Actions가 자동으로 실행
3. **테스트**: 애플리케이션 import 및 기본 테스트
4. **패키징**: 필요한 파일들만 패키징
5. **배포**: Azure App Service에 자동 배포
6. **확인**: 배포 완료 후 URL로 접속 가능

## 🌐 배포 후 접속

배포가 완료되면 다음 URL로 접속할 수 있습니다:
```
https://sr-impact-navigator.azurewebsites.net
```

## 🔍 배포 상태 확인

### GitHub Actions에서 확인
1. GitHub 저장소 > Actions 탭
2. 최근 워크플로우 실행 상태 확인
3. 실패 시 로그 확인하여 문제 해결

### Azure Portal에서 확인
1. Azure Portal > App Service
2. Deployment Center에서 배포 히스토리 확인
3. Logs에서 애플리케이션 로그 확인

## 🛠️ 문제 해결

### **일반적인 문제들**

1. **배포 실패**
   - GitHub Secrets 설정 확인
   - Azure App Service 상태 확인
   - 로그에서 구체적인 오류 메시지 확인

2. **애플리케이션 실행 오류**
   - 환경 변수 설정 확인
   - Python 버전 호환성 확인
   - 의존성 패키지 설치 확인

3. **성능 문제**
   - App Service 플랜 업그레이드 고려
   - 캐싱 설정 확인
   - 데이터베이스 연결 최적화

## 📊 모니터링

### **Azure Application Insights 설정**
```bash
# Application Insights 리소스 생성
az monitor app-insights component create --app sr-impact-navigator --location koreacentral --resource-group rg-sr-impact-navigator

# App Service에 연결
az webapp config appsettings set --resource-group rg-sr-impact-navigator --name sr-impact-navigator --settings \
  APPINSIGHTS_INSTRUMENTATIONKEY="your-instrumentation-key"
```

## 🔄 롤백 방법

문제가 발생한 경우 이전 버전으로 롤백:

1. **Azure Portal에서**:
   - App Service > Deployment Center
   - 이전 배포 선택 후 "Redeploy"

2. **GitHub에서**:
   - Actions 탭에서 이전 성공한 워크플로우 선택
   - "Re-run jobs" 클릭

## 📈 확장성

### **스케일링**
- 수동 스케일링: Azure Portal에서 인스턴스 수 조정
- 자동 스케일링: CPU/메모리 기반 자동 스케일링 설정

### **고가용성**
- 여러 지역에 배포
- Load Balancer 설정
- 데이터베이스 복제

---

**자동 배포 설정이 완료되면 코드를 푸시할 때마다 자동으로 Azure에 배포됩니다!** 🚀

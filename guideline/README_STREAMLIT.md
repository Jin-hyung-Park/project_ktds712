# SR Impact Navigator - Streamlit UI

## 개요
Streamlit을 사용한 웹 기반 개발 리스크 분석 시스템입니다. 개발 요구사항을 입력하면 연관 SR과 장애 정보를 검색하여 FMEA 기반 위험도 분석을 수행합니다.

## 주요 기능

### 📝 개발 요구사항 입력
- **제목**: 개발 과제의 제목 입력
- **상세 내용**: 개발 과제의 구체적인 내용, 요구사항, 목표 등 입력

### 🔍 리스크 분석
- **연관 SR 검색**: 입력된 개발 과제와 관련된 Service Request 검색
- **유사 장애 검색**: 과거 발생한 유사한 장애 사례 검색
- **FMEA 분석**: OpenAI를 통한 체계적인 위험도 분석

### 📊 분석 결과 표시
- **위험도 요약**: 전체 위험 요소, 고위험/중위험/저위험 요소 개수, 전체 위험도 점수
- **참조 정보**: 연관 SR과 장애 정보의 요약
- **위험 요소 상세**: 각 위험 요소의 원인, 영향, RPN, 완화 방안
- **개발 가이드라인**: 개발 시 고려사항
- **모니터링 권장사항**: 운영 시 모니터링 포인트

## 실행 방법

### 1. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일)
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_KEY=your-search-key
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_EMBEDDING_OPENAI_ENDPOINT=your-embedding-endpoint
AZURE_EMBEDDING_OPENAI_KEY=your-embedding-key
AZURE_EMBEDDING_OPENAI_DEPLOYMENT=your-embedding-deployment
```

### 2. Streamlit 앱 실행
```bash
streamlit run app_streamlit.py
```

### 3. 웹 브라우저에서 접속
- 기본 URL: `http://localhost:8501`
- 자동으로 브라우저가 열리지 않으면 위 URL로 직접 접속

## 사용법

### 1. 개발 요구사항 입력
- **제목**: 간단하고 명확한 개발 과제 제목 입력
- **상세 내용**: 개발하고자 하는 기능의 구체적인 내용 입력
  - 예: "가입일 기준 월할 계산 기능 개발"
  - 예: "사용자가 가입한 날짜를 기준으로 월 단위로 요금을 할인 계산하는 기능을 개발합니다. 기존 일할 계산 로직을 월할 계산으로 변경하고, 할인 정책을 적용해야 합니다."

### 2. 분석 설정 (사이드바)
- **연관 SR 검색 수**: 검색할 연관 SR의 최대 개수 (1-10)
- **유사 장애 검색 수**: 검색할 유사 장애의 최대 개수 (1-10)

### 3. 분석 실행
- "🔍 리스크 분석 시작" 버튼 클릭
- 분석 중에는 스피너가 표시됩니다
- 분석 완료 후 결과가 자동으로 표시됩니다

### 4. 결과 해석
- **위험도 점수**: 0-10점 (높을수록 위험)
- **RPN**: 발생도 × 심각도 × 탐지율 (100 이상 고위험)
- **완화 방안**: 각 위험 요소에 대한 구체적인 대응 방안

## 화면 구성

### 메인 화면
- **헤더**: 시스템 제목 및 설명
- **입력 폼**: 개발 과제 제목 및 상세 내용 입력
- **분석 버튼**: 리스크 분석 실행

### 사이드바
- **분석 설정**: 검색할 SR/장애 개수 조정
- **시스템 정보**: FMEA 기반 분석 안내

### 결과 화면
- **위험도 요약 카드**: 주요 지표를 한눈에 확인
- **참조 정보**: 연관 SR과 장애 정보 요약
- **위험 요소**: 상세한 위험 분석 및 완화 방안
- **가이드라인**: 개발 및 모니터링 권장사항

## 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python
- **AI/ML**: Azure OpenAI, Azure AI Search
- **Data**: Azure Search Index (SR, Incident)

## 주의사항
- 분석 결과는 참고용이며, 실제 개발 시에는 추가적인 검토가 필요합니다
- Azure 서비스 연결이 필요하므로 네트워크 연결을 확인하세요
- 대용량 데이터 분석 시 시간이 오래 걸릴 수 있습니다

# SR Impact Navigator - 개발 리스크 분석 시스템

**FMEA 기반 개발 과제 위험도 분석 및 가이드 제공 AI 시스템**

---

## 🚀 프로젝트 개요

SR Impact Navigator는 개발 요구사항을 입력받아 연관 SR과 유사 장애를 검색하고, FMEA(Failure Mode and Effects Analysis) 기반으로 체계적인 위험도 분석을 수행하는 Streamlit 기반 웹 애플리케이션입니다.

---

## 🎯 주요 기능

### 📝 **개발 요구사항 입력**
- 개발 과제 제목 및 상세 내용 입력
- 직관적인 웹 인터페이스 제공

### 🔍 **지능형 검색 및 분석**
- **연관 SR 검색**: Azure AI Search를 통한 관련 Service Request 검색
- **유사 장애 검색**: 과거 발생한 유사한 장애 사례 검색
- **FMEA 분석**: OpenAI를 통한 체계적인 위험도 분석

### 📊 **종합 리스크 분석 결과**
- **위험도 요약**: 전체 위험 요소, 고위험/중위험/저위험 요소 개수
- **참조 정보**: 연관 SR과 장애 정보의 요약 표시
- **위험 요소 상세**: 각 위험 요소의 원인, 영향, RPN, 완화 방안
- **개발 가이드라인**: 개발 시 고려사항 제공
- **모니터링 권장사항**: 운영 시 모니터링 포인트 제시

---

## 🏗️ 시스템 아키텍처

```text
[사용자 입력: 개발 과제 설명]
        ↓
[Streamlit UI - app_streamlit.py]
        ↓
[통합 리스크 분석기 - integrated_risk_analyzer.py]
  1️⃣ 연관 SR 검색 (search_rag.py)
  2️⃣ 유사 장애 검색 (incident_rag.py)
  3️⃣ FMEA 기반 위험도 분석 (OpenAI GPT-4)
        ↓
[분석 결과 시각화]
  → 위험도 요약 + 상세 분석 + 가이드라인 제공
```

---

## 🧮 FMEA 기반 위험도 분석

### **RPN (Risk Priority Number) 계산**
- **발생 가능성 (Occurrence)**: 1-10점 (발생 빈도)
- **심각도 (Severity)**: 1-10점 (영향 정도)  
- **탐지 가능성 (Detection)**: 1-10점 (사전 탐지 가능성)
- **RPN = 발생 가능성 × 심각도 × 탐지 가능성**

### **위험도 등급 분류**

| RPN 범위 | 위험도 | 색상 | 조치 |
|----------|--------|------|------|
| 200+ | 🔴 High | 빨강 | 즉시 검토 필요 |
| 100-199 | 🟡 Medium | 노랑 | 우선 검토 |
| 50-99 | 🟢 Low | 초록 | 일반 검토 |
| 50 미만 | ⚪ Minimal | 회색 | 모니터링 |

---

## 🚀 빠른 시작

### **1. 환경 설정**

```bash
# 저장소 클론
git clone https://github.com/Jin-hyung-Park/project_ktds712.git
cd project_ktds712

# 의존성 설치
pip install -r requirements.txt
```

### **2. 환경 변수 설정**

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```bash
# Azure AI Search 설정
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key

# Azure OpenAI 설정
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Azure Embedding 설정 (선택사항)
AZURE_EMBEDDING_OPENAI_ENDPOINT=https://your-embedding-service.openai.azure.com
AZURE_EMBEDDING_OPENAI_KEY=your-embedding-key
AZURE_EMBEDDING_OPENAI_DEPLOYMENT=text-embedding-ada-002
```

### **3. 애플리케이션 실행**

```bash
streamlit run app_streamlit.py
```

웹 브라우저에서 `http://localhost:8501`로 접속하세요.

---

## 📁 프로젝트 구조

```
project_ktds712/
├── app_streamlit.py              # 🎯 메인 Streamlit 애플리케이션
├── src/
│   ├── integrated_risk_analyzer.py  # 🔧 통합 리스크 분석기
│   ├── search_rag.py               # 🔍 SR 검색 RAG 모듈
│   ├── incident_rag.py             # 🚨 장애 검색 RAG 모듈
│   ├── config.py                   # ⚙️ 설정 관리
│   └── azure_search_client.py      # 🔗 Azure Search 클라이언트
├── pdfs/                         # 📄 PDF 데이터 파일들
│   ├── incident/                 # 🚨 장애 PDF (20개)
│   └── sr/                       # 📋 SR PDF (16개)
├── guideline/                    # 📚 가이드라인 문서들
│   ├── AI_RISK_EVALUATION.md
│   ├── INCIDENT_RAG_README.md
│   ├── README_STREAMLIT.md
│   ├── SEARCH_ENGINE_IMPROVEMENT.md
│   └── deployment_guide.md
├── reference/                    # 📖 참고용 Jupyter 노트북들
│   ├── 01.azure-search-quickstart.ipynb
│   ├── 02.Quickstart-rag.ipynb
│   └── 04.vector-search-quickstart.ipynb
├── sample_incident_data.json     # 📊 샘플 장애 데이터
├── sample_sr_data.json          # 📋 샘플 SR 데이터
├── requirements.txt              # 📦 Python 의존성
└── README.md                     # 📖 프로젝트 문서
```

---

## 💡 사용법

### **1. 개발 요구사항 입력**
- **제목**: 개발 과제의 간단하고 명확한 제목 입력
- **상세 내용**: 개발하고자 하는 기능의 구체적인 내용 입력

### **2. 분석 설정 조정**
- **연관 SR 검색 수**: 검색할 연관 SR의 최대 개수 (1-10)
- **유사 장애 검색 수**: 검색할 유사 장애의 최대 개수 (1-10)

### **3. 리스크 분석 실행**
- "🔍 리스크 분석 시작" 버튼 클릭
- AI가 연관 SR과 장애를 검색하고 FMEA 분석 수행

### **4. 결과 확인**
- **위험도 요약**: 전체 위험 요소 개수 및 위험도 점수
- **참조 정보**: 연관 SR과 장애 정보 요약
- **위험 요소 상세**: 각 위험 요소의 원인, 영향, RPN, 완화 방안
- **개발 가이드라인**: 개발 시 고려사항
- **모니터링 권장사항**: 운영 시 모니터링 포인트

---

## 🛠️ 기술 스택

| 기술 | 용도 | 버전 |
|------|------|------|
| **Streamlit** | 웹 UI 프레임워크 | 1.28.0+ |
| **Azure AI Search** | 벡터 검색 및 의미 검색 | 11.4.0+ |
| **Azure OpenAI** | GPT-4 기반 FMEA 분석 | 1.0.0+ |
| **LangChain** | RAG 파이프라인 | 0.1.0+ |
| **Python** | 백엔드 언어 | 3.11+ |

---

## 📊 데이터 소스

### **PDF 데이터 (36개 파일)**
- **장애 PDF**: `pdfs/incident/` (20개) - 실제 장애 보고서
- **SR PDF**: `pdfs/sr/` (16개) - 실제 Service Request 문서

### **샘플 JSON 데이터**
- **장애 데이터**: `sample_incident_data.json` - 구조화된 장애 정보
- **SR 데이터**: `sample_sr_data.json` - 구조화된 SR 정보

---

## 🔧 설정 없이 실행

Azure 리소스가 없는 경우에도 실행 가능합니다:
- **AI Search**: 로컬 텍스트 유사도 검색으로 자동 폴백
- **OpenAI**: 규칙 기반 리스크 평가로 자동 폴백

---

## 📈 기대 효과

| 항목 | 기존 방식 | 개선된 방식 | 효과 |
|------|-----------|-------------|------|
| **리스크 정확도** | 주관적 판단 | FMEA 기반 과학적 분석 | 🎯 **정확도 30% 향상** |
| **의사결정 지원** | 경험 기반 | 데이터 기반 객관적 평가 | 📊 **객관적 우선순위** |
| **리스크 관리** | 사후 대응 | 예측형 리스크 식별 | ⚡ **조기 대응 가능** |
| **자동화** | 수동 검토 | AI 기반 자동 분석 | ⏱️ **업무 효율 50% 향상** |

---

## 📚 참고 자료

### **가이드라인 문서**
- [AI 리스크 평가 가이드](guideline/AI_RISK_EVALUATION.md)
- [장애 RAG 시스템 문서](guideline/INCIDENT_RAG_README.md)
- [Streamlit 앱 사용법](guideline/README_STREAMLIT.md)
- [검색 엔진 개선 문서](guideline/SEARCH_ENGINE_IMPROVEMENT.md)
- [배포 가이드](guideline/deployment_guide.md)

### **참고용 노트북**
- [Azure Search 빠른 시작](reference/01.azure-search-quickstart.ipynb)
- [RAG 빠른 시작](reference/02.Quickstart-rag.ipynb)
- [벡터 검색 빠른 시작](reference/04.vector-search-quickstart.ipynb)

---

## 🚀 배포

### **Azure App Service 배포**

```bash
# 배포 스크립트 실행
chmod +x deploy.sh
./deploy.sh
```

### **로컬 Docker 실행**

```bash
# Docker 이미지 빌드
docker build -t sr-impact-navigator .

# 컨테이너 실행
docker run -p 8501:8501 sr-impact-navigator
```

---

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

**SR Impact Navigator** - 개발 리스크를 사전에 예측하고 관리하는 AI 기반 솔루션 🚀
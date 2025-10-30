# 장애 검색 RAG 시스템

`search_rag.py`의 구조를 준용하여 구현한 장애(Incident) 관련 벡터 검색 기능입니다.

## 🚀 주요 기능

### 1. 장애 검색 및 분석
- **텍스트 검색**: 키워드 기반 장애 검색
- **벡터 검색**: 의미적 유사성 기반 검색 (임베딩 모델 필요)
- **하이브리드 검색**: 텍스트 + 벡터 검색 조합
- **AI 분석**: LLM을 통한 장애 분석 및 해결 방안 제시

### 2. 장애 ID 기반 검색
- 특정 장애 ID로 관련 청크 검색
- 장애 상세 정보 조회

## 📁 파일 구조

```
src/
├── incident_rag.py          # 장애 검색 RAG 시스템 메인 모듈
└── search_rag.py           # SR 검색 RAG 시스템 (참조)

example_incident_search.py   # 사용 예시 스크립트
```

## 🔧 사용 방법

### 1. 기본 사용법

```python
from src.incident_rag import search_related_incidents, search_incident_by_id

# 연관 장애 검색
result = search_related_incidents(
    query="로그인 오류",
    top_k=5,
    use_llm=True,
    search_mode="text"  # "text", "vector", "hybrid"
)

print(f"검색 결과: {result['total_count']}개")
print(f"AI 분석: {result['llm_response']}")

# 특정 장애 ID 검색
incident_result = search_incident_by_id("INC-2024-001", top_k=10)
print(f"장애 상세: {incident_result['sources_formatted']}")
```

### 2. 클래스 기반 사용법

```python
from src.incident_rag import IncidentRAGSearch

# 검색기 초기화
searcher = IncidentRAGSearch(
    index_name="rag-inc-ktds712",
    config=config
)

# 검색 실행
result = searcher.search_related_incidents(
    query="데이터베이스 연결 문제",
    top_k=3,
    use_llm=True,
    search_mode="text"
)
```

### 3. 예시 스크립트 실행

```bash
# 기본 검색 테스트
python3 example_incident_search.py

# 대화형 검색
echo "3" | python3 example_incident_search.py
```

## 🔍 검색 모드

### 1. 텍스트 검색 (`search_mode="text"`)
- 키워드 기반 검색
- 가장 안정적이고 빠름
- 기본 모드

### 2. 벡터 검색 (`search_mode="vector"`)
- 의미적 유사성 기반 검색
- 임베딩 모델 필요
- **현재 Azure Search SDK에서 vector_queries 미지원으로 텍스트 검색으로 자동 대체**

### 3. 하이브리드 검색 (`search_mode="hybrid"`)
- 텍스트 + 벡터 검색 조합
- 최고의 검색 품질
- **현재 Azure Search SDK에서 vector_queries 미지원으로 텍스트 검색으로 자동 대체**

## 📊 인덱스 구조

장애 인덱스 (`rag-inc-ktds712`)는 다음 필드로 구성됩니다:

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `chunk_id` | String (Key) | 청크 고유 ID |
| `parent_id` | String | 장애 ID |
| `chunk` | String | 청크 내용 |
| `title` | String | 장애 제목 |
| `text_vector` | Collection(Single) | 텍스트 벡터 (임베딩) |

## 🤖 AI 분석 기능

### 프롬프트 템플릿
```python
INCIDENT_GROUNDED_PROMPT = """
당신은 장애 분석 및 해결 방안 제시를 위한 전문 어시스턴트입니다.
각 장애에 대해 다음 정보를 포함하여 분석하세요:
- 장애 ID 및 제목
- 장애 유형 및 심각도
- 발생 원인 및 영향 범위
- 해결 방안 및 예방 조치
- 관련 시스템 및 컴포넌트
"""
```

### 분석 결과 예시
```
### 장애 ID 및 제목
- 장애 ID: INC-2024-006
- 제목: 청구서 생성 시스템 장애

### 장애 유형 및 심각도
- 유형: 메모리 부족에 따른 시스템 오류
- 심각도: Medium

### 발생 원인 및 영향 범위
- 원인: 청구서 생성 시 메모리 부족 및 대용량 데이터 처리 로직 오류
- 영향: 1,200명 고객 대상 청구서 일부 미생성

### 해결 방안 및 예방 조치
- 해결: 메모리 사용량 최적화 및 배치 처리 로직 개선
- 예방: 메모리 모니터링 강화, 배치 처리 성능 최적화
```

## ⚙️ 설정

### 환경 변수
```bash
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_KEY=your-search-key
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Config 클래스
```python
from src.config import Config

config = Config()
# config 객체를 함수에 전달하여 사용
```

## 🚨 주의사항

1. **임베딩 모델**: 벡터 검색을 사용하려면 Azure OpenAI에 임베딩 모델이 배포되어 있어야 합니다.
2. **인덱스 이름**: 기본 인덱스명은 `rag-inc-ktds712`입니다.
3. **에러 처리**: 임베딩 모델이 없으면 자동으로 텍스트 검색으로 대체됩니다.

## 📈 성능 최적화

1. **검색 모드 선택**: 상황에 맞는 검색 모드 선택
2. **top_k 조정**: 필요한 만큼의 결과만 요청
3. **LLM 사용 여부**: 빠른 검색이 필요하면 `use_llm=False` 설정

## 🔄 SR 검색과의 차이점

| 구분 | SR 검색 | 장애 검색 |
|------|---------|-----------|
| 인덱스 | `key-sr-ktds712` | `rag-inc-ktds712` |
| 검색 모드 | 텍스트만 | 텍스트/벡터/하이브리드 |
| 필드 구조 | SR 전용 필드 | 청크 기반 구조 |
| 용도 | SR 추천 | 장애 분석 |

## 📝 예시 쿼리

```python
# 일반적인 장애 검색
queries = [
    "로그인 오류 관련 장애",
    "데이터베이스 연결 문제", 
    "메모리 부족으로 인한 서비스 중단",
    "API 응답 지연 문제",
    "인증 시스템 장애"
]

for query in queries:
    result = search_related_incidents(query, top_k=3)
    print(f"쿼리: {query}")
    print(f"결과: {result['total_count']}개")
    print(f"분석: {result['llm_response']}")
```

## 🛠️ 문제 해결

### 1. 임베딩 모델 오류
```
Error code: 404 - DeploymentNotFound
```
→ 텍스트 검색 모드 사용 또는 임베딩 모델 배포

### 2. 인덱스 접근 오류
```
Azure Search 인증 실패
```
→ 환경 변수 및 인덱스명 확인

### 3. 검색 결과 없음
```
Total results found: 0
```
→ 쿼리 키워드 변경 또는 인덱스 데이터 확인

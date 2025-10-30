# 검색 엔진 분리 개선 사항

## 🎯 개선 목적

SR 유사도 검색과 장애 연관도 검색을 분리하여 각각의 특성에 맞게 최적화

## ✅ 주요 개선 사항

### 1. **책임 분리 (Separation of Concerns)**
- **SRSearchEngine**: SR 유사도 검색 전용
- **IncidentSearchEngine**: 장애 연관도 검색 전용
- 각각 독립적인 검색 전략과 알고리즘 적용 가능

### 2. **Azure AI Search 인덱스 분리**
```python
# 설정에서 이미 분리되어 있음
AZURE_SEARCH_INDEX_SR = "sr-index"          # SR 전용 인덱스
AZURE_SEARCH_INDEX_INCIDENT = "incident-index"  # 장애 전용 인덱스
```

### 3. **검색 알고리즘 최적화**

#### **SR 검색 (SRSearchEngine)**
- **텍스트 유사도 (40%)**: SR 제목, 설명, 기술 요구사항 종합
- **시스템 일치도 (15%)**: 동일 시스템 여부
- **컴포넌트 일치도 (25%)**: 영향받는 컴포넌트 공통 여부
- **카테고리 일치도 (10%)**: SR 카테고리 일치
- **우선순위 유사도 (10%)**: 우선순위 레벨 유사성

#### **장애 검색 (IncidentSearchEngine)**
- **시스템 일치도 (30%)**: 동일 시스템 여부
- **컴포넌트 일치도 (30%)**: 관련 컴포넌트 공통 여부
- **텍스트 유사도 (20%)**: 제목, 설명, 근본 원인 포함
- **장애 심각도 가중치 (10%)**: Critical > High > Medium > Low
- **시간 가중치 (10%)**: 최근 장애일수록 높은 가중치

### 4. **추가 분석 정보**

#### **SR 검색 결과**
- `match_factors`: 매치 요소 상세 분석
  - 텍스트 유사도
  - 시스템 일치 여부
  - 컴포넌트 중복 개수

#### **장애 검색 결과**
- `temporal_relevance`: 시간적 관련성 (최근/중기/중장기/과거)
- `risk_factors`: 리스크 요소 분석
  - 심각도
  - 영향받은 사용자 수
  - 장애 지속 시간
  - 비즈니스 임팩트
  - 근본 원인
  - 해결책 존재 여부

## 🔧 사용 방법

### 기본 사용 (기존과 동일)
```python
from src.search_engine import SearchEngine
from src.data_loader import DataLoader

loader = DataLoader()
search_engine = SearchEngine(loader)

# SR 유사도 검색
similar_srs = search_engine.search_similar_srs(query_sr, top_k=5)

# 장애 연관도 검색
related_incidents = search_engine.search_related_incidents(query_sr, top_k=5)
```

### 전용 엔진 직접 접근
```python
# SR 검색 엔진 직접 사용
sr_searcher = search_engine.get_sr_searcher()
similar_srs = sr_searcher.search_similar(query_sr, top_k=5)

# 장애 검색 엔진 직접 사용
incident_searcher = search_engine.get_incident_searcher()
related_incidents = incident_searcher.search_related(query_sr, top_k=5)
```

## 📊 개선 효과

### 1. **검색 정확도 향상**
- 각 데이터 타입에 특화된 알고리즘 적용
- 더 정확한 유사도/연관도 계산

### 2. **유지보수성 향상**
- 책임이 명확히 분리되어 코드 수정 용이
- 각 검색 엔진을 독립적으로 테스트 및 개선 가능

### 3. **확장성 향상**
- 실제 Azure AI Search 연동 시 각 인덱스별 최적화 가능
- 벡터 검색, 필터링, 정렬 등 각각 독립적으로 구성

### 4. **성능 최적화**
- 각 인덱스별로 다른 검색 전략 적용 가능
- 캐싱, 프리페칭 등 개별 최적화

## 🚀 향후 개선 방향

### 1. **Azure AI Search 실제 연동**
```python
# SR 인덱스용 벡터 필드 구성
sr_vector_field = "description_vector"
sr_search_fields = ["title", "description", "technical_requirements"]

# 장애 인덱스용 벡터 필드 구성
incident_vector_field = "description_vector"
incident_search_fields = ["title", "description", "root_cause"]
```

### 2. **하이브리드 검색**
- 키워드 검색 + 벡터 검색 조합
- 필터링 옵션 추가

### 3. **검색 결과 랭킹 개선**
- Learning to Rank 적용
- 사용자 피드백 기반 랭킹 조정


# OpenAI 기반 리스크 평가 기능

## 🎯 개요

FMEA 방법론 기반 리스크 평가를 OpenAI를 활용하여 더 정교하고 맥락을 고려한 평가로 개선했습니다.

## ✨ 주요 특징

### 1. **AI 기반 평가**
- **System Prompt**: FMEA 방법론 기준을 시스템 프롬프트로 제공
- **컨텍스트 기반**: AI Search 결과(유사 SR, 관련 장애)를 참고하여 평가
- **구조화된 출력**: JSON 형식으로 일관된 결과 제공

### 2. **하이브리드 접근법**
- **OpenAI 사용 가능 시**: AI 기반 평가
- **OpenAI 사용 불가 시**: 자동으로 규칙 기반 평가로 폴백

### 3. **풍부한 분석 결과**
- 리스크 점수 및 등급
- AI 평가 근거 설명
- 주요 리스크 요소 식별
- 맥락 기반 권장사항

## 📋 평가 기준 (System Prompt)

```
1. SR 유사도 (25% 가중치)
   - 과거 유사한 SR 존재 여부
   - 유사 SR의 발생 빈도와 결과
   
2. 장애 연관도 (25% 가중치)
   - 관련된 과거 장애 존재 여부
   - 장애 심각도와 빈도
   - 시스템/컴포넌트 일치도
   
3. 시스템 중요도 (25% 가중치)
   - 비즈니스 중요도
   - Critical > High > Medium > Low
   
4. 시간 민감도 (15% 가중치)
   - 최근 관련 장애 여부
   - 최근 30일 내 장애는 높은 가중치
   
5. SR 복잡도 (10% 가중치)
   - 기술 요구사항 복잡도
   - 영향받는 컴포넌트 수
   - 구현 난이도
```

## 🔧 사용 방법

### 1. 환경 설정

`.env` 파일 또는 환경 변수에 Azure OpenAI 설정:

```bash
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 2. 코드 사용

```python
from src.data_loader import DataLoader
from src.search_engine import SearchEngine
from src.ai_risk_evaluator import AIRiskEvaluator

# 컴포넌트 초기화
loader = DataLoader()
search_engine = SearchEngine(loader)
evaluator = AIRiskEvaluator(loader, search_engine)

# SR 리스크 평가
sr = {...}  # SR 데이터
result = evaluator.evaluate_risk(sr, use_openai=True)

print(f"리스크 점수: {result['total_score']:.3f}")
print(f"리스크 등급: {result['risk_level']}")
print(f"평가 근거: {result['reasoning']}")
print(f"권장사항: {result['recommendations']}")
```

### 3. Streamlit UI 사용

1. Streamlit 앱 실행
2. "SR 분석" 페이지 선택
3. SR 선택
4. "🤖 OpenAI 기반 AI 평가 사용" 체크박스 선택 (설정된 경우)
5. "🚀 리스크 분석 실행" 버튼 클릭

## 📊 출력 형식

```json
{
    "evaluation_method": "openai" | "rule_based",
    "total_score": 0.0-1.0,
    "risk_level": "Critical" | "High" | "Medium" | "Low" | "Minimal",
    "components": {
        "sr_similarity": 0.0-1.0,
        "incident_correlation": 0.0-1.0,
        "system_importance": 0.0-1.0,
        "time_sensitivity": 0.0-1.0,
        "sr_complexity": 0.0-1.0
    },
    "reasoning": "AI 평가 근거 설명 (2-3문장)",
    "key_risks": ["주요 리스크 1", "주요 리스크 2"],
    "recommendations": ["권장사항 1", "권장사항 2"],
    "similar_srs": [...],
    "related_incidents": [...]
}
```

## 🎯 장점

### 기존 규칙 기반 vs AI 기반

| 항목 | 규칙 기반 | AI 기반 |
|------|-----------|---------|
| **정확도** | 고정된 공식 | 맥락 이해 가능 |
| **유연성** | 제한적 | 높음 |
| **설명성** | 기본 | 상세한 근거 제공 |
| **커스터마이징** | 코드 수정 필요 | 프롬프트 조정 가능 |
| **비용** | 무료 | API 사용료 발생 |

### AI 기반 평가의 강점

1. **맥락 이해**: 유사 SR과 관련 장애의 관계를 종합적으로 이해
2. **자연어 설명**: 평가 근거를 자연어로 명확히 설명
3. **유연한 기준**: 복잡한 상황에서도 적절한 판단 가능
4. **지속적 개선**: 프롬프트 튜닝으로 지속적인 개선 가능

## ⚠️ 주의사항

1. **비용 관리**: OpenAI API 사용 시 토큰 사용량에 따른 비용 발생
2. **응답 시간**: API 호출로 인한 약간의 지연 (1-3초)
3. **설정 필요**: Azure OpenAI 서비스 및 API 키 설정 필요
4. **폴백 메커니즘**: 설정이 없거나 오류 시 자동으로 규칙 기반 평가 사용

## 🚀 향후 개선 방향

1. **프롬프트 최적화**: 실제 사용 데이터로 프롬프트 개선
2. **캐싱 전략**: 동일 SR에 대한 결과 캐싱
3. **배치 평가**: 여러 SR 일괄 평가 기능
4. **평가 히스토리**: 평가 결과 이력 관리 및 비교
5. **피드백 루프**: 사용자 피드백을 통한 모델 개선


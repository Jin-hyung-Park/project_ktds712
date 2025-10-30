
# SR Impact Navigator+
**SR 변경 영향도 및 장애연관 정량 리스크 기반 개발 과제 평가 AI 시스템 (실구현 기준 README)**

---

## 🌐 Web App 접속 URL
- **(필요시) 배포 URL**: https://sr-impact-navigator.azurewebsites.net

---

## 🚀 프로젝트 개요
- 과거 SR, 장애 데이터를 RAG로 자동 검색하여 FMEA 기반 LLM 정량 평가로 개발 리스크를 분석하고 가이드/권고를 Streamlit UI로 제공

---

## 🛠️ 주요 기능

| 주요 기능            | 역할 및 설명                                                                                   |
|---------------------|--------------------------------------------------------------------------------------------|
| SR 연관 문서 검색      | 입력(개발 목적·상세) 기반 Azure Search 쿼리 생성(LLM 보조) + Top-K 자동 SR 추천               |
| 장애 연관 청크 검색    | 장애 보고서(청크 단위) 벡터/텍스트/하이브리드 기반 유사 장애 탐색, 근본 원인 데이터 취득           |
| FMEA 기반 LLM 위험분석 | RAG 결과로 LLM에 구조적 FMEA(실패모드·원인·영향·점수·RPN·가이드 등) 분석, 위험요소별 JSON 산출  |
| 리스크 요약 및 보정    | LLM 위험요소/점수 등 요약 summary 결과 구동 및 보정                                            |
| 실시간 대시보드 시각화 | Streamlit 기반 위험카드, 주요 위험요소 컬러/expander, 참조SR/장애, 가이드/권장사항 등 시각화      |
| 개발가이드·권장사항 제시| 위험요소별 및 총괄 예방/완화/모니터링 방안 등 다단계 구조적 가이드 자동 제시                   |

---

## 🗂️ 인덱스 구조 (SR/장애 데이터)

- **SR 인덱스(Keyword Search):**
  | 필드명          | 설명           |
  |----------------|--------------|
  | id             | SR 고유 ID     |
  | title          | SR 제목        |
  | description    | SR 상세 내용   |
  | system         | 관련 시스템    |
  | priority       | 우선순위       |
  | category       | 카테고리       |
  | requester      | 요청자        |
  | created_date   | 요청일자       |
  | target_date    | 반영목표일자       |
  | business_impact| 업무영향도       |
  | technical_requirements | 기술요구사항 |
  | affected_components       | 관련모듈 |

- **장애 인덱스(Vector Search):**
  | 필드명     | 설명           |
  |-----------|---------------|
  | chunk_id  | 청크(문단) ID  |
  | parent_id | 문서 식별 ID        |
  | chunk     | 문서 내용 |
  | title     | 문서 제목      |
  | text_vector     | vector 값(1,536차원)          |


---

## 🔄 처리 프로세스

```
[사용자 입력]
   │
   ▼
(개발 요청 목적 + 상세 요구 사항 입력)
   │
   ▼
[Query Builder]
   │
   ▼
[SR RAG 검색]           [장애 RAG 검색]
   │                        │
   └───► (Top-K 결과 취합)◄───┘
               │
               ▼
    [FMEA 기반 LLM 정량분석]
               │
               ▼
 [요약/위험요소/가이드/권장사항 구조화]
               │
               ▼
   [Streamlit 대시보드 시각화]
```

---


## ⚙️ 환경 및 설치
- Python 3.11+ 권장
- requirements.txt 패키지 설치 필수: Azure OpenAI, Azure Search 등 포함
- `.env` 환경변수 (Azure/OpenAI Key 등) 필요, 별도 예제파일 참고
- Azure 자원 미연결시 텍스트 폴백·규칙기반 분석도 일부 지원

---

## 🚩 실제 활용 분석 예시
- (입력) "월정액 요금 계산 기능 개발" + 상세요구 → SR/장애 RAG로 Top-K 자동검색
- (내부) 각 결과를 기반으로 FMEA LLM 구조 프롬프트 자동생성, LLM 분석값(위험요소별 점수·원인·완화책 등) 구조화
- (출력) Streamlit에서 위험카드, 참조 SR/장애 expandable, 가이드/모니터링 등 UX에 맞게 실시간 분석 결과 제공

---

## ✅ 참고
- 본 README는 실 소스 구현 기준으로, 설계 탑다운이 아닌 기능중심 명세임
- 분석/검색/정량화/시각화 모두 소스와 1:1 연계되어 구동됨

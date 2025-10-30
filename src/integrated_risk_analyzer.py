"""
통합 리스크 분석 시스템
연관 SR과 유사 장애를 종합하여 FMEA 기반 리스크 분석 및 개발 가이드 제공
"""
from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.search_rag import search_related_srs
from src.incident_rag import search_related_incidents
from config import Config
from openai import AzureOpenAI


class IntegratedRiskAnalyzer:
    """통합 리스크 분석 클래스"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        초기화
        
        Args:
            config: Config 객체 (None이면 새로 생성)
        """
        self.config = config or Config()
        
        # OpenAI 클라이언트 초기화
        try:
            self.openai_client = AzureOpenAI(
                api_version="2024-12-01-preview",
                azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT,
                api_key=self.config.AZURE_OPENAI_KEY,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {e}")
    
    def analyze_development_risk(self, 
                               development_task: str,
                               sr_top_k: int = 5,
                               incident_top_k: int = 5,
                               use_llm: bool = True) -> Dict[str, Any]:
        """
        개발 과제에 대한 통합 리스크 분석
        
        Args:
            development_task: 개발 과제 설명
            sr_top_k: SR 검색 결과 수
            incident_top_k: 장애 검색 결과 수
            use_llm: LLM을 사용하여 분석 생성 여부
        
        Returns:
            통합 리스크 분석 결과
        """
        try:
            # 1. 연관 SR 검색
            print("🔍 연관 SR 검색 중...")
            sr_result = search_related_srs(
                query=development_task,
                top_k=sr_top_k,
                use_llm=False  # 원본 데이터만 필요
            )
            
            # 2. 유사 장애 검색
            print("🔍 유사 장애 검색 중...")
            incident_result = search_related_incidents(
                query=development_task,
                top_k=incident_top_k,
                search_mode="hybrid",
                use_llm=False  # 원본 데이터만 필요
            )
            
            # 3. 데이터 통합
            integrated_data = {
                "sr_data": {
                    "total_count": sr_result.get("total_count", 0),
                    "documents": sr_result.get("documents", []),
                    "sources_formatted": sr_result.get("sources_formatted", "")
                },
                "incident_data": {
                    "total_count": incident_result.get("total_count", 0),
                    "documents": incident_result.get("documents", []),
                    "sources_formatted": incident_result.get("sources_formatted", "")
                },
                "query": development_task
            }
            
            # 4. FMEA 기반 리스크 분석
            if use_llm:
                risk_analysis = self._perform_fmea_analysis(integrated_data)
                integrated_data["risk_analysis"] = risk_analysis
            
            return integrated_data
            
        except Exception as e:
            raise RuntimeError(f"통합 리스크 분석 실패: {e}")
    
    def _perform_fmea_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """FMEA 기반 리스크 분석 수행"""
        
        fmea_prompt = f"""
당신은 FMEA(Failure Mode and Effects Analysis) 기반 리스크 분석 전문가입니다.
제공된 연관 SR과 유사 장애 정보를 바탕으로 개발 과제에 대한 리스크를 분석하세요.

## 분석 대상
- **개발 과제**: {data['query']}
- **연관 SR 수**: {data['sr_data']['total_count']}개
- **유사 장애 수**: {data['incident_data']['total_count']}개

## 연관 SR 정보
{data['sr_data']['sources_formatted']}

## 유사 장애 정보
{data['incident_data']['sources_formatted']}

## FMEA 분석 요구사항

### 1. 잠재적 실패 모드 (Failure Modes) 식별
연관 SR과 유사 장애를 기반으로 다음 관점에서 실패 모드를 식별하세요:
- 기능적 실패 (Functional Failures)
- 성능적 실패 (Performance Failures)
- 보안적 실패 (Security Failures)
- 사용성 실패 (Usability Failures)
- 호환성 실패 (Compatibility Failures)

### 2. 실패 원인 (Failure Causes) 분석
각 실패 모드에 대한 근본 원인을 분석하세요:
- 기술적 원인 (Technical Causes)
- 설계적 원인 (Design Causes)
- 운영적 원인 (Operational Causes)
- 환경적 원인 (Environmental Causes)

### 3. 실패 영향 (Failure Effects) 평가
각 실패가 미칠 수 있는 영향을 분석하세요:
- 비즈니스 영향 (Business Impact)
- 사용자 영향 (User Impact)
- 시스템 영향 (System Impact)
- 보안 영향 (Security Impact)

### 4. 위험도 평가 (Risk Assessment)
각 실패 모드에 대해 다음 척도로 평가하세요:

**발생 가능성 (Occurrence) - 1~10점**
- 1-2: 매우 낮음 (거의 발생하지 않음)
- 3-4: 낮음 (가끔 발생)
- 5-6: 보통 (때때로 발생)
- 7-8: 높음 (자주 발생)
- 9-10: 매우 높음 (거의 항상 발생)

**심각도 (Severity) - 1~10점**
- 1-2: 매우 낮음 (미미한 영향)
- 3-4: 낮음 (작은 영향)
- 5-6: 보통 (중간 영향)
- 7-8: 높음 (심각한 영향)
- 9-10: 매우 높음 (치명적 영향)

**탐지 가능성 (Detection) - 1~10점**
- 1-2: 매우 높음 (거의 확실히 탐지)
- 3-4: 높음 (높은 확률로 탐지)
- 5-6: 보통 (중간 확률로 탐지)
- 7-8: 낮음 (낮은 확률로 탐지)
- 9-10: 매우 낮음 (거의 탐지 불가)

**RPN (Risk Priority Number) = 발생 가능성 × 심각도 × 탐지 가능성**

### 5. 개발 가이드 및 권장사항
각 위험에 대한 완화 방안을 제시하세요:
- 예방 조치 (Prevention Measures)
- 탐지 조치 (Detection Measures)
- 완화 조치 (Mitigation Measures)
- 모니터링 방안 (Monitoring Strategies)

## 출력 형식

다음 JSON 형식으로 출력하세요:

```json
{{
    "summary": {{
        "total_risks": "총 위험 요소 수",
        "high_risk_count": "고위험 요소 수 (RPN > 100)",
        "medium_risk_count": "중위험 요소 수 (RPN 50-100)",
        "low_risk_count": "저위험 요소 수 (RPN < 50)",
        "overall_risk_score": "전체 위험도 점수 (0-10)"
    }},
    "risk_factors": [
        {{
            "id": "R001",
            "failure_mode": "실패 모드명",
            "failure_cause": "실패 원인",
            "failure_effect": "실패 영향",
            "occurrence": 5,
            "severity": 7,
            "detection": 6,
            "rpn": 210,
            "risk_level": "High",
            "mitigation_measures": [
                "완화 방안 1",
                "완화 방안 2"
            ]
        }}
    ],
    "development_guidelines": [
        "개발 가이드라인 1",
        "개발 가이드라인 2"
    ],
    "monitoring_recommendations": [
        "모니터링 권장사항 1",
        "모니터링 권장사항 2"
    ]
}}
```

위험도 점수는 0-10 척도로 평가하며, 10에 가까울수록 위험도가 높습니다.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {
                        "role": "user",
                        "content": fmea_prompt
                    },
                ],
                temperature=0.3  # 일관된 분석을 위해 낮은 temperature 사용
            )
            
            # JSON 응답 파싱 시도
            try:
                import json
                import re
                
                # 응답에서 JSON 부분만 추출
                content = response.choices[0].message.content
                
                # ```json과 ``` 사이의 내용 추출
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # ```json이 없으면 전체 내용에서 JSON 찾기
                    json_str = content
                
                analysis_result = json.loads(json_str)
            except (json.JSONDecodeError, AttributeError) as e:
                # JSON 파싱 실패 시 텍스트로 반환
                analysis_result = {
                    "raw_response": response.choices[0].message.content,
                    "parse_error": f"JSON 파싱 실패: {e}"
                }
            
            return analysis_result
            
        except Exception as e:
            return {
                "error": f"FMEA 분석 실패: {e}",
                "raw_response": None
            }
    
    def format_risk_report(self, 
                           analysis_result: Dict[str, Any],
                           sr_documents: Optional[List[Dict[str, Any]]] = None,
                           incident_documents: Optional[List[Dict[str, Any]]] = None) -> str:
        """리스크 분석 결과를 포맷팅하여 출력 (참조 SR/장애 요약 포함)"""
        
        if "error" in analysis_result:
            return f"❌ 분석 오류: {analysis_result['error']}"
        
        if "raw_response" in analysis_result and analysis_result.get("parse_error"):
            return f"📋 원본 분석 결과:\n{analysis_result['raw_response']}"
        
        report = []
        report.append("=" * 80)
        report.append("🔍 FMEA 기반 개발 리스크 분석 보고서")
        report.append("=" * 80)
        
        # 요약 정보
        if "summary" in analysis_result:
            summary = analysis_result["summary"]
            report.append(f"\n📊 위험도 요약")
            report.append("-" * 40)
            report.append(f"총 위험 요소: {summary.get('total_risks', 'N/A')}개")
            report.append(f"고위험 요소: {summary.get('high_risk_count', 'N/A')}개 (RPN > 100)")
            report.append(f"중위험 요소: {summary.get('medium_risk_count', 'N/A')}개 (RPN 50-100)")
            report.append(f"저위험 요소: {summary.get('low_risk_count', 'N/A')}개 (RPN < 50)")
            report.append(f"전체 위험도: {summary.get('overall_risk_score', 'N/A')}/10")

        # 참조 SR 요약
        if sr_documents is not None and len(sr_documents) > 0:
            report.append(f"\n📄 참조 SR 요약 (상위 {min(3, len(sr_documents))}건)")
            report.append("-" * 40)
            for i, doc in enumerate(sr_documents[:3], 1):
                sr_id = doc.get('id') or doc.get('SR_ID') or 'N/A'
                title = doc.get('title', 'N/A')
                system = doc.get('system', 'N/A')
                priority = doc.get('priority', 'N/A')
                category = doc.get('category', 'N/A')
                desc = str(doc.get('description', '')).strip()
                if len(desc) > 120:
                    desc = desc[:117] + '...'
                tech = doc.get('technical_requirements', [])
                if isinstance(tech, list):
                    tech_summary = ', '.join(tech[:5])
                else:
                    tech_summary = str(tech)
                if len(tech_summary) > 120:
                    tech_summary = tech_summary[:117] + '...'
                report.append(f"{i}. [{sr_id}] {title} | 시스템:{system} | 우선순위:{priority} | 카테고리:{category}")
                if desc:
                    report.append(f"   - 설명: {desc}")
                if tech_summary and tech_summary != '':
                    report.append(f"   - 기술요구사항: {tech_summary}")

        # 참조 장애 요약
        if incident_documents is not None and len(incident_documents) > 0:
            report.append(f"\n🚨 참조 장애 요약 (상위 {min(3, len(incident_documents))}건)")
            report.append("-" * 40)
            import re
            def _extract_section(text: str, header: str) -> str:
                # 헤더 라인부터 다음 빈 줄/다음 헤더까지 추출
                # 예: '장애 설명', '근본 원인', '해결 방법'
                pattern = rf"{header}\s*\n([\s\S]*?)(\n\n|\n\s*근본 원인|\n\s*해결 방법|\n\s*영향|\n\s*비즈니스 임팩트|\n\s*재발 방지 조치|$)"
                m = re.search(pattern, text)
                if m:
                    return m.group(1).strip()
                return ''
            def _shorten(s: str, n: int = 150) -> str:
                s = s.replace('\n', ' ').strip()
                return (s[:n-3] + '...') if len(s) > n else s
            for i, doc in enumerate(incident_documents[:3], 1):
                title = doc.get('title', 'N/A')
                chunk = str(doc.get('chunk', ''))
                desc = _extract_section(chunk, '장애 설명')
                cause = _extract_section(chunk, '근본 원인')
                fix = _extract_section(chunk, '해결 방법')
                report.append(f"{i}. {title}")
                if desc:
                    report.append(f"   - 장애 설명: {_shorten(desc)}")
                if cause:
                    report.append(f"   - 근본 원인: {_shorten(cause)}")
                if fix:
                    report.append(f"   - 해결 방법: {_shorten(fix)}")
        
        # 위험 요소 상세
        if "risk_factors" in analysis_result:
            report.append(f"\n⚠️ 주요 위험 요소")
            report.append("-" * 40)
            
            for i, risk in enumerate(analysis_result["risk_factors"][:5], 1):  # 상위 5개만 표시
                report.append(f"\n{i}. {risk.get('failure_mode', 'N/A')}")
                report.append(f"   원인: {risk.get('failure_cause', 'N/A')}")
                report.append(f"   영향: {risk.get('failure_effect', 'N/A')}")
                report.append(f"   RPN: {risk.get('rpn', 'N/A')} (발생:{risk.get('occurrence', 'N/A')} × 심각도:{risk.get('severity', 'N/A')} × 탐지:{risk.get('detection', 'N/A')})")
                report.append(f"   위험도: {risk.get('risk_level', 'N/A')}")
                
                if risk.get('mitigation_measures'):
                    report.append(f"   완화 방안:")
                    for measure in risk['mitigation_measures'][:3]:  # 상위 3개만 표시
                        report.append(f"     - {measure}")
        
        # 개발 가이드라인
        if "development_guidelines" in analysis_result:
            report.append(f"\n📋 개발 가이드라인")
            report.append("-" * 40)
            for i, guideline in enumerate(analysis_result["development_guidelines"], 1):
                report.append(f"{i}. {guideline}")
        
        # 모니터링 권장사항
        if "monitoring_recommendations" in analysis_result:
            report.append(f"\n🔍 모니터링 권장사항")
            report.append("-" * 40)
            for i, recommendation in enumerate(analysis_result["monitoring_recommendations"], 1):
                report.append(f"{i}. {recommendation}")
        
        return "\n".join(report)


def analyze_development_risk(development_task: str,
                           sr_top_k: int = 5,
                           incident_top_k: int = 5,
                           use_llm: bool = True,
                           config: Optional[Config] = None) -> Dict[str, Any]:
    """
    개발 과제 리스크 분석 함수 (간편 함수)
    
    Args:
        development_task: 개발 과제 설명
        sr_top_k: SR 검색 결과 수
        incident_top_k: 장애 검색 결과 수
        use_llm: LLM을 사용하여 분석 생성 여부
        config: Config 객체 (None이면 새로 생성)
    
    Returns:
        통합 리스크 분석 결과
    """
    analyzer = IntegratedRiskAnalyzer(config=config)
    return analyzer.analyze_development_risk(
        development_task=development_task,
        sr_top_k=sr_top_k,
        incident_top_k=incident_top_k,
        use_llm=use_llm
    )


# 메인 실행 부분
if __name__ == "__main__":
    # 테스트 쿼리
    test_queries = [
        "가입일 기준 월할 계산 기능 개발",
        "위약금 계산 시스템 개선",
        "요금 계산 엔진 최적화"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 개발 과제: {query}")
        print('='*80)
        
        try:
            # 통합 리스크 분석 실행
            result = analyze_development_risk(
                sr_query=query,
                sr_top_k=3,
                incident_top_k=3,
                use_llm=True
            )
            
            # 결과 출력
            analyzer = IntegratedRiskAnalyzer()
            report = analyzer.format_risk_report(
                result.get("risk_analysis", {}),
                sr_documents=result.get('sr_data', {}).get('documents', []),
                incident_documents=result.get('incident_data', {}).get('documents', [])
            )
            print(report)
            
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()

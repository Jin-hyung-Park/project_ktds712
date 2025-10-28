"""
OpenAI 기반 리스크 평가 엔진
FMEA 기준을 시스템 프롬프트로 제공하고, AI Search 결과를 참고하여 리스크 평가
"""
import json
from typing import Dict, List, Any, Optional
from .data_loader import DataLoader
from .config import Config
from .search_engine import SearchEngine

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. pip install openai 를 실행하세요.")

class AIRiskEvaluator:
    """OpenAI 기반 리스크 평가 클래스"""
    
    def __init__(self, data_loader: DataLoader, search_engine: SearchEngine):
        self.data_loader = data_loader
        self.search_engine = search_engine
        self.config = Config()
        
        # OpenAI 클라이언트 초기화
        if OPENAI_AVAILABLE and self._has_openai_config():
            try:
                self.client = AzureOpenAI(
                    api_key=self.config.AZURE_OPENAI_KEY,
                    api_version="2024-02-15-preview",
                    azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT
                )
                self.openai_available = True
            except Exception as e:
                print(f"⚠️ OpenAI 초기화 실패: {e}")
                self.openai_available = False
        else:
            self.openai_available = False
    
    def _has_openai_config(self) -> bool:
        """OpenAI 설정이 있는지 확인"""
        return (self.config.AZURE_OPENAI_ENDPOINT and 
                self.config.AZURE_OPENAI_ENDPOINT != "https://your-openai-service.openai.azure.com" and
                self.config.AZURE_OPENAI_KEY and
                self.config.AZURE_OPENAI_KEY != "your-openai-key")
    
    def _get_system_prompt(self) -> str:
        """FMEA 기반 리스크 평가 시스템 프롬프트"""
        return """당신은 SR(Service Request)의 리스크를 평가하는 전문가입니다. 
FMEA(Failure Mode and Effects Analysis) 방법론을 기반으로 다음 요소들을 종합적으로 평가하세요:

## 평가 기준

### 1. SR 유사도 (25% 가중치)
- 과거 유사한 SR이 있는가?
- 유사한 SR이 발생한 빈도와 결과는?
- 텍스트 유사도, 시스템 일치도, 컴포넌트 일치도를 종합 평가

### 2. 장애 연관도 (25% 가중치)
- 관련된 과거 장애가 있는가?
- 장애의 심각도와 빈도는?
- 같은 시스템/컴포넌트에서 발생한 장애인가?
- 최근 장애일수록 높은 가중치 부여

### 3. 시스템 중요도 (25% 가중치)
- 영향을 받는 시스템의 비즈니스 중요도는?
- Critical > High > Medium > Low 순으로 평가
- 요금계산시스템과 같은 핵심 시스템은 높은 중요도

### 4. 시간 민감도 (15% 가중치)
- 최근 관련 장애가 있는가?
- 최근 30일 내 장애면 높은 가중치
- 시간이 지날수록 가중치 감소

### 5. SR 복잡도 (10% 가중치)
- 기술 요구사항의 복잡도는?
- 영향받는 컴포넌트의 수는?
- 구현 난이도는?

## 출력 형식

다음 JSON 형식으로 응답하세요:
{
    "total_score": 0.0-1.0 범위의 종합 리스크 점수,
    "risk_level": "Critical" | "High" | "Medium" | "Low" | "Minimal",
    "components": {
        "sr_similarity": 0.0-1.0,
        "incident_correlation": 0.0-1.0,
        "system_importance": 0.0-1.0,
        "time_sensitivity": 0.0-1.0,
        "sr_complexity": 0.0-1.0
    },
    "reasoning": "리스크 평가 근거 설명 (2-3문장)",
    "key_risks": ["주요 리스크 1", "주요 리스크 2", ...],
    "recommendations": ["권장사항 1", "권장사항 2", ...]
}
"""
    
    def _build_user_prompt(self, sr: Dict[str, Any], 
                          similar_srs: List[Dict[str, Any]],
                          related_incidents: List[Dict[str, Any]]) -> str:
        """사용자 프롬프트 구성"""
        prompt_parts = []
        
        # 대상 SR 정보
        prompt_parts.append("## 평가 대상 SR")
        prompt_parts.append(f"ID: {sr.get('id', '')}")
        prompt_parts.append(f"제목: {sr.get('title', '')}")
        prompt_parts.append(f"설명: {sr.get('description', '')}")
        prompt_parts.append(f"시스템: {sr.get('system', '')}")
        prompt_parts.append(f"우선순위: {sr.get('priority', '')}")
        prompt_parts.append(f"카테고리: {sr.get('category', '')}")
        prompt_parts.append(f"영향받는 컴포넌트: {', '.join(sr.get('affected_components', []))}")
        prompt_parts.append(f"기술 요구사항: {', '.join(sr.get('technical_requirements', []))}")
        prompt_parts.append(f"비즈니스 임팩트: {sr.get('business_impact', '')}")
        prompt_parts.append("")
        
        # 유사 SR 정보
        prompt_parts.append("## 유사한 SR (AI Search 결과)")
        if similar_srs:
            for i, result in enumerate(similar_srs[:3], 1):  # 상위 3개만
                sr_data = result.get('sr', {})
                prompt_parts.append(f"{i}. {sr_data.get('title', '')}")
                prompt_parts.append(f"   유사도: {result.get('similarity_score', 0):.3f}")
                prompt_parts.append(f"   ID: {sr_data.get('id', '')}")
                prompt_parts.append(f"   시스템: {sr_data.get('system', '')}")
                prompt_parts.append(f"   매치 이유: {result.get('match_reason', '')}")
                prompt_parts.append("")
        else:
            prompt_parts.append("유사한 SR을 찾을 수 없습니다.")
            prompt_parts.append("")
        
        # 관련 장애 정보
        prompt_parts.append("## 관련 장애 (AI Search 결과)")
        if related_incidents:
            for i, result in enumerate(related_incidents[:3], 1):  # 상위 3개만
                incident = result.get('incident', {})
                prompt_parts.append(f"{i}. {incident.get('title', '')}")
                prompt_parts.append(f"   연관도: {result.get('correlation_score', 0):.3f}")
                prompt_parts.append(f"   ID: {incident.get('id', '')}")
                prompt_parts.append(f"   심각도: {incident.get('severity', '')}")
                prompt_parts.append(f"   발생일: {incident.get('reported_date', '')}")
                prompt_parts.append(f"   근본 원인: {incident.get('root_cause', '')}")
                prompt_parts.append(f"   영향받은 사용자: {incident.get('affected_users', 0)}명")
                prompt_parts.append(f"   비즈니스 임팩트: {incident.get('business_impact', '')}")
                prompt_parts.append(f"   매치 이유: {result.get('match_reason', '')}")
                prompt_parts.append("")
        else:
            prompt_parts.append("관련 장애를 찾을 수 없습니다.")
            prompt_parts.append("")
        
        prompt_parts.append("위 정보를 바탕으로 FMEA 방법론에 따라 리스크를 평가하고 JSON 형식으로 응답하세요.")
        
        return "\n".join(prompt_parts)
    
    def evaluate_risk(self, sr: Dict[str, Any], use_openai: bool = True) -> Dict[str, Any]:
        """OpenAI를 사용한 리스크 평가"""
        
        # AI Search로 유사 SR과 관련 장애 검색
        similar_srs = self.search_engine.search_similar_srs(sr, top_k=5)
        related_incidents = self.search_engine.search_related_incidents(sr, top_k=5)
        
        # OpenAI 사용 가능하고 사용 요청한 경우
        if use_openai and self.openai_available:
            try:
                # 프롬프트 구성
                system_prompt = self._get_system_prompt()
                user_prompt = self._build_user_prompt(sr, similar_srs, related_incidents)
                
                # OpenAI API 호출
                response = self.client.chat.completions.create(
                    model=self.config.AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # 일관성을 위해 낮은 temperature
                    response_format={"type": "json_object"}  # JSON 형식 강제
                )
                
                # 응답 파싱
                result_text = response.choices[0].message.content
                result_dict = json.loads(result_text)
                
                # 메타데이터 추가
                result_dict['evaluation_method'] = 'openai'
                result_dict['similar_srs'] = similar_srs[:3]  # 상위 3개
                result_dict['related_incidents'] = related_incidents[:3]  # 상위 3개
                
                return result_dict
                
            except Exception as e:
                print(f"⚠️ OpenAI 평가 실패: {e}. 기본 계산 방식으로 전환합니다.")
                return self._fallback_evaluation(sr, similar_srs, related_incidents)
        else:
            # OpenAI 사용 불가 시 기본 계산 방식 사용
            return self._fallback_evaluation(sr, similar_srs, related_incidents)
    
    def _fallback_evaluation(self, sr: Dict[str, Any],
                            similar_srs: List[Dict[str, Any]],
                            related_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OpenAI 사용 불가 시 기본 계산 방식"""
        from .risk_calculator import RiskCalculator
        
        calculator = RiskCalculator(self.data_loader)
        result = calculator.calculate_risk_score(sr)
        
        # 기본 권장사항 추가
        recommendations = calculator.get_risk_recommendations(result)
        
        return {
            'evaluation_method': 'rule_based',
            'total_score': result['total_score'],
            'risk_level': result['risk_level'],
            'components': result['components'],
            'reasoning': f"규칙 기반 FMEA 평가 결과: {result['risk_level']} 등급",
            'key_risks': self._extract_key_risks(sr, similar_srs, related_incidents),
            'recommendations': recommendations,
            'similar_srs': similar_srs[:3],
            'related_incidents': related_incidents[:3]
        }
    
    def _extract_key_risks(self, sr: Dict[str, Any],
                          similar_srs: List[Dict[str, Any]],
                          related_incidents: List[Dict[str, Any]]) -> List[str]:
        """주요 리스크 추출"""
        risks = []
        
        # 유사 SR이 있는 경우
        if similar_srs:
            top_similar = similar_srs[0]
            if top_similar.get('similarity_score', 0) > 0.5:
                risks.append(f"유사한 SR {top_similar['sr'].get('title', '')} 존재")
        
        # 관련 장애가 있는 경우
        if related_incidents:
            critical_incidents = [inc for inc in related_incidents 
                                if inc.get('incident', {}).get('severity') in ['Critical', 'High']]
            if critical_incidents:
                risks.append(f"심각한 관련 장애 {len(critical_incidents)}건 존재")
        
        # 시스템 중요도
        system = sr.get('system', '')
        if '요금계산' in system:
            risks.append("핵심 비즈니스 시스템 영향")
        
        return risks if risks else ["기본 리스크 요소 확인 필요"]

# 사용 예시
if __name__ == "__main__":
    from src.data_loader import DataLoader
    from src.search_engine import SearchEngine
    
    loader = DataLoader()
    search_engine = SearchEngine(loader)
    evaluator = AIRiskEvaluator(loader, search_engine)
    
    srs = loader.load_sr_data()
    if srs:
        test_sr = srs[0]
        print(f"\n🔍 SR 평가: {test_sr['title']}")
        print(f"OpenAI 사용 가능: {evaluator.openai_available}\n")
        
        result = evaluator.evaluate_risk(test_sr, use_openai=False)  # 테스트를 위해 False
        
        print(f"📊 평가 결과:")
        print(f"  방법: {result['evaluation_method']}")
        print(f"  총점: {result['total_score']:.3f}")
        print(f"  등급: {result['risk_level']}")
        print(f"\n📈 구성 요소:")
        for comp, score in result['components'].items():
            print(f"  {comp}: {score:.3f}")
        print(f"\n💡 권장사항:")
        for rec in result.get('recommendations', []):
            print(f"  - {rec}")


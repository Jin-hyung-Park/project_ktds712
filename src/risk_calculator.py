"""
FMEA 기반 리스크 계산 엔진
"""
import math
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from .data_loader import DataLoader
from .config import Config

class RiskCalculator:
    """FMEA 기반 리스크 계산 클래스"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.config = Config()
        
    def calculate_sr_similarity(self, target_sr: Dict[str, Any], 
                              reference_srs: List[Dict[str, Any]]) -> float:
        """SR 유사도 계산 (시뮬레이션)"""
        if not reference_srs:
            return 0.0
        
        # 실제로는 Azure AI Search의 벡터 유사도 사용
        # 여기서는 간단한 키워드 기반 유사도 계산
        target_text = f"{target_sr.get('title', '')} {target_sr.get('description', '')}".lower()
        target_keywords = set(target_text.split())
        
        max_similarity = 0.0
        for ref_sr in reference_srs:
            ref_text = f"{ref_sr.get('title', '')} {ref_sr.get('description', '')}".lower()
            ref_keywords = set(ref_text.split())
            
            # Jaccard 유사도 계산
            intersection = len(target_keywords.intersection(ref_keywords))
            union = len(target_keywords.union(ref_keywords))
            similarity = intersection / union if union > 0 else 0.0
            
            max_similarity = max(max_similarity, similarity)
        
        return min(max_similarity, 1.0)
    
    def calculate_incident_correlation(self, target_sr: Dict[str, Any], 
                                     incidents: List[Dict[str, Any]]) -> float:
        """장애 연관도 계산"""
        if not incidents:
            return 0.0
        
        target_system = target_sr.get('system', '')
        target_components = set(target_sr.get('affected_components', []))
        
        correlation_score = 0.0
        total_weight = 0.0
        
        for incident in incidents:
            # 시스템 일치도
            system_match = 1.0 if incident.get('system') == target_system else 0.0
            
            # 컴포넌트 일치도
            incident_components = set(incident.get('related_components', []))
            component_match = len(target_components.intersection(incident_components)) / len(target_components) if target_components else 0.0
            
            # 장애 심각도 가중치
            severity_weights = {
                'Critical': 1.0,
                'High': 0.8,
                'Medium': 0.6,
                'Low': 0.4
            }
            severity_weight = severity_weights.get(incident.get('severity', 'Low'), 0.4)
            
            # 시간 가중치 (최근 장애일수록 높은 가중치)
            time_weight = self._calculate_time_weight(incident.get('reported_date', ''))
            
            # 종합 점수
            incident_score = (system_match * 0.4 + component_match * 0.6) * severity_weight * time_weight
            correlation_score += incident_score
            total_weight += severity_weight * time_weight
        
        return correlation_score / total_weight if total_weight > 0 else 0.0
    
    def calculate_time_sensitivity(self, incidents: List[Dict[str, Any]]) -> float:
        """시간 민감도 계산"""
        if not incidents:
            return 0.0
        
        current_date = datetime.now()
        total_weight = 0.0
        
        for incident in incidents:
            try:
                incident_date = datetime.strptime(incident['reported_date'], '%Y-%m-%d')
                days_ago = (current_date - incident_date).days
                
                # 지수적 감소 함수 (30일 기준)
                time_weight = math.exp(-days_ago / 30)
                total_weight += time_weight
            except ValueError:
                continue
        
        # 정규화 (0-1 범위)
        return min(total_weight / len(incidents), 1.0) if incidents else 0.0
    
    def calculate_system_importance(self, system: str) -> float:
        """시스템 중요도 계산"""
        return self.data_loader.get_system_importance(system)
    
    def calculate_sr_complexity(self, sr: Dict[str, Any]) -> float:
        """SR 복잡도 계산"""
        return self.data_loader.calculate_sr_complexity(sr)
    
    def _calculate_time_weight(self, date_str: str) -> float:
        """시간 가중치 계산"""
        try:
            incident_date = datetime.strptime(date_str, '%Y-%m-%d')
            days_ago = (datetime.now() - incident_date).days
            
            # 지수적 감소 (30일 기준)
            return math.exp(-days_ago / 30)
        except ValueError:
            return 0.1  # 기본값
    
    def calculate_risk_score(self, sr: Dict[str, Any]) -> Dict[str, Any]:
        """종합 리스크 점수 계산"""
        # 모든 SR 데이터 로드
        all_srs = self.data_loader.load_sr_data()
        all_incidents = self.data_loader.load_incident_data()
        
        # 1. SR 유사도 (25%)
        sr_similarity = self.calculate_sr_similarity(sr, all_srs)
        
        # 2. 장애 연관도 (25%)
        incident_correlation = self.calculate_incident_correlation(sr, all_incidents)
        
        # 3. 시스템 중요도 (25%)
        system_importance = self.calculate_system_importance(sr.get('system', ''))
        
        # 4. 시간 민감도 (15%)
        time_sensitivity = self.calculate_time_sensitivity(all_incidents)
        
        # 5. SR 복잡도 (10%)
        sr_complexity = self.calculate_sr_complexity(sr)
        
        # 가중 평균 계산
        weights = self.config.RISK_WEIGHTS
        base_risk_score = (
            sr_similarity * weights['sr_similarity'] +
            incident_correlation * weights['incident_correlation'] +
            system_importance * weights['system_importance'] +
            time_sensitivity * weights['time_sensitivity'] +
            sr_complexity * weights['sr_complexity']
        )
        
        # 시간 가중치 적용
        time_weight = self.calculate_time_sensitivity(all_incidents)
        final_risk_score = base_risk_score * (1 + time_weight * 0.2)  # 최대 20% 증가
        
        # 리스크 등급 결정
        risk_level = self._determine_risk_level(final_risk_score)
        
        return {
            'total_score': min(final_risk_score, 1.0),
            'risk_level': risk_level,
            'components': {
                'sr_similarity': sr_similarity,
                'incident_correlation': incident_correlation,
                'system_importance': system_importance,
                'time_sensitivity': time_sensitivity,
                'sr_complexity': sr_complexity
            },
            'weights': weights
        }
    
    def _determine_risk_level(self, score: float) -> str:
        """리스크 등급 결정"""
        thresholds = self.config.RISK_THRESHOLDS
        
        if score >= thresholds['critical']:
            return 'Critical'
        elif score >= thresholds['high']:
            return 'High'
        elif score >= thresholds['medium']:
            return 'Medium'
        elif score >= thresholds['low']:
            return 'Low'
        else:
            return 'Minimal'
    
    def get_risk_color(self, risk_level: str) -> str:
        """리스크 등급별 색상 반환"""
        colors = {
            'Critical': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Minimal': '⚪'
        }
        return colors.get(risk_level, '⚪')
    
    def get_risk_recommendations(self, risk_result: Dict[str, Any]) -> List[str]:
        """리스크 등급별 권장사항 생성"""
        risk_level = risk_result['risk_level']
        components = risk_result['components']
        
        recommendations = []
        
        if risk_level in ['Critical', 'High']:
            recommendations.append("🚨 즉시 검토 및 대응 계획 수립 필요")
            recommendations.append("📋 상세한 영향도 분석 수행")
            recommendations.append("🛡️ 추가 테스트 및 검증 강화")
        
        if components['sr_similarity'] > 0.7:
            recommendations.append("🔍 유사 SR 사례 참고하여 검증 방안 수립")
        
        if components['incident_correlation'] > 0.6:
            recommendations.append("⚠️ 관련 장애 사례 분석 및 재발 방지 대책 수립")
        
        if components['system_importance'] > 0.8:
            recommendations.append("🏢 핵심 시스템 영향도 고려한 단계적 배포 검토")
        
        if components['sr_complexity'] > 0.7:
            recommendations.append("🔧 복잡한 요구사항으로 인한 세분화된 개발 계획 수립")
        
        return recommendations

# 사용 예시
if __name__ == "__main__":
    from data_loader import DataLoader
    
    # 데이터 로더 초기화
    loader = DataLoader()
    
    # 리스크 계산기 초기화
    risk_calc = RiskCalculator(loader)
    
    # SR 데이터 로드
    srs = loader.load_sr_data()
    
    if srs:
        # 첫 번째 SR의 리스크 계산
        test_sr = srs[0]
        print(f"\n🔍 SR 분석: {test_sr['title']}")
        
        risk_result = risk_calc.calculate_risk_score(test_sr)
        
        print(f"\n📊 리스크 분석 결과:")
        print(f"총점: {risk_result['total_score']:.3f}")
        print(f"등급: {risk_calc.get_risk_color(risk_result['risk_level'])} {risk_result['risk_level']}")
        
        print(f"\n📈 구성 요소별 점수:")
        for component, score in risk_result['components'].items():
            print(f"  {component}: {score:.3f}")
        
        print(f"\n💡 권장사항:")
        recommendations = risk_calc.get_risk_recommendations(risk_result)
        for rec in recommendations:
            print(f"  {rec}")

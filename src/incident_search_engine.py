"""
장애 보고서 검색 엔진
Azure AI Search의 Incident 인덱스를 활용한 관련 장애 검색 전용
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from .data_loader import DataLoader
from .config import Config

class IncidentSearchEngine:
    """장애 보고서 검색 전용 엔진"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.config = Config()
        self.index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
    def search_related(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """관련 장애 검색"""
        all_incidents = self.data_loader.load_incident_data()
        
        # 쿼리 구성 (장애 특화)
        query_context = self._build_incident_query(query_sr)
        
        # 연관도 계산
        correlations = []
        for incident in all_incidents:
            correlation_score = self._calculate_incident_correlation(query_sr, incident)
            
            if correlation_score > 0.1:  # 최소 임계값
                correlations.append({
                    'incident': incident,
                    'correlation_score': correlation_score,
                    'match_reason': self._get_match_reason(query_sr, incident),
                    'risk_factors': self._analyze_risk_factors(incident),
                    'temporal_relevance': self._calculate_temporal_relevance(incident)
                })
        
        # 연관도 순으로 정렬
        correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
        
        return correlations[:top_k]
    
    def _build_incident_query(self, sr: Dict[str, Any]) -> Dict[str, Any]:
        """장애 검색용 쿼리 구성"""
        return {
            'text': f"{sr.get('title', '')} {sr.get('description', '')}",
            'system': sr.get('system', ''),
            'components': set(sr.get('affected_components', [])),
            'category': sr.get('category', '')
        }
    
    def _calculate_incident_correlation(self, sr: Dict[str, Any], incident: Dict[str, Any]) -> float:
        """장애 연관도 계산 (장애 특화 로직)"""
        correlation_score = 0.0
        
        # 1. 시스템 일치도 (30%)
        if incident.get('system') == sr.get('system'):
            correlation_score += 0.30
        
        # 2. 컴포넌트 일치도 (30%)
        sr_components = set(sr.get('affected_components', []))
        incident_components = set(incident.get('related_components', []))
        if sr_components and incident_components:
            comp_intersection = len(sr_components.intersection(incident_components))
            comp_union = len(sr_components.union(incident_components))
            comp_ratio = comp_intersection / comp_union if comp_union > 0 else 0.0
            correlation_score += comp_ratio * 0.30
        
        # 3. 텍스트 유사도 (20%)
        sr_text = f"{sr.get('title', '')} {sr.get('description', '')}"
        incident_text = f"{incident.get('title', '')} {incident.get('description', '')} {incident.get('root_cause', '')}"
        text_similarity = self._calculate_text_similarity(sr_text, incident_text)
        correlation_score += text_similarity * 0.20
        
        # 4. 장애 심각도 가중치 (10%)
        severity_weights = {
            'Critical': 1.0,
            'High': 0.8,
            'Medium': 0.6,
            'Low': 0.4
        }
        severity_weight = severity_weights.get(incident.get('severity', 'Low'), 0.4)
        correlation_score += severity_weight * 0.10
        
        # 5. 시간 가중치 (10%) - 최근 장애일수록 높은 가중치
        time_weight = self._calculate_temporal_weight(incident.get('reported_date', ''))
        correlation_score += time_weight * 0.10
        
        return min(correlation_score, 1.0)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """텍스트 유사도 계산"""
        text1 = self._preprocess_text(text1)
        text2 = self._preprocess_text(text2)
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard 유사도
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # 키워드 가중치 적용
        important_keywords = [
            '오류', '장애', '계산', '요금', '시스템', '성능', '데이터',
            '로직', '처리', '할인', '청구', '정책'
        ]
        
        keyword_weight = sum(1 for word in words1.intersection(words2) if word in important_keywords)
        keyword_factor = min(keyword_weight / 5, 1.0) * 0.3
        
        jaccard_sim = intersection / union if union > 0 else 0.0
        final_similarity = jaccard_sim * 0.7 + keyword_factor
        
        return min(final_similarity, 1.0)
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        text = text.lower()
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _calculate_temporal_weight(self, date_str: str) -> float:
        """시간 가중치 계산"""
        try:
            incident_date = datetime.strptime(date_str, '%Y-%m-%d')
            days_ago = (datetime.now() - incident_date).days
            
            # 지수적 감소 (30일 기준)
            import math
            return math.exp(-days_ago / 30)
        except (ValueError, TypeError):
            return 0.1
    
    def _calculate_temporal_relevance(self, incident: Dict[str, Any]) -> str:
        """시간적 관련성 평가"""
        try:
            incident_date = datetime.strptime(incident.get('reported_date', ''), '%Y-%m-%d')
            days_ago = (datetime.now() - incident_date).days
            
            if days_ago <= 30:
                return "최근"
            elif days_ago <= 90:
                return "중기"
            elif days_ago <= 180:
                return "중장기"
            else:
                return "과거"
        except (ValueError, TypeError):
            return "알 수 없음"
    
    def _get_match_reason(self, sr: Dict[str, Any], incident: Dict[str, Any]) -> str:
        """장애 매치 이유 생성"""
        reasons = []
        
        # 시스템 일치
        if sr.get('system') == incident.get('system'):
            reasons.append("동일 시스템")
        
        # 컴포넌트 일치
        sr_components = set(sr.get('affected_components', []))
        incident_components = set(incident.get('related_components', []))
        common_components = sr_components.intersection(incident_components)
        if common_components:
            reasons.append(f"공통 컴포넌트: {', '.join(list(common_components)[:2])}")
        
        # 장애 심각도
        severity = incident.get('severity', 'Unknown')
        reasons.append(f"심각도: {severity}")
        
        # 시간적 관련성
        temporal = self._calculate_temporal_relevance(incident)
        if temporal == "최근":
            reasons.append("최근 장애")
        
        return ", ".join(reasons) if reasons else "텍스트 유사성"
    
    def _analyze_risk_factors(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """장애 리스크 요소 분석"""
        return {
            'severity': incident.get('severity', 'Unknown'),
            'affected_users': incident.get('affected_users', 0),
            'duration_minutes': incident.get('duration_minutes', 0),
            'business_impact': incident.get('business_impact', ''),
            'root_cause': incident.get('root_cause', ''),
            'has_resolution': bool(incident.get('resolution', ''))
        }


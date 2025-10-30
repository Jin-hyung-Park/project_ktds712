"""
통합 검색 엔진 인터페이스
SR 검색과 장애 검색을 분리하여 관리하는 통합 클래스
"""
from typing import List, Dict, Any
from .data_loader import DataLoader
from .sr_search_engine import SRSearchEngine
from .incident_search_engine import IncidentSearchEngine

class SearchEngine:
    """통합 검색 엔진 - SR 검색과 장애 검색을 분리 관리"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        
        # 각각의 전용 검색 엔진 초기화
        self.sr_searcher = SRSearchEngine(data_loader)
        self.incident_searcher = IncidentSearchEngine(data_loader)
    
    def search_similar_srs(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """유사한 SR 검색 (SR 전용 검색 엔진 사용)"""
        return self.sr_searcher.search_similar(query_sr, top_k)
    
    def search_related_incidents(self, query_sr: Dict[str, Any], top_k: int = 5, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """관련 장애 검색 (장애 전용 검색 엔진 사용, 노트북 스타일)
        
        Args:
            query_sr: 검색할 SR 객체
            top_k: 반환할 최대 결과 수
            use_semantic: True면 semantic 검색 사용 (READMe의 semantic 방식), False면 simple 검색
        """
        return self.incident_searcher.search_related(query_sr, top_k, use_semantic)
    
    def get_search_summary(self, query_sr: Dict[str, Any]) -> Dict[str, Any]:
        """검색 결과 요약"""
        similar_srs = self.search_similar_srs(query_sr, top_k=3)
        related_incidents = self.search_related_incidents(query_sr, top_k=3)
        
        return {
            'query_sr': query_sr,
            'similar_srs_count': len(similar_srs),
            'related_incidents_count': len(related_incidents),
            'top_similarity': similar_srs[0]['similarity_score'] if similar_srs else 0.0,
            'top_correlation': related_incidents[0]['correlation_score'] if related_incidents else 0.0,
            'similar_srs': similar_srs,
            'related_incidents': related_incidents
        }
    
    # 편의 메서드들
    def get_sr_searcher(self) -> SRSearchEngine:
        """SR 검색 엔진 직접 접근"""
        return self.sr_searcher
    
    def get_incident_searcher(self) -> IncidentSearchEngine:
        """장애 검색 엔진 직접 접근"""
        return self.incident_searcher

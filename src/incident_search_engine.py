"""
장애 보고서 검색 엔진
Azure AI Search의 Incident 인덱스를 활용한 관련 장애 검색 전용
"""
from datetime import datetime
from typing import List, Dict, Any
from .data_loader import DataLoader
from .config import Config
from .azure_search_client import AzureSearchClient


class IncidentSearchEngine:
    """장애 보고서 검색 전용 엔진 (Azure AI Search만 사용)"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.config = Config()
        self.index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        # Azure Search 클라이언트 초기화 (필수)
        if not self._has_azure_config():
            raise ValueError(
                "Azure AI Search 설정이 필요합니다. "
                ".env 파일에 AZURE_SEARCH_ENDPOINT와 AZURE_SEARCH_KEY를 설정하세요."
            )
        
        try:
            self.azure_client = AzureSearchClient()
        except Exception as e:
            raise RuntimeError(f"Azure Search 클라이언트 초기화 실패: {e}")
    
    def _has_azure_config(self) -> bool:
        """Azure Search 설정이 있는지 확인"""
        return (self.config.AZURE_SEARCH_ENDPOINT and 
                self.config.AZURE_SEARCH_ENDPOINT != "https://your-search-service.search.windows.net" and
                self.config.AZURE_SEARCH_KEY and
                self.config.AZURE_SEARCH_KEY != "your-search-key")
        
    def search_related(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """관련 장애 검색 (Azure AI Search 사용)"""
        # 쿼리 텍스트 생성
        query_text = self._build_incident_query(query_sr)
        
        # 필터 설정
        filters = {
            'system': query_sr.get('system')
        }
        
        # Azure Search로 검색
        results = self.azure_client.search_related_incidents(
            query_text=query_text,
            top_k=top_k,
            filters=filters
        )
        
        # 추가 정보 채우기
        for result in results:
            incident = result['incident']
            
            # 시간적 관련성 추가
            if 'temporal_relevance' not in result:
                result['temporal_relevance'] = self._calculate_temporal_relevance(incident)
            
            # 리스크 요소 추가
            if 'risk_factors' not in result:
                result['risk_factors'] = self._analyze_risk_factors(incident)
        
        return results
    
    def _build_incident_query(self, sr: Dict[str, Any]) -> str:
        """장애 검색용 쿼리 텍스트 구성"""
        parts = [
            sr.get('title', ''),
            sr.get('description', ''),
            ' '.join(sr.get('technical_requirements', [])),
            ' '.join(sr.get('affected_components', []))
        ]
        return ' '.join(filter(None, parts))
    
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
    
    def initialize_index(self) -> bool:
        """인덱스 초기화 및 데이터 업로드"""
        try:
            # 인덱스 생성
            if not self.azure_client.create_incident_index(self.index_name):
                return False
            
            # 장애 데이터 로드
            incidents = self.data_loader.load_incident_data()
            
            # 데이터 인덱싱
            return self.azure_client.index_incident_documents(incidents, self.index_name)
            
        except Exception as e:
            raise RuntimeError(f"인덱스 초기화 실패: {e}")

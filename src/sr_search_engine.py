"""
SR 유사도 검색 엔진
Azure AI Search의 SR 인덱스를 활용한 유사 SR 검색 전용
"""
from typing import List, Dict, Any
from .data_loader import DataLoader
from .config import Config
from .azure_search_client import AzureSearchClient


class SRSearchEngine:
    """SR 유사도 검색 전용 엔진 (Azure AI Search만 사용)"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.config = Config()
        self.index_name = self.config.AZURE_SEARCH_INDEX_SR
        
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
        
    def search_similar(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """유사한 SR 검색 (Azure AI Search 사용)"""
        # 쿼리 텍스트 생성
        query_text = self._build_sr_query(query_sr)
        
        # 필터 설정
        filters = {
            'exclude_id': query_sr.get('id')
        }
        
        # Azure Search로 검색
        results = self.azure_client.search_similar_srs(
            query_text=query_text,
            top_k=top_k,
            filters=filters
        )
        
        # 결과 포맷 통일
        for result in results:
            if 'match_factors' not in result:
                result['match_factors'] = self._analyze_match_factors_from_result(
                    query_sr, result['sr']
                )
        
        return results
    
    def _build_sr_query(self, sr: Dict[str, Any]) -> str:
        """SR 쿼리 텍스트 구성"""
        parts = [
            sr.get('title', ''),
            sr.get('description', ''),
            ' '.join(sr.get('technical_requirements', [])),
            sr.get('category', ''),
            sr.get('priority', '')
        ]
        return ' '.join(filter(None, parts))
    
    def _analyze_match_factors_from_result(self, query_sr: Dict[str, Any], result_sr: Dict[str, Any]) -> Dict[str, Any]:
        """Azure Search 결과에서 매치 요소 분석"""
        return {
            'system_match': 1.0 if query_sr.get('system') == result_sr.get('system') else 0.0,
            'component_overlap': len(
                set(query_sr.get('affected_components', []))
                .intersection(set(result_sr.get('affected_components', [])))
            )
        }
    
    def initialize_index(self) -> bool:
        """인덱스 초기화 및 데이터 업로드"""
        try:
            # 인덱스 생성
            if not self.azure_client.create_sr_index(self.index_name):
                return False
            
            # SR 데이터 로드
            srs = self.data_loader.load_sr_data()
            
            # 데이터 인덱싱
            return self.azure_client.index_sr_documents(srs, self.index_name)
            
        except Exception as e:
            raise RuntimeError(f"인덱스 초기화 실패: {e}")

"""
SR 유사도 검색 엔진
Azure AI Search의 SR 인덱스를 활용한 유사 SR 검색 전용
"""
import re
from typing import List, Dict, Any, Optional
from .data_loader import DataLoader
from .config import Config

try:
    from .azure_search_client import AzureSearchClient
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False
    print("⚠️ Azure Search 클라이언트를 사용할 수 없습니다.")

class SRSearchEngine:
    """SR 유사도 검색 전용 엔진"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.config = Config()
        self.index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        # Azure Search 클라이언트 초기화
        self.azure_client = None
        self.use_azure = False
        
        if AZURE_SEARCH_AVAILABLE and self._has_azure_config():
            try:
                self.azure_client = AzureSearchClient()
                self.use_azure = True
                print("✅ Azure AI Search 사용 가능")
            except Exception as e:
                print(f"⚠️ Azure Search 초기화 실패: {e}. 로컬 검색으로 폴백합니다.")
                self.use_azure = False
    
    def _has_azure_config(self) -> bool:
        """Azure Search 설정이 있는지 확인"""
        return (self.config.AZURE_SEARCH_ENDPOINT and 
                self.config.AZURE_SEARCH_ENDPOINT != "https://your-search-service.search.windows.net" and
                self.config.AZURE_SEARCH_KEY and
                self.config.AZURE_SEARCH_KEY != "your-search-key")
        
    def search_similar(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """유사한 SR 검색"""
        # Azure Search 사용 가능하면 Azure Search 사용
        if self.use_azure and self.azure_client:
            return self._search_with_azure(query_sr, top_k)
        else:
            # 로컬 검색으로 폴백
            return self._search_local(query_sr, top_k)
    
    def _search_with_azure(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """Azure AI Search를 사용한 검색"""
        try:
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
            
        except Exception as e:
            print(f"⚠️ Azure Search 검색 실패: {e}. 로컬 검색으로 폴백합니다.")
            return self._search_local(query_sr, top_k)
    
    def _search_local(self, query_sr: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """로컬 검색 (폴백)"""
        all_srs = self.data_loader.load_sr_data()
        
        # 쿼리 텍스트 생성 (SR 특화)
        query_text = self._build_sr_query(query_sr)
        
        # 유사도 계산
        similarities = []
        for sr in all_srs:
            if sr['id'] == query_sr.get('id'):
                continue  # 자기 자신 제외
                
            similarity = self._calculate_sr_similarity(query_sr, sr)
            
            similarities.append({
                'sr': sr,
                'similarity_score': similarity,
                'match_reason': self._get_match_reason(query_sr, sr),
                'match_factors': self._analyze_match_factors(query_sr, sr)
            })
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similarities[:top_k]
    
    def _build_sr_query(self, sr: Dict[str, Any]) -> str:
        """SR 쿼리 텍스트 구성"""
        # SR 특화 쿼리 구성
        parts = [
            sr.get('title', ''),
            sr.get('description', ''),
            ' '.join(sr.get('technical_requirements', [])),
            sr.get('category', ''),
            sr.get('priority', '')
        ]
        return ' '.join(filter(None, parts))
    
    def _calculate_sr_similarity(self, sr1: Dict[str, Any], sr2: Dict[str, Any]) -> float:
        """SR 간 유사도 계산 (SR 특화 로직)"""
        score = 0.0
        
        # 1. 텍스트 유사도 (40%)
        text1 = self._build_sr_query(sr1)
        text2 = self._build_sr_query(sr2)
        text_sim = self._calculate_text_similarity(text1, text2)
        score += text_sim * 0.4
        
        # 2. 시스템 일치도 (15%)
        if sr1.get('system') == sr2.get('system'):
            score += 0.15
        
        # 3. 컴포넌트 일치도 (25%)
        comp1 = set(sr1.get('affected_components', []))
        comp2 = set(sr2.get('affected_components', []))
        if comp1 and comp2:
            comp_overlap = len(comp1.intersection(comp2)) / len(comp1.union(comp2))
            score += comp_overlap * 0.25
        
        # 4. 카테고리 일치도 (10%)
        if sr1.get('category') == sr2.get('category'):
            score += 0.10
        
        # 5. 우선순위 유사도 (10%)
        priority_map = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        p1 = priority_map.get(sr1.get('priority', 'Low'), 1)
        p2 = priority_map.get(sr2.get('priority', 'Low'), 1)
        priority_sim = 1 - abs(p1 - p2) / 4
        score += priority_sim * 0.10
        
        return min(score, 1.0)
    
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
        return intersection / union if union > 0 else 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        text = text.lower()
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_match_reason(self, query_sr: Dict[str, Any], target_sr: Dict[str, Any]) -> str:
        """SR 매치 이유 생성"""
        reasons = []
        
        if query_sr.get('system') == target_sr.get('system'):
            reasons.append("동일 시스템")
        
        if query_sr.get('category') == target_sr.get('category'):
            reasons.append(f"동일 카테고리: {query_sr.get('category')}")
        
        query_components = set(query_sr.get('affected_components', []))
        target_components = set(target_sr.get('affected_components', []))
        common_components = query_components.intersection(target_components)
        if common_components:
            reasons.append(f"공통 컴포넌트: {', '.join(list(common_components)[:2])}")
        
        return ", ".join(reasons) if reasons else "텍스트 유사성"
    
    def _analyze_match_factors(self, sr1: Dict[str, Any], sr2: Dict[str, Any]) -> Dict[str, float]:
        """매치 요소 분석"""
        return {
            'text_similarity': self._calculate_text_similarity(
                self._build_sr_query(sr1),
                self._build_sr_query(sr2)
            ),
            'system_match': 1.0 if sr1.get('system') == sr2.get('system') else 0.0,
            'component_overlap': len(set(sr1.get('affected_components', []))
                                   .intersection(set(sr2.get('affected_components', []))))
        }
    
    def _analyze_match_factors_from_result(self, query_sr: Dict[str, Any], result_sr: Dict[str, Any]) -> Dict[str, float]:
        """Azure Search 결과에서 매치 요소 분석"""
        return self._analyze_match_factors(query_sr, result_sr)
    
    def initialize_index(self) -> bool:
        """인덱스 초기화 및 데이터 업로드"""
        if not self.use_azure or not self.azure_client:
            print("⚠️ Azure Search가 사용 가능하지 않습니다.")
            return False
        
        try:
            # 인덱스 생성
            if not self.azure_client.create_sr_index(self.index_name):
                return False
            
            # SR 데이터 로드
            srs = self.data_loader.load_sr_data()
            
            # 데이터 인덱싱
            return self.azure_client.index_sr_documents(srs, self.index_name)
            
        except Exception as e:
            print(f"❌ 인덱스 초기화 실패: {e}")
            return False


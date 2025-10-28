"""
Azure AI Search 클라이언트
인덱스 관리 및 데이터 검색 기능 제공 (REST API 직접 호출)
"""
import json
import requests
from typing import List, Dict, Any, Optional
from .config import Config

class AzureSearchClient:
    """Azure AI Search 클라이언트 래퍼 (REST API)"""
    
    def __init__(self):
        self.config = Config()
        self.endpoint = self.config.AZURE_SEARCH_ENDPOINT.rstrip('/')
        self.api_key = self.config.AZURE_SEARCH_KEY
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
    
    def _make_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """REST API 요청"""
        url = f"{self.endpoint}/{path}?api-version=2023-11-01"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                return {}  # 404는 빈 결과로 처리
            raise Exception(f"API 요청 실패: {e}")
    
    def create_sr_index(self, index_name: Optional[str] = None) -> bool:
        """SR 인덱스 생성"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # 인덱스가 이미 존재하는지 확인
            try:
                result = self._make_request('GET', f"indexes/{index_name}")
                if result:
                    print(f"ℹ️  인덱스 '{index_name}'가 이미 존재합니다.")
                    return True
            except:
                pass
            
            # 인덱스 스키마 정의
            index_definition = {
                "name": index_name,
                "fields": [
                    {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
                    {"name": "title", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "description", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "system", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
                    {"name": "priority", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
                    {"name": "category", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
                    {"name": "requester", "type": "Edm.String", "searchable": True},
                    {"name": "created_date", "type": "Edm.String", "searchable": False, "filterable": True},
                    {"name": "target_date", "type": "Edm.String", "searchable": False, "filterable": True},
                    {"name": "business_impact", "type": "Edm.String", "searchable": True},
                    {"name": "technical_requirements", "type": "Collection(Edm.String)", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "affected_components", "type": "Collection(Edm.String)", "searchable": True, "filterable": True, "facetable": True},
                ]
            }
            
            # 인덱스 생성
            self._make_request('PUT', f"indexes/{index_name}", index_definition)
            print(f"✅ SR 인덱스 '{index_name}' 생성 완료")
            return True
            
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
            return False
    
    def index_sr_documents(self, srs: List[Dict[str, Any]], index_name: Optional[str] = None) -> bool:
        """SR 문서들을 인덱스에 업로드"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # 문서 변환
            documents = []
            for sr in srs:
                doc = {
                    "id": sr.get('id', ''),
                    "title": sr.get('title', ''),
                    "description": sr.get('description', ''),
                    "system": sr.get('system', ''),
                    "priority": sr.get('priority', ''),
                    "category": sr.get('category', ''),
                    "requester": sr.get('requester', ''),
                    "created_date": sr.get('created_date', ''),
                    "target_date": sr.get('target_date', ''),
                    "business_impact": sr.get('business_impact', ''),
                    "technical_requirements": sr.get('technical_requirements', []),
                    "affected_components": sr.get('affected_components', []),
                }
                documents.append({"@search.action": "upload", **doc})
            
            # 배치로 업로드 (최대 1000개씩)
            batch_size = 1000
            total_succeeded = 0
            total_failed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # 배치 업로드
                batch_data = {"value": batch}
                url = f"{self.endpoint}/indexes/{index_name}/docs/index?api-version=2023-11-01"
                
                try:
                    response = requests.post(url, headers=self.headers, json=batch_data)
                    response.raise_for_status()
                    
                    result = response.json()
                    succeeded = sum(1 for r in result.get('value', []) if r.get('status'))
                    failed = len(batch) - succeeded
                    
                    total_succeeded += succeeded
                    total_failed += failed
                    
                    if failed > 0:
                        print(f"⚠️  {failed}개 문서 업로드 실패")
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  배치 업로드 실패: {e}")
                    total_failed += len(batch)
            
            if total_failed == 0:
                print(f"✅ {total_succeeded}개 SR 문서 인덱싱 완료")
            else:
                print(f"⚠️  {total_succeeded}개 성공, {total_failed}개 실패")
            
            return total_failed == 0
            
        except Exception as e:
            print(f"❌ 문서 인덱싱 실패: {e}")
            return False
    
    def search_similar_srs(self, query_text: str, top_k: int = 5, 
                          filters: Optional[Dict[str, Any]] = None,
                          index_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """유사한 SR 검색"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # 필터 구성
            filter_expr = None
            if filters:
                filter_parts = []
                if filters.get('system'):
                    filter_parts.append(f"system eq '{filters['system']}'")
                if filters.get('exclude_id'):
                    filter_parts.append(f"id ne '{filters['exclude_id']}'")
                if filter_parts:
                    filter_expr = " and ".join(filter_parts)
            
            # 검색 요청 구성 (쿼리 파라미터와 본문 분리)
            url = f"{self.endpoint}/indexes/{index_name}/docs/search?api-version=2023-11-01"
            
            if filter_expr:
                url += f"&$filter={filter_expr}"
            
            search_body = {
                "search": query_text,
                "top": top_k,
                "count": True,
                "searchMode": "any",
                "queryType": "simple",
            }
            
            # 검색 실행
            response = requests.post(url, headers=self.headers, json=search_body)
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Search failed ({response.status_code}): {error_detail}")
            
            response.raise_for_status()
            
            results_data = response.json()
            
            # 결과 변환
            similar_srs = []
            for result in results_data.get('value', []):
                raw_score = result.get('@search.score', 0.0)
                
                # 정규화 (Azure Search 점수는 가변적)
                normalized_score = min(raw_score / 10.0, 1.0) if raw_score > 10 else raw_score / 10.0
                
                similar_srs.append({
                    'sr': {
                        'id': result.get('id'),
                        'title': result.get('title'),
                        'description': result.get('description'),
                        'system': result.get('system'),
                        'priority': result.get('priority'),
                        'category': result.get('category'),
                        'requester': result.get('requester'),
                        'created_date': result.get('created_date'),
                        'target_date': result.get('target_date'),
                        'business_impact': result.get('business_impact'),
                        'technical_requirements': result.get('technical_requirements', []),
                        'affected_components': result.get('affected_components', []),
                    },
                    'similarity_score': normalized_score,
                    'match_reason': self._build_match_reason(result),
                    'raw_score': raw_score
                })
            
            return similar_srs
            
        except Exception as e:
            print(f"⚠️  Azure Search 검색 실패: {e}")
            return []
    
    def _build_match_reason(self, result: Dict) -> str:
        """매치 이유 구성"""
        reasons = []
        
        if result.get('@search.highlights'):
            highlights = result['@search.highlights']
            if highlights.get('title'):
                reasons.append("제목 일치")
            if highlights.get('description'):
                reasons.append("설명 일치")
        
        if result.get('system'):
            reasons.append(f"시스템: {result['system']}")
        
        if result.get('affected_components'):
            components = result['affected_components'][:2]
            if components:
                reasons.append(f"컴포넌트: {', '.join(components)}")
        
        return ", ".join(reasons) if reasons else "텍스트 유사성"
    
    def delete_index(self, index_name: str) -> bool:
        """인덱스 삭제"""
        try:
            self._make_request('DELETE', f"indexes/{index_name}")
            print(f"✅ 인덱스 '{index_name}' 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ 인덱스 삭제 실패: {e}")
            return False
    
    def create_incident_index(self, index_name: Optional[str] = None) -> bool:
        """장애 인덱스 생성"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # 인덱스가 이미 존재하는지 확인
            try:
                result = self._make_request('GET', f"indexes/{index_name}")
                if result:
                    print(f"ℹ️  인덱스 '{index_name}'가 이미 존재합니다.")
                    return True
            except:
                pass
            
            # 인덱스 스키마 정의
            index_definition = {
                "name": index_name,
                "fields": [
                    {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
                    {"name": "title", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "description", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "system", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
                    {"name": "severity", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
                    {"name": "status", "type": "Edm.String", "searchable": True, "filterable": True},
                    {"name": "reported_date", "type": "Edm.String", "searchable": False, "filterable": True},
                    {"name": "resolved_date", "type": "Edm.String", "searchable": False, "filterable": True},
                    {"name": "duration_minutes", "type": "Edm.Int32", "searchable": False, "filterable": True},
                    {"name": "affected_users", "type": "Edm.Int32", "searchable": False, "filterable": True},
                    {"name": "root_cause", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "resolution", "type": "Edm.String", "searchable": True, "analyzer": "ko.lucene"},
                    {"name": "impact", "type": "Edm.String", "searchable": True},
                    {"name": "business_impact", "type": "Edm.String", "searchable": True},
                    {"name": "related_components", "type": "Collection(Edm.String)", "searchable": True, "filterable": True, "facetable": True},
                ]
            }
            
            # 인덱스 생성
            self._make_request('PUT', f"indexes/{index_name}", index_definition)
            print(f"✅ 장애 인덱스 '{index_name}' 생성 완료")
            return True
            
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
            return False
    
    def index_incident_documents(self, incidents: List[Dict[str, Any]], index_name: Optional[str] = None) -> bool:
        """장애 문서들을 인덱스에 업로드"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # 문서 변환
            documents = []
            for incident in incidents:
                doc = {
                    "id": incident.get('id', ''),
                    "title": incident.get('title', ''),
                    "description": incident.get('description', ''),
                    "system": incident.get('system', ''),
                    "severity": incident.get('severity', ''),
                    "status": incident.get('status', ''),
                    "reported_date": incident.get('reported_date', ''),
                    "resolved_date": incident.get('resolved_date', ''),
                    "duration_minutes": incident.get('duration_minutes', 0),
                    "affected_users": incident.get('affected_users', 0),
                    "root_cause": incident.get('root_cause', ''),
                    "resolution": incident.get('resolution', ''),
                    "impact": incident.get('impact', ''),
                    "business_impact": incident.get('business_impact', ''),
                    "related_components": incident.get('related_components', []),
                }
                documents.append({"@search.action": "upload", **doc})
            
            # 배치로 업로드 (최대 1000개씩)
            batch_size = 1000
            total_succeeded = 0
            total_failed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # 배치 업로드
                batch_data = {"value": batch}
                url = f"{self.endpoint}/indexes/{index_name}/docs/index?api-version=2023-11-01"
                
                try:
                    response = requests.post(url, headers=self.headers, json=batch_data)
                    response.raise_for_status()
                    
                    result = response.json()
                    succeeded = sum(1 for r in result.get('value', []) if r.get('status'))
                    failed = len(batch) - succeeded
                    
                    total_succeeded += succeeded
                    total_failed += failed
                    
                    if failed > 0:
                        print(f"⚠️  {failed}개 문서 업로드 실패")
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  배치 업로드 실패: {e}")
                    total_failed += len(batch)
            
            if total_failed == 0:
                print(f"✅ {total_succeeded}개 장애 문서 인덱싱 완료")
            else:
                print(f"⚠️  {total_succeeded}개 성공, {total_failed}개 실패")
            
            return total_failed == 0
            
        except Exception as e:
            print(f"❌ 문서 인덱싱 실패: {e}")
            return False
    
    def search_related_incidents(self, query_text: str, top_k: int = 5,
                                filters: Optional[Dict[str, Any]] = None,
                                index_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """관련 장애 검색"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # 필터 구성
            filter_expr = None
            if filters:
                filter_parts = []
                if filters.get('system'):
                    filter_parts.append(f"system eq '{filters['system']}'")
                if filter_parts:
                    filter_expr = " and ".join(filter_parts)
            
            # 검색 요청 구성
            url = f"{self.endpoint}/indexes/{index_name}/docs/search?api-version=2023-11-01"
            
            if filter_expr:
                url += f"&$filter={filter_expr}"
            
            search_body = {
                "search": query_text,
                "top": top_k,
                "count": True,
                "searchMode": "any",
                "queryType": "simple",
            }
            
            # 검색 실행
            response = requests.post(url, headers=self.headers, json=search_body)
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Search failed ({response.status_code}): {error_detail}")
            
            response.raise_for_status()
            
            results_data = response.json()
            
            # 결과 변환
            related_incidents = []
            for result in results_data.get('value', []):
                raw_score = result.get('@search.score', 0.0)
                
                # 정규화
                normalized_score = min(raw_score / 10.0, 1.0) if raw_score > 10 else raw_score / 10.0
                
                related_incidents.append({
                    'incident': {
                        'id': result.get('id'),
                        'title': result.get('title'),
                        'description': result.get('description'),
                        'system': result.get('system'),
                        'severity': result.get('severity'),
                        'status': result.get('status'),
                        'reported_date': result.get('reported_date'),
                        'resolved_date': result.get('resolved_date'),
                        'duration_minutes': result.get('duration_minutes'),
                        'affected_users': result.get('affected_users'),
                        'root_cause': result.get('root_cause'),
                        'resolution': result.get('resolution'),
                        'impact': result.get('impact'),
                        'business_impact': result.get('business_impact'),
                        'related_components': result.get('related_components', []),
                    },
                    'correlation_score': normalized_score,
                    'match_reason': self._build_incident_match_reason(result),
                    'raw_score': raw_score
                })
            
            return related_incidents
            
        except Exception as e:
            print(f"⚠️  Azure Search 검색 실패: {e}")
            return []
    
    def _build_incident_match_reason(self, result: Dict) -> str:
        """장애 매치 이유 구성"""
        reasons = []
        
        if result.get('@search.highlights'):
            highlights = result['@search.highlights']
            if highlights.get('title'):
                reasons.append("제목 일치")
            if highlights.get('description'):
                reasons.append("설명 일치")
            if highlights.get('root_cause'):
                reasons.append("근본 원인 일치")
        
        if result.get('system'):
            reasons.append(f"시스템: {result['system']}")
        
        if result.get('severity'):
            reasons.append(f"심각도: {result['severity']}")
        
        if result.get('related_components'):
            components = result['related_components'][:2]
            if components:
                reasons.append(f"컴포넌트: {', '.join(components)}")
        
        return ", ".join(reasons) if reasons else "텍스트 유사성"
    
    def list_indexes(self) -> List[str]:
        """인덱스 목록 조회"""
        try:
            result = self._make_request('GET', 'indexes')
            return [idx['name'] for idx in result.get('value', [])]
        except Exception as e:
            print(f"⚠️  인덱스 목록 조회 실패: {e}")
            return []

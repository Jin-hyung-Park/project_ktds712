"""
Azure AI Search 클라이언트
Azure SDK를 사용한 인덱스 관리 및 데이터 검색
노트북 스타일로 구현
"""
from __future__ import annotations  # Python 3.8 호환성을 위한 타입 힌트

from typing import List, Dict, Any, Optional
import sys
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
)
from .config import Config


class AzureSearchClient:
    """Azure AI Search 클라이언트 (Azure SDK 사용)"""
    
    def __init__(self):
        self.config = Config()
        
        # 노트북 스타일: credential 객체 생성
        self.credential = AzureKeyCredential(self.config.AZURE_SEARCH_KEY)
        
        # 인덱스 클라이언트 초기화 (노트북 스타일)
        try:
            self.index_client = SearchIndexClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                credential=self.credential
            )
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            sys.exit(1)
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Azure Search 서비스 연결 실패: {e}")
            sys.exit(1)
        
        # 검색 클라이언트는 인덱스별로 동적으로 생성
        self._search_clients: Dict[str, SearchClient] = {}
    
    def _get_search_client(self, index_name: str) -> SearchClient:
        """검색 클라이언트 가져오기 (캐싱)
        노트: 이제 대부분의 메서드에서 직접 SearchClient를 생성하지만, 
        호환성을 위해 유지
        """
        if index_name not in self._search_clients:
            self._search_clients[index_name] = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=self.credential
            )
        return self._search_clients[index_name]
    
    def create_sr_index(self, index_name: Optional[str] = None) -> bool:
        """SR 인덱스 생성 (노트북 스타일)"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # 인덱스가 이미 존재하는지 확인
            try:
                existing_index = self.index_client.get_index(index_name)
                if existing_index:
                    print(f"ℹ️  인덱스 '{index_name}'가 이미 존재합니다.")
                    return True
            except Exception:
                pass  # 인덱스가 없으면 생성 진행
            
            # 인덱스 스키마 정의 (PDF 파일 구조와 일치)
            # PDF 필드 매핑:
            # - SR ID (기본정보) -> id
            # - 제목 (기본정보) -> title
            # - 시스템 (기본정보) -> system
            # - 우선순위 (기본정보) -> priority
            # - 카테고리 (기본정보) -> category
            # - 요청자 (기본정보) -> requester
            # - 생성일 (기본정보) -> created_date
            # - 목표일 (기본정보) -> target_date
            # - 설명 (본문) -> description
            # - 비즈니스 임팩트 (본문) -> business_impact
            # - 기술 요구사항 (본문, 배열) -> technical_requirements
            # - 영향받는 컴포넌트 (본문, 배열) -> affected_components
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, searchable=False),  # PDF: SR ID
                SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),  # PDF: 제목
                SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),  # PDF: 설명
                SearchableField(name="system", type=SearchFieldDataType.String, filterable=True, facetable=True),  # PDF: 시스템
                SearchableField(name="priority", type=SearchFieldDataType.String, filterable=True, facetable=True),  # PDF: 우선순위
                SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),  # PDF: 카테고리
                SearchableField(name="requester", type=SearchFieldDataType.String),  # PDF: 요청자
                SimpleField(name="created_date", type=SearchFieldDataType.String, filterable=True),  # PDF: 생성일
                SimpleField(name="target_date", type=SearchFieldDataType.String, filterable=True),  # PDF: 목표일
                SearchableField(name="business_impact", type=SearchFieldDataType.String),  # PDF: 비즈니스 임팩트
                SearchableField(name="technical_requirements", type=SearchFieldDataType.String, collection=True, analyzer_name="ko.lucene"),  # PDF: 기술 요구사항 (배열)
                SearchableField(name="affected_components", type=SearchFieldDataType.String, collection=True, filterable=True, facetable=True),  # PDF: 영향받는 컴포넌트 (배열)
            ]
            
            # 인덱스 생성 (노트북 스타일)
            index = SearchIndex(name=index_name, fields=fields)
            result = self.index_client.create_or_update_index(index)
            
            print(f"✅ SR 인덱스 '{result.name}' 생성 완료")
            return True
            
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            return False
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            return False
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
            return False
    
    def index_sr_documents(self, srs: List[Dict[str, Any]], index_name: Optional[str] = None) -> bool:
        """SR 문서들을 인덱스에 업로드 (노트북 스타일)"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # SearchClient 생성 (노트북 스타일)
            search_client = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=self.credential
            )
            
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
                documents.append(doc)
            
            # 배치로 업로드 (노트북 스타일: upload_documents 직접 호출)
            batch_size = 1000
            total_succeeded = 0
            total_failed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                try:
                    # 노트북 스타일: upload_documents 직접 사용
                    result = search_client.upload_documents(documents=batch)
                    
                    # 결과 확인
                    succeeded = sum(1 for r in result if r.succeeded)
                    failed = len(batch) - succeeded
                    
                    total_succeeded += succeeded
                    total_failed += failed
                    
                    if failed > 0:
                        failed_items = [r for r in result if not r.succeeded]
                        print(f"⚠️  {failed}개 문서 업로드 실패")
                        for fail in failed_items[:5]:  # 최대 5개만 출력
                            print(f"   - {fail.key}: {fail.error_message}")
                            
                except Exception as e:
                    print(f"⚠️  배치 업로드 실패: {e}")
                    total_failed += len(batch)
            
            if total_failed == 0:
                print(f"✅ {total_succeeded}개 SR 문서 인덱싱 완료")
            else:
                print(f"⚠️  {total_succeeded}개 성공, {total_failed}개 실패")
            
            return total_failed == 0
            
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            return False
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            return False
        except Exception as e:
            print(f"❌ 문서 인덱싱 실패: {e}")
            return False
    
    def search_similar_srs(self, query_text: str, top_k: int = 5, 
                          filters: Optional[Dict[str, Any]] = None,
                          index_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """유사한 SR 검색 (노트북 스타일: query_type="simple" 명시)"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_SR
        
        try:
            # SearchClient 생성 (노트북 스타일)
            search_client = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=self.credential
            )
            
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
            
            # 검색 실행 (노트북 스타일: 명시적 파라미터 전달)
            if filter_expr:
                results = search_client.search(
                    query_type="simple",
                    search_text=query_text,
                    select="id, title, description, system, priority, category, requester, created_date, target_date, business_impact, technical_requirements, affected_components",
                    top=top_k,
                    filter=filter_expr,
                    include_total_count=True
                )
            else:
                results = search_client.search(
                    query_type="simple",
                    search_text=query_text,
                    select="id, title, description, system, priority, category, requester, created_date, target_date, business_impact, technical_requirements, affected_components",
                    top=top_k,
                    include_total_count=True
                )
            
            # 결과 변환
            similar_srs = []
            for result in results:
                raw_score = result.get('@search.score', 0.0)
                
                # 정규화 (Azure Search 점수는 가변적이므로 0-1 범위로 변환)
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
            
        except ClientAuthenticationError as auth_error:
            print(f"⚠️  인증 오류: {auth_error.message}")
            return []
        except HttpResponseError as http_error:
            print(f"⚠️  HTTP 오류: {http_error.message}")
            return []
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
    
    def create_incident_index(self, index_name: Optional[str] = None) -> bool:
        """장애 인덱스 생성 (노트북 스타일)"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # 인덱스가 이미 존재하는지 확인
            try:
                existing_index = self.index_client.get_index(index_name)
                if existing_index:
                    print(f"ℹ️  인덱스 '{index_name}'가 이미 존재합니다.")
                    return True
            except Exception:
                pass  # 인덱스가 없으면 생성 진행
            
            # 인덱스 스키마 정의 (노트북 스타일)
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, searchable=False),
                SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),
                SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),
                SearchableField(name="system", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SearchableField(name="severity", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SearchableField(name="status", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="reported_date", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="resolved_date", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="duration_minutes", type=SearchFieldDataType.Int32, filterable=True),
                SimpleField(name="affected_users", type=SearchFieldDataType.Int32, filterable=True),
                SearchableField(name="root_cause", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),
                SearchableField(name="resolution", type=SearchFieldDataType.String, analyzer_name="ko.lucene"),
                SearchableField(name="impact", type=SearchFieldDataType.String),
                SearchableField(name="business_impact", type=SearchFieldDataType.String),
                SearchableField(name="related_components", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
            ]
            
            # 인덱스 생성 (노트북 스타일)
            index = SearchIndex(name=index_name, fields=fields)
            result = self.index_client.create_or_update_index(index)
            
            print(f"✅ 장애 인덱스 '{result.name}' 생성 완료")
            return True
            
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            return False
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            return False
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
            return False
    
    def index_incident_documents(self, incidents: List[Dict[str, Any]], index_name: Optional[str] = None) -> bool:
        """장애 문서들을 인덱스에 업로드 (노트북 스타일)"""
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # SearchClient 생성 (노트북 스타일)
            search_client = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=self.credential
            )
            
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
                documents.append(doc)
            
            # 배치로 업로드 (노트북 스타일)
            batch_size = 1000
            total_succeeded = 0
            total_failed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                try:
                    # 노트북 스타일: upload_documents 직접 사용
                    result = search_client.upload_documents(documents=batch)
                    
                    # 결과 확인
                    succeeded = sum(1 for r in result if r.succeeded)
                    failed = len(batch) - succeeded
                    
                    total_succeeded += succeeded
                    total_failed += failed
                    
                    if failed > 0:
                        failed_items = [r for r in result if not r.succeeded]
                        print(f"⚠️  {failed}개 문서 업로드 실패")
                        for fail in failed_items[:5]:  # 최대 5개만 출력
                            print(f"   - {fail.key}: {fail.error_message}")
                            
                except Exception as e:
                    print(f"⚠️  배치 업로드 실패: {e}")
                    total_failed += len(batch)
            
            if total_failed == 0:
                print(f"✅ {total_succeeded}개 장애 문서 인덱싱 완료")
            else:
                print(f"⚠️  {total_succeeded}개 성공, {total_failed}개 실패")
            
            return total_failed == 0
            
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            return False
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            return False
        except Exception as e:
            print(f"❌ 문서 인덱싱 실패: {e}")
            return False
    
    def search_related_incidents(self, query_text: str, top_k: int = 5,
                                filters: Optional[Dict[str, Any]] = None,
                                index_name: Optional[str] = None,
                                use_semantic: bool = True) -> List[Dict[str, Any]]:
        """관련 장애 검색 (노트북 스타일: semantic 검색 지원)
        
        Args:
            query_text: 검색 쿼리 텍스트
            top_k: 반환할 최대 결과 수
            filters: 필터 조건
            index_name: 인덱스 이름
            use_semantic: True면 semantic 검색 사용 (기본값, README의 "semantic" 방식),
                         False면 simple 검색
        """
        if not index_name:
            index_name = self.config.AZURE_SEARCH_INDEX_INCIDENT
        
        try:
            # SearchClient 생성 (노트북 스타일)
            search_client = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=self.credential
            )
            
            # 필터 구성
            filter_expr = None
            if filters:
                filter_parts = []
                if filters.get('system'):
                    filter_parts.append(f"system eq '{filters['system']}'")
                if filter_parts:
                    filter_expr = " and ".join(filter_parts)
            
            # 선택할 필드 정의
            select_fields = "id, title, description, system, severity, status, reported_date, resolved_date, duration_minutes, affected_users, root_cause, resolution, impact, business_impact, related_components"
            
            # 검색 실행 (노트북 스타일: Python 3.11에서는 semantic 검색 완전 지원)
            if use_semantic:
                # Semantic 검색 (노트북 02번 스타일)
                if filter_expr:
                    results = search_client.search(
                        query_type="semantic",
                        semantic_configuration_name="semantic-config",  # 인덱스에 설정된 semantic config 이름
                        search_text=query_text,
                        select=select_fields,
                        top=top_k,
                        filter=filter_expr,
                        include_total_count=True
                    )
                else:
                    results = search_client.search(
                        query_type="semantic",
                        semantic_configuration_name="semantic-config",
                        search_text=query_text,
                        select=select_fields,
                        top=top_k,
                        include_total_count=True
                    )
            else:
                # Simple 검색 (노트북 01번 스타일)
                if filter_expr:
                    results = search_client.search(
                        query_type="simple",
                        search_text=query_text,
                        select=select_fields,
                        top=top_k,
                        filter=filter_expr,
                        include_total_count=True
                    )
                else:
                    results = search_client.search(
                        query_type="simple",
                        search_text=query_text,
                        select=select_fields,
                        top=top_k,
                        include_total_count=True
                    )
            
            # 결과 변환
            related_incidents = []
            for result in results:
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
            
        except ClientAuthenticationError as auth_error:
            print(f"⚠️  인증 오류: {auth_error.message}")
            return []
        except HttpResponseError as http_error:
            print(f"⚠️  HTTP 오류: {http_error.message}")
            return []
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
    
    def delete_index(self, index_name: str) -> bool:
        """인덱스 삭제 (노트북 스타일)"""
        try:
            result = self.index_client.delete_index(index_name)
            print(f"✅ 인덱스 '{index_name}' 삭제 완료")
            return True
        except ClientAuthenticationError as auth_error:
            print(f"❌ 인증 오류: {auth_error.message}")
            return False
        except HttpResponseError as http_error:
            print(f"❌ HTTP 오류: {http_error.message}")
            return False
        except Exception as e:
            print(f"❌ 인덱스 삭제 실패: {e}")
            return False
    
    def list_indexes(self) -> List[str]:
        """인덱스 목록 조회"""
        try:
            indexes = self.index_client.list_indexes()
            return [idx.name for idx in indexes]
        except Exception as e:
            print(f"⚠️  인덱스 목록 조회 실패: {e}")
            return []

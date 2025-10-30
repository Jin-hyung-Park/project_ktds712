"""
장애 검색 RAG 시스템
Azure Search와 OpenAI를 활용한 장애 검색 및 분석 기능
벡터 검색을 통한 유사 장애 검색 및 해결 방안 제시
"""
from typing import Dict, List, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError
from openai import AzureOpenAI
import sys
import json
from config import Config

config = Config()

# 장애 검색을 위한 기본 프롬프트 템플릿
INCIDENT_GROUNDED_PROMPT = """
당신은 장애 분석 및 해결 방안 제시를 위한 전문 어시스턴트입니다.
아래 제공된 장애 정보를 바탕으로 쿼리에 답변하세요.

각 장애에 대해 다음 정보를 포함하여 분석하세요:
- 장애 ID 및 제목
- 장애 유형 및 심각도
- 발생 원인 및 영향 범위
- 해결 방안 및 예방 조치
- 관련 시스템 및 컴포넌트

아래 소스에 나열된 사실만을 사용하여 답변하세요.
충분한 정보가 없으면 모른다고 말하세요.
소스에 없는 내용을 포함한 답변을 생성하지 마세요.

쿼리: {query}

장애 정보:\n{sources}
"""


class IncidentRAGSearch:
    """장애 검색 RAG 클래스"""
    
    def __init__(self, 
                 index_name: str = "rag-inc-ktds712",
                 config: Optional[Config] = None):
        """
        초기화
        
        Args:
            index_name: Azure Search 인덱스 이름
            config: Config 객체 (None이면 새로 생성)
        """
        self.config = config or Config()
        self.index_name = index_name
        
        # Azure Search 클라이언트 초기화
        try:
            search_credentials = AzureKeyCredential(self.config.AZURE_SEARCH_KEY)
            self.search_client = SearchClient(
                endpoint=self.config.AZURE_SEARCH_ENDPOINT,
                index_name=self.index_name,
                credential=search_credentials
            )
        except ClientAuthenticationError as auth_error:
            raise RuntimeError(f"Azure Search 인증 실패: {auth_error.message}")
        except HttpResponseError as http_error:
            raise RuntimeError(f"Azure Search HTTP 오류: {http_error.message}")
        except Exception as e:
            raise RuntimeError(f"Azure Search 연결 실패: {e}")
        
        # OpenAI 클라이언트 초기화
        try:
            self.openai_client = AzureOpenAI(
                api_version="2024-12-01-preview",
                azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT,
                api_key=self.config.AZURE_OPENAI_KEY,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {e}")
    
    def _format_incident_document(self, document: Dict[str, Any]) -> str:
        """장애 문서를 포맷팅하여 문자열로 변환"""
        return (
            f"장애 ID: {document.get('parent_id', 'N/A')}\n"
            f"청크 ID: {document.get('chunk_id', 'N/A')}\n"
            f"제목: {document.get('title', 'N/A')}\n"
            f"내용: {document.get('chunk', 'N/A')}\n"
            f"---"
        )
    
    def search_related_incidents(self, 
                                query: str,
                                top_k: int = 5,
                                use_llm: bool = True,
                                custom_prompt: Optional[str] = None,
                                search_mode: str = "hybrid") -> Dict[str, Any]:
        """
        연관 장애 검색 및 분석
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            use_llm: LLM을 사용하여 분석 생성 여부
            custom_prompt: 커스텀 프롬프트 (None이면 기본 프롬프트 사용)
            search_mode: 검색 모드 ("text", "vector", "hybrid")
        
        Returns:
            Dict containing:
                - total_count: 전체 검색 결과 수
                - documents: 검색된 문서 리스트
                - llm_response: LLM 응답 (use_llm=True인 경우)
                - sources_formatted: 포맷팅된 소스 문자열
        """
        try:
            # 검색 모드에 따른 파라미터 설정
            search_params = {
                "search_text": query,
                "top": top_k,
                "include_total_count": True,
                "select": "chunk_id, parent_id, chunk, title"
            }
            
            if search_mode == "vector":
                # 벡터 검색만 사용
                try:
                    query_vector = self._get_query_embedding(query)
                    vector_query = VectorizedQuery(
                        vector=query_vector,
                        k_nearest_neighbors=top_k,
                        fields="text_vector"
                    )
                    search_results = self.search_client.search(
                        search_text=None,
                        vector_queries=[vector_query],
                        top=top_k,
                        include_total_count=True,
                        select="chunk_id, parent_id, chunk, title"
                    )
                except Exception as e:
                    print(f"⚠️ 벡터 검색 실패, 텍스트 검색으로 대체: {e}")
                    search_mode = "text"
                    search_results = self.search_client.search(**search_params)
            elif search_mode == "hybrid":
                # 하이브리드 검색 (텍스트 + 벡터)
                try:
                    query_vector = self._get_query_embedding(query)
                    vector_query = VectorizedQuery(
                        vector=query_vector,
                        k_nearest_neighbors=top_k,
                        fields="text_vector"
                    )
                    search_results = self.search_client.search(
                        search_text=query,
                        vector_queries=[vector_query],
                        top=top_k,
                        include_total_count=True,
                        select="chunk_id, parent_id, chunk, title"
                    )
                except Exception as e:
                    print(f"⚠️ 하이브리드 검색 실패, 텍스트 검색으로 대체: {e}")
                    search_mode = "text"
                    search_results = self.search_client.search(**search_params)
            else:
                # text 모드는 기본 설정 사용
                search_results = self.search_client.search(**search_params)
            
            total_count = search_results.get_count() if hasattr(search_results, 'get_count') else 0
            
            # 검색 결과를 리스트로 변환
            documents = []
            for doc in search_results:
                documents.append(dict(doc))
            
            # 소스 포맷팅
            sources_formatted = "\n".join([
                self._format_incident_document(doc) for doc in documents
            ])
            
            result = {
                "total_count": total_count,
                "documents": documents,
                "sources_formatted": sources_formatted,
                "search_mode": search_mode
            }
            
            # LLM을 사용하여 분석 생성
            if use_llm:
                try:
                    prompt = custom_prompt or INCIDENT_GROUNDED_PROMPT
                    llm_response = self.openai_client.chat.completions.create(
                        model=self.config.AZURE_OPENAI_DEPLOYMENT,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt.format(
                                    query=query,
                                    sources=sources_formatted
                                ),
                            },
                        ]
                    )
                    
                    result["llm_response"] = llm_response.choices[0].message.content
                except Exception as e:
                    result["llm_error"] = str(e)
                    result["llm_response"] = None
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"장애 검색 실패: {e}")
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """쿼리를 벡터로 변환"""
        try:
            # 임베딩 전용 클라이언트 생성
            embedding_client = AzureOpenAI(
                api_version="2024-12-01-preview",
                azure_endpoint=self.config.AZURE_EMBEDDING_OPENAI_ENDPOINT,
                api_key=self.config.AZURE_EMBEDDING_OPENAI_KEY,
            )
            
            response = embedding_client.embeddings.create(
                model=self.config.AZURE_EMBEDDING_OPENAI_DEPLOYMENT,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"쿼리 임베딩 생성 실패: {e}")
    
    def search_by_incident_id(self, 
                             incident_id: str,
                             top_k: int = 10) -> Dict[str, Any]:
        """
        특정 장애 ID로 관련 청크 검색
        
        Args:
            incident_id: 장애 ID
            top_k: 반환할 결과 수
        
        Returns:
            검색 결과 딕셔너리
        """
        try:
            search_results = self.search_client.search(
                search_text="*",
                filter=f"parent_id eq '{incident_id}'",
                top=top_k,
                include_total_count=True,
                select="chunk_id, parent_id, chunk, title"
            )
            
            total_count = search_results.get_count() if hasattr(search_results, 'get_count') else 0
            
            documents = []
            for doc in search_results:
                documents.append(dict(doc))
            
            sources_formatted = "\n".join([
                self._format_incident_document(doc) for doc in documents
            ])
            
            return {
                "total_count": total_count,
                "documents": documents,
                "sources_formatted": sources_formatted,
                "incident_id": incident_id
            }
            
        except Exception as e:
            raise RuntimeError(f"장애 ID 검색 실패: {e}")


def search_related_incidents(query: str, 
                           top_k: int = 5,
                           index_name: str = "rag-inc-ktds712",
                           use_llm: bool = True,
                           search_mode: str = "vector",
                           config: Optional[Config] = None) -> Dict[str, Any]:
    """
    연관 장애 검색 함수 (간편 함수)
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 결과 수
        index_name: Azure Search 인덱스 이름
        use_llm: LLM을 사용하여 분석 생성 여부
        search_mode: 검색 모드 ("hybrid", "vector", "text")
        config: Config 객체 (None이면 새로 생성)
    
    Returns:
        검색 결과 딕셔너리:
            - total_count: 전체 검색 결과 수
            - documents: 검색된 문서 리스트
            - llm_response: LLM 응답 (use_llm=True인 경우)
            - sources_formatted: 포맷팅된 소스 문자열
            - search_mode: 사용된 검색 모드
    
    Example:
        >>> result = search_related_incidents("로그인 오류", top_k=3)
        >>> print(result['llm_response'])
        >>> for doc in result['documents']:
        ...     print(doc['title'])
    """
    searcher = IncidentRAGSearch(index_name=index_name, config=config)
    return searcher.search_related_incidents(
        query=query, 
        top_k=top_k, 
        use_llm=use_llm,
        search_mode=search_mode
    )


def search_incident_by_id(incident_id: str,
                         top_k: int = 10,
                         index_name: str = "rag-inc-ktds712",
                         config: Optional[Config] = None) -> Dict[str, Any]:
    """
    장애 ID로 관련 청크 검색 함수 (간편 함수)
    
    Args:
        incident_id: 장애 ID
        top_k: 반환할 결과 수
        index_name: Azure Search 인덱스 이름
        config: Config 객체 (None이면 새로 생성)
    
    Returns:
        검색 결과 딕셔너리
    """
    searcher = IncidentRAGSearch(index_name=index_name, config=config)
    return searcher.search_by_incident_id(incident_id=incident_id, top_k=top_k)


# 메인 실행 부분
if __name__ == "__main__":
    # 예시 쿼리들
    test_queries = [
        "위약금 계산 오류",
        "가입일 기준 월할 계산 기능 개발"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 쿼리: {query}")
        print('='*80)
        
        try:
            # 하이브리드 검색 실행
            result = search_related_incidents(
                query=query, 
                top_k=3, 
                use_llm=True,
                search_mode="vector"
            )
            
            print(f"Total results found: {result['total_count']}")
            print(f"Search mode: {result['search_mode']}")
            
            print("\n📋 검색된 장애 정보:")
            print("-" * 60)
            print(result['sources_formatted'])
            
            if result.get('llm_response'):
                print("\n🤖 LLM 분석 결과:")
                print("-" * 60)
                print(result['llm_response'])
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    # 특정 장애 ID 검색 예시
    print(f"\n{'='*80}")
    print("🔍 특정 장애 ID 검색 예시")
    print('='*80)
    
    try:
        incident_result = search_incident_by_id("INC-2024-001", top_k=5)
        print(f"장애 ID: INC-2024-001")
        print(f"총 청크 수: {incident_result['total_count']}")
        print("\n📋 장애 상세 정보:")
        print("-" * 60)
        print(incident_result['sources_formatted'])
        
    except Exception as e:
        print(f"❌ 장애 ID 검색 오류: {e}")

"""
연관 SR 검색 RAG 시스템
Azure Search와 OpenAI를 활용한 연관 SR 검색 및 추천 기능
"""
from typing import Dict, List, Any, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError
from openai import AzureOpenAI
import sys
from config import Config


# 기본 프롬프트 템플릿
GROUNDED_PROMPT = """
당신은 연관된 SR(Service Request)을 찾아 추천하는 전문 어시스턴트입니다.
아래 제공된 소스에서 찾은 정보만을 사용하여 쿼리에 답변하세요.
각 연관 SR에 대해 SR ID, 제목, 시스템, 우선순위, 카테고리, 기술 요구사항, 영향받는 컴포넌트, 비즈니스 임팩트를 포함하여 간결하고 구조화된 형태로 답변하세요.
아래 소스에 나열된 사실만 사용하세요.
충분한 정보가 없으면 모른다고 말하세요.
소스에 없는 내용을 포함한 답변을 생성하지 마세요.

쿼리: {query}

소스:\n{sources}
"""


class SRRAGSearch:
    """연관 SR 검색 RAG 클래스"""
    
    def __init__(self, 
                 index_name: str = "key-sr-ktds712",
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
    
    def _format_document(self, document: Dict[str, Any]) -> str:
        """문서를 포맷팅하여 문자열로 변환"""
        tech_reqs = document.get('technical_requirements', [])
        if isinstance(tech_reqs, list):
            tech_reqs_str = ', '.join(tech_reqs) if tech_reqs else 'N/A'
        else:
            tech_reqs_str = str(tech_reqs)
        
        components = document.get('affected_components', [])
        if isinstance(components, list):
            components_str = ', '.join(components) if components else 'N/A'
        else:
            components_str = str(components)
        
        return (
            f"SR ID: {document.get('id', 'N/A')}\n"
            f"제목: {document.get('title', 'N/A')}\n"
            f"설명: {document.get('description', 'N/A')}\n"
            f"시스템: {document.get('system', 'N/A')}\n"
            f"우선순위: {document.get('priority', 'N/A')}\n"
            f"카테고리: {document.get('category', 'N/A')}\n"
            f"요청자: {document.get('requester', 'N/A')}\n"
            f"생성일: {document.get('created_date', 'N/A')}\n"
            f"목표일: {document.get('target_date', 'N/A')}\n"
            f"비즈니스 임팩트: {document.get('business_impact', 'N/A')}\n"
            f"기술 요구사항: {tech_reqs_str}\n"
            f"영향받는 컴포넌트: {components_str}\n"
            f"---"
        )
    
    def search_related_srs(self, 
                           query: str,
                           top_k: int = 5,
                           fields: Optional[List[str]] = None,
                           use_llm: bool = True,
                           custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        연관 SR 검색 및 추천
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            fields: 검색할 필드 목록 (None이면 모든 필드)
            use_llm: LLM을 사용하여 추천 생성 여부
            custom_prompt: 커스텀 프롬프트 (None이면 기본 프롬프트 사용)
        
        Returns:
            Dict containing:
                - total_count: 전체 검색 결과 수
                - documents: 검색된 문서 리스트
                - llm_response: LLM 응답 (use_llm=True인 경우)
                - sources_formatted: 포맷팅된 소스 문자열
        """
        # 기본 필드 설정
        if fields is None:
            fields = [
                "id", "title", "description", "system", "priority", "category",
                "requester", "created_date", "target_date", "business_impact",
                "technical_requirements", "affected_components"
            ]
        
        select_fields = ", ".join(fields)
        
        try:
            # Azure Search로 검색
            search_results = self.search_client.search(
                search_text=query,
                select=select_fields,
                top=top_k,
                include_total_count=True
            )
            
            total_count = search_results.get_count() if hasattr(search_results, 'get_count') else 0
            
            # 검색 결과를 리스트로 변환
            documents = []
            for doc in search_results:
                documents.append(dict(doc))
            
            # 소스 포맷팅
            sources_formatted = "\n".join([
                self._format_document(doc) for doc in documents
            ])
            
            result = {
                "total_count": total_count,
                "documents": documents,
                "sources_formatted": sources_formatted
            }
            
            # LLM을 사용하여 추천 생성
            if use_llm:
                try:
                    prompt = custom_prompt or GROUNDED_PROMPT
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
            raise RuntimeError(f"검색 실패: {e}")


def search_related_srs(query: str, 
                       top_k: int = 5,
                       index_name: str = "key-sr-ktds712",
                       use_llm: bool = True,
                       config: Optional[Config] = None) -> Dict[str, Any]:
    """
    연관 SR 검색 함수 (간편 함수)
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 결과 수
        index_name: Azure Search 인덱스 이름
        use_llm: LLM을 사용하여 추천 생성 여부
        config: Config 객체 (None이면 새로 생성)
    
    Returns:
        검색 결과 딕셔너리:
            - total_count: 전체 검색 결과 수
            - documents: 검색된 문서 리스트
            - llm_response: LLM 응답 (use_llm=True인 경우)
            - sources_formatted: 포맷팅된 소스 문자열
    
    Example:
        >>> result = search_related_srs("월정액 요금 계산", top_k=3)
        >>> print(result['llm_response'])
        >>> for doc in result['documents']:
        ...     print(doc['title'])
    """
    searcher = SRRAGSearch(index_name=index_name, config=config)
    return searcher.search_related_srs(query=query, top_k=top_k, use_llm=use_llm)


# 메인 실행 부분
if __name__ == "__main__":
    query = "가입일 기준 월할 계산 기능 개발 연관된 SR을 검색해주세요."
    
    try:
        # 함수로 검색 실행
        result = search_related_srs(query=query, top_k=3, use_llm=True)
        
        print(f"Total results found: {result['total_count']}")
        print("\n" + "=" * 80)
        print("검색된 문서:")
        print("=" * 80)
        print(result['sources_formatted'])
        
        if result.get('llm_response'):
            print("\n" + "=" * 80)
            print("LLM 응답:")
            print("=" * 80)
            print(result['llm_response'])
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

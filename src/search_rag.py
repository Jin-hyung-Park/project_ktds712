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
    
    def _build_search_query(self, user_query: str) -> str:
        """LLM을 사용해 인덱스 친화적인 검색 쿼리로 정제

        목적/요청 상세 등 자연어 입력을 Azure Cognitive Search에 적합한 키워드/구문으로 축약
        실패 시 원본 쿼리를 그대로 반환
        """
        try:
            system_prompt = (
                "너는 Azure AI Search용 쿼리 빌더다. 입력 텍스트에서 핵심 키워드와 \n"
                "필드 연관 단어를 뽑아 검색 효율이 높은 간결한 쿼리를 만들어라. \n"
                "불필요한 문장은 제거하고, 핵심 명사구/기술용어/시스템명/카테고리/우선순위/\n"
                "기술요구사항/영향 컴포넌트를 중심으로 10~25단어 이내 한국어 키워드 열로 구성해라. \n"
                "따옴표나 마크다운 없이 평문으로만 출력해라."
            )
            completion = self.openai_client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.2,
            )
            refined = (completion.choices[0].message.content or "").strip()
            # 너무 짧게 오면 원본 유지
            return refined if len(refined.split()) >= 3 else user_query
        except Exception:
            return user_query
    
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
                           custom_prompt: Optional[str] = None,
                           use_query_builder: bool = True) -> Dict[str, Any]:
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
            # 쿼리 빌더로 인덱스 친화적 쿼리 생성
            original_query = query
            if use_query_builder:
                query = self._build_search_query(query)
                try:
                    print(f"🔧 SR 쿼리 빌더 적용: '{original_query[:60]}...' => '{query[:120]}'")
                except Exception:
                    pass
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
                        ],
                        temperature=0.2
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
    query = """    신규 결제 시스템 개발 - 실시간 결제 처리 및 다중 결제 수단 지원
    
    기존 결제 시스템의 성능 문제와 다중 결제 수단 지원 부족을 해결하기 위해 
    새로운 결제 시스템을 개발합니다.

    주요 요구사항:
    1. 실시간 결제 처리 (응답 시간 < 3초)
    2. 신용카드, 계좌이체, 간편결제 지원
    3. 결제 실패 시 자동 재시도 메커니즘
    4. 결제 내역 실시간 조회 및 알림
    5. PCI DSS 보안 규정 준수
    6. 99.9% 가용성 보장

    기술 스택:
    - Backend: Node.js + Express
    - Database: PostgreSQL + Redis
    - Payment Gateway: 토스페이먼츠, KG모빌리언스
    - Monitoring: Prometheus + Grafana
    """
    
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

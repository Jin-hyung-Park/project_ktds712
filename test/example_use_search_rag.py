"""
search_rag.py 사용 예시
외부에서 연관 SR 검색 기능을 호출하는 방법을 보여줍니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.search_rag import search_related_srs, SRRAGSearch


def example_1_simple_function():
    """예시 1: 간편 함수 사용"""
    print("=" * 80)
    print("예시 1: 간편 함수 사용")
    print("=" * 80)
    
    query = "월정액 요금 계산"
    result = search_related_srs(query=query, top_k=3, use_llm=True)
    
    print(f"\n검색 결과 수: {result['total_count']}")
    print(f"\n검색된 문서 수: {len(result['documents'])}")
    
    if result.get('llm_response'):
        print(f"\nLLM 추천:\n{result['llm_response']}")


def example_2_class_usage():
    """예시 2: 클래스 사용 (재사용 가능)"""
    print("\n" + "=" * 80)
    print("예시 2: 클래스 사용")
    print("=" * 80)
    
    # 클래스 인스턴스 생성 (재사용 가능)
    searcher = SRRAGSearch(index_name="key-sr-ktds712")
    
    # 여러 번 검색 가능
    queries = [
        "성능 최적화",
        "할인 계산",
        "사용료 계산"
    ]
    
    for query in queries:
        print(f"\n검색어: {query}")
        result = searcher.search_related_srs(query=query, top_k=2, use_llm=False)
        print(f"  결과 수: {result['total_count']}")
        if result['documents']:
            print(f"  첫 번째 결과: {result['documents'][0]['title']}")


def example_3_custom_prompt():
    """예시 3: 커스텀 프롬프트 사용"""
    print("\n" + "=" * 80)
    print("예시 3: 커스텀 프롬프트 사용")
    print("=" * 80)
    
    custom_prompt = """
    당신은 SR 분석 전문가입니다.
    아래 SR들을 분석하여 비슷한 점과 차이점을 설명하세요.
    
    쿼리: {query}
    소스:\n{sources}
    """
    
    searcher = SRRAGSearch()
    result = searcher.search_related_srs(
        query="요금 계산 관련",
        top_k=2,
        use_llm=True,
        custom_prompt=custom_prompt
    )
    
    if result.get('llm_response'):
        print(result['llm_response'])


def example_4_search_only():
    """예시 4: 검색만 수행 (LLM 없이)"""
    print("\n" + "=" * 80)
    print("예시 4: 검색만 수행")
    print("=" * 80)
    
    result = search_related_srs(
        query="요금계산시스템",
        top_k=5,
        use_llm=False  # LLM 사용 안 함
    )
    
    print(f"전체 결과: {result['total_count']}개")
    print(f"\n검색된 SR 목록:")
    for i, doc in enumerate(result['documents'], 1):
        print(f"{i}. [{doc.get('id', 'N/A')}] {doc.get('title', 'N/A')}")
        print(f"   시스템: {doc.get('system', 'N/A')}, 우선순위: {doc.get('priority', 'N/A')}")


def example_5_detailed_result():
    """예시 5: 상세 결과 활용"""
    print("\n" + "=" * 80)
    print("예시 5: 상세 결과 활용")
    print("=" * 80)
    
    result = search_related_srs(
        query="개선 카테고리의 SR",
        top_k=3,
        use_llm=True
    )
    
    # 검색된 문서 상세 정보
    print("\n📋 검색된 SR 상세 정보:")
    for i, doc in enumerate(result['documents'], 1):
        print(f"\n{i}. {doc.get('title', 'N/A')}")
        print(f"   ID: {doc.get('id', 'N/A')}")
        print(f"   시스템: {doc.get('system', 'N/A')}")
        print(f"   우선순위: {doc.get('priority', 'N/A')}")
        print(f"   카테고리: {doc.get('category', 'N/A')}")
        print(f"   기술 요구사항: {', '.join(doc.get('technical_requirements', []))}")
    
    # LLM 응답
    if result.get('llm_response'):
        print("\n🤖 AI 추천:")
        print(result['llm_response'])


if __name__ == "__main__":
    try:
        # 예시 실행
        example_1_simple_function()
        # example_2_class_usage()
        # example_3_custom_prompt()
        # example_4_search_only()
        # example_5_detailed_result()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


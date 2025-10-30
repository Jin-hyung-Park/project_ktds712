#!/usr/bin/env python3
"""
장애 검색 RAG 시스템 사용 예시
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.incident_rag import search_related_incidents, search_incident_by_id

def test_incident_search():
    """장애 검색 테스트"""
    print("🚨 장애 검색 RAG 시스템 테스트")
    print("=" * 80)
    
    # 테스트 쿼리들
    test_queries = [
        "로그인 오류 관련 장애",
        "데이터베이스 연결 문제",
        "메모리 부족으로 인한 서비스 중단",
        "API 응답 지연 문제",
        "인증 시스템 장애"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {query}")
        print("-" * 60)
        
        try:
            # 하이브리드 검색 실행
            result = search_related_incidents(
                query=query, 
                top_k=3, 
                use_llm=True,
                search_mode="hybrid"
            )
            
            print(f"✅ 검색 완료 - 총 {result['total_count']}개 결과")
            print(f"🔧 검색 모드: {result['search_mode']}")
            
            if result.get('llm_response'):
                print(f"\n🤖 AI 분석:")
                print(result['llm_response'])
            else:
                print("\n📋 검색된 장애 정보:")
                print(result['sources_formatted'])
            
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # 특정 장애 ID 검색 테스트
    print(f"\n{'='*80}")
    print("🔍 특정 장애 ID 검색 테스트")
    print('='*80)
    
    test_incident_ids = ["INC-2024-001", "INC-2024-002", "INC-2024-003"]
    
    for incident_id in test_incident_ids:
        print(f"\n📋 장애 ID: {incident_id}")
        print("-" * 40)
        
        try:
            result = search_incident_by_id(incident_id, top_k=5)
            print(f"✅ 검색 완료 - 총 {result['total_count']}개 청크")
            
            if result['total_count'] > 0:
                print("\n📄 장애 상세 정보:")
                print(result['sources_formatted'])
            else:
                print("ℹ️ 해당 장애 ID의 정보를 찾을 수 없습니다.")
            
        except Exception as e:
            print(f"❌ 장애 ID 검색 실패: {e}")

def test_different_search_modes():
    """다양한 검색 모드 테스트"""
    print(f"\n{'='*80}")
    print("🔍 다양한 검색 모드 테스트")
    print('='*80)
    
    query = "로그인 오류"
    search_modes = ["hybrid", "vector", "text"]
    
    for mode in search_modes:
        print(f"\n🔧 검색 모드: {mode}")
        print("-" * 40)
        
        try:
            result = search_related_incidents(
                query=query, 
                top_k=2, 
                use_llm=False,  # LLM 없이 검색 결과만 확인
                search_mode=mode
            )
            
            print(f"✅ {mode} 검색 완료 - {result['total_count']}개 결과")
            print(f"📋 검색된 정보:")
            print(result['sources_formatted'])
            
        except Exception as e:
            print(f"❌ {mode} 검색 실패: {e}")

def interactive_search():
    """대화형 검색"""
    print(f"\n{'='*80}")
    print("💬 대화형 장애 검색")
    print('='*80)
    print("장애 관련 키워드를 입력하세요. (종료하려면 'quit' 입력)")
    
    while True:
        try:
            query = input("\n🔍 검색어: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료']:
                print("👋 검색을 종료합니다.")
                break
            
            if not query:
                print("⚠️ 검색어를 입력해주세요.")
                continue
            
            print(f"\n🔍 '{query}' 검색 중...")
            
            result = search_related_incidents(
                query=query, 
                top_k=3, 
                use_llm=True,
                search_mode="hybrid"
            )
            
            print(f"\n✅ 검색 완료 - {result['total_count']}개 결과")
            
            if result.get('llm_response'):
                print(f"\n🤖 AI 분석:")
                print(result['llm_response'])
            else:
                print("\n📋 검색된 장애 정보:")
                print(result['sources_formatted'])
            
        except KeyboardInterrupt:
            print("\n\n👋 검색을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")

if __name__ == "__main__":
    print("🚨 장애 검색 RAG 시스템 예시")
    print("=" * 80)
    print("1. 기본 검색 테스트")
    print("2. 다양한 검색 모드 테스트") 
    print("3. 대화형 검색")
    print("4. 모든 테스트 실행")
    
    try:
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == "1":
            test_incident_search()
        elif choice == "2":
            test_different_search_modes()
        elif choice == "3":
            interactive_search()
        elif choice == "4":
            test_incident_search()
            test_different_search_modes()
        else:
            print("❌ 잘못된 선택입니다. 기본 테스트를 실행합니다.")
            test_incident_search()
            
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

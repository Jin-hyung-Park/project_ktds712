"""
Azure AI Search 인덱스 초기화 스크립트
SR 및 장애 데이터를 Azure AI Search에 인덱싱
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import DataLoader
from src.sr_search_engine import SRSearchEngine
from src.incident_search_engine import IncidentSearchEngine

def setup_indices():
    """SR 및 장애 인덱스 초기화"""
    print("🚀 Azure AI Search 인덱스 초기화 시작\n")
    
    # 데이터 로더 초기화
    loader = DataLoader()
    
    try:
        # SR 검색 엔진 초기화
        sr_searcher = SRSearchEngine(loader)
        print("✅ SR 검색 엔진 초기화 완료")
        
        # 장애 검색 엔진 초기화
        incident_searcher = IncidentSearchEngine(loader)
        print("✅ 장애 검색 엔진 초기화 완료\n")
        
    except (ValueError, RuntimeError) as e:
        print(f"❌ 초기화 실패: {e}")
        return False
    
    # SR 인덱스 초기화
    print("=" * 60)
    print("📊 SR 인덱스 생성 및 데이터 업로드")
    print("=" * 60)
    
    if not sr_searcher.initialize_index():
        print("\n❌ SR 인덱스 초기화 실패")
        return False
    
    print("\n✅ SR 인덱스 초기화 완료!")
    
    # 장애 인덱스 초기화
    print("\n" + "=" * 60)
    print("📊 장애 인덱스 생성 및 데이터 업로드")
    print("=" * 60)
    
    if not incident_searcher.initialize_index():
        print("\n❌ 장애 인덱스 초기화 실패")
        return False
    
    print("\n✅ 장애 인덱스 초기화 완료!")
    
    # 검색 테스트
    print("\n" + "=" * 60)
    print("🔍 검색 테스트")
    print("=" * 60)
    
    srs = loader.load_sr_data()
    if srs:
        test_sr = srs[0]
        print(f"\n테스트 SR: {test_sr['title']}")
        
        # SR 검색 테스트
        sr_results = sr_searcher.search_similar(test_sr, top_k=3)
        print(f"\n유사한 SR 검색 결과 ({len(sr_results)}개):")
        for i, result in enumerate(sr_results, 1):
            print(f"\n  {i}. {result['sr']['title']}")
            print(f"     유사도: {result['similarity_score']:.3f}")
            print(f"     매치 이유: {result['match_reason']}")
        
        # 장애 검색 테스트
        incident_results = incident_searcher.search_related(test_sr, top_k=3)
        print(f"\n관련 장애 검색 결과 ({len(incident_results)}개):")
        for i, result in enumerate(incident_results, 1):
            print(f"\n  {i}. {result['incident']['title']}")
            print(f"     연관도: {result['correlation_score']:.3f}")
            print(f"     매치 이유: {result['match_reason']}")
    
    return True

if __name__ == "__main__":
    success = setup_indices()
    sys.exit(0 if success else 1)


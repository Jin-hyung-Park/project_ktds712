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

def setup_sr_index():
    """SR 인덱스 초기화"""
    print("🚀 Azure AI Search SR 인덱스 초기화 시작\n")
    
    # 데이터 로더 초기화
    loader = DataLoader()
    
    # SR 검색 엔진 초기화
    sr_searcher = SRSearchEngine(loader)
    
    if not sr_searcher.use_azure:
        print("❌ Azure AI Search가 사용 가능하지 않습니다.")
        print("   .env 파일에 AZURE_SEARCH_ENDPOINT와 AZURE_SEARCH_KEY를 설정하세요.")
        return False
    
    print("✅ Azure AI Search 클라이언트 초기화 완료\n")
    
    # 인덱스 초기화 및 데이터 업로드
    print("=" * 60)
    print("📊 인덱스 생성 및 데이터 업로드")
    print("=" * 60)
    
    if sr_searcher.initialize_index():
        print("\n✅ SR 인덱스 초기화 완료!")
        
        # 검색 테스트
        print("\n" + "=" * 60)
        print("🔍 검색 테스트")
        print("=" * 60)
        
        srs = loader.load_sr_data()
        if srs:
            test_sr = srs[0]
            print(f"\n테스트 SR: {test_sr['title']}")
            
            results = sr_searcher.search_similar(test_sr, top_k=3)
            
            print(f"\n유사한 SR 검색 결과 ({len(results)}개):")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result['sr']['title']}")
                print(f"     유사도: {result['similarity_score']:.3f}")
                print(f"     매치 이유: {result['match_reason']}")
        
        return True
    else:
        print("\n❌ 인덱스 초기화 실패")
        return False

if __name__ == "__main__":
    success = setup_sr_index()
    sys.exit(0 if success else 1)


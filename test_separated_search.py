"""
분리된 검색 엔진 테스트
"""
from src.data_loader import DataLoader
from src.search_engine import SearchEngine

def test_separated_search():
    """분리된 검색 엔진 테스트"""
    print("🚀 분리된 검색 엔진 테스트 시작\n")
    
    # 데이터 로더 초기화
    loader = DataLoader()
    
    # 통합 검색 엔진 초기화
    search_engine = SearchEngine(loader)
    
    # SR 데이터 로드
    srs = loader.load_sr_data()
    
    if srs:
        test_sr = srs[0]
        print(f"📋 테스트 SR: {test_sr['title']}\n")
        
        # 1. SR 유사도 검색 (SR 전용 엔진 사용)
        print("=" * 60)
        print("1️⃣ SR 유사도 검색 (SRSearchEngine 사용)")
        print("=" * 60)
        similar_srs = search_engine.search_similar_srs(test_sr, top_k=3)
        
        for i, result in enumerate(similar_srs, 1):
            print(f"\n  {i}. {result['sr']['title']}")
            print(f"     유사도: {result['similarity_score']:.3f}")
            print(f"     매치 이유: {result['match_reason']}")
            if 'match_factors' in result:
                print(f"     매치 요소: {result['match_factors']}")
        
        # 2. 장애 연관도 검색 (Incident 전용 엔진 사용)
        print("\n" + "=" * 60)
        print("2️⃣ 장애 연관도 검색 (IncidentSearchEngine 사용)")
        print("=" * 60)
        related_incidents = search_engine.search_related_incidents(test_sr, top_k=3)
        
        for i, result in enumerate(related_incidents, 1):
            print(f"\n  {i}. {result['incident']['title']}")
            print(f"     연관도: {result['correlation_score']:.3f}")
            print(f"     매치 이유: {result['match_reason']}")
            if 'temporal_relevance' in result:
                print(f"     시간적 관련성: {result['temporal_relevance']}")
            if 'risk_factors' in result:
                print(f"     리스크 요소: 심각도={result['risk_factors']['severity']}")
        
        # 3. 검색 요약
        print("\n" + "=" * 60)
        print("3️⃣ 검색 요약")
        print("=" * 60)
        summary = search_engine.get_search_summary(test_sr)
        print(f"  유사 SR: {summary['similar_srs_count']}개")
        print(f"  관련 장애: {summary['related_incidents_count']}개")
        print(f"  최고 유사도: {summary['top_similarity']:.3f}")
        print(f"  최고 연관도: {summary['top_correlation']:.3f}")
        
        # 4. 직접 접근 가능
        print("\n" + "=" * 60)
        print("4️⃣ 전용 엔진 직접 접근")
        print("=" * 60)
        print(f"  SR 검색 엔진 인덱스: {search_engine.get_sr_searcher().index_name}")
        print(f"  장애 검색 엔진 인덱스: {search_engine.get_incident_searcher().index_name}")
        
        print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_separated_search()


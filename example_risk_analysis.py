#!/usr/bin/env python3
"""
통합 리스크 분석 시스템 사용 예시
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.integrated_risk_analyzer import analyze_development_risk, IntegratedRiskAnalyzer

def test_risk_analysis():
    """리스크 분석 테스트"""
    print("🔍 통합 리스크 분석 시스템 테스트")
    print("=" * 80)
    
    # 테스트 쿼리들
    test_queries = [
        "가입일 기준 월할 계산 기능 개발",
        "위약금 계산 시스템 개선",
        "요금 계산 엔진 최적화",
        "할인 계산 로직 개선",
        "청구서 생성 시스템 업그레이드"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {query}")
        print("-" * 60)
        
        try:
            # 통합 리스크 분석 실행
            result = analyze_development_risk(
                sr_query=query,
                sr_top_k=3,
                incident_top_k=3,
                use_llm=True
            )
            
            print(f"✅ 분석 완료")
            print(f"   - 연관 SR: {result['sr_data']['total_count']}개")
            print(f"   - 유사 장애: {result['incident_data']['total_count']}개")
            
            # 리스크 분석 결과 출력
            if result.get('risk_analysis'):
                analyzer = IntegratedRiskAnalyzer()
                report = analyzer.format_risk_report(
                    result['risk_analysis'],
                    sr_documents=result.get('sr_data', {}).get('documents', []),
                    incident_documents=result.get('incident_data', {}).get('documents', [])
                )
                print(f"\n📋 리스크 분석 결과:")
                print(report)
            else:
                print("⚠️ 리스크 분석 결과가 없습니다.")
            
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()

def interactive_risk_analysis():
    """대화형 리스크 분석"""
    print("💬 대화형 개발 리스크 분석")
    print("=" * 80)
    print("개발 과제를 입력하세요. (종료하려면 'quit' 입력)")
    
    while True:
        try:
            query = input("\n🔍 개발 과제: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료']:
                print("👋 분석을 종료합니다.")
                break
            
            if not query:
                print("⚠️ 개발 과제를 입력해주세요.")
                continue
            
            print(f"\n🔍 '{query}' 리스크 분석 중...")
            
            result = analyze_development_risk(
                sr_query=query,
                sr_top_k=5,
                incident_top_k=5,
                use_llm=True
            )
            
            print(f"\n✅ 분석 완료")
            print(f"   - 연관 SR: {result['sr_data']['total_count']}개")
            print(f"   - 유사 장애: {result['incident_data']['total_count']}개")
            
            # 리스크 분석 결과 출력
            if result.get('risk_analysis'):
                analyzer = IntegratedRiskAnalyzer()
                report = analyzer.format_risk_report(
                    result['risk_analysis'],
                    sr_documents=result.get('sr_data', {}).get('documents', []),
                    incident_documents=result.get('incident_data', {}).get('documents', [])
                )
                print(f"\n📋 리스크 분석 결과:")
                print(report)
            else:
                print("⚠️ 리스크 분석 결과가 없습니다.")
            
        except KeyboardInterrupt:
            print("\n\n👋 분석을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 분석 중 오류 발생: {e}")

def quick_risk_check():
    """빠른 리스크 체크"""
    print("⚡ 빠른 리스크 체크")
    print("=" * 80)
    
    query = input("🔍 개발 과제를 입력하세요: ").strip()
    
    if not query:
        print("⚠️ 개발 과제를 입력해주세요.")
        return
    
    try:
        print(f"\n🔍 '{query}' 빠른 리스크 체크 중...")
        
        result = analyze_development_risk(
            sr_query=query,
            sr_top_k=3,
            incident_top_k=3,
            use_llm=True
        )
        
        print(f"\n✅ 체크 완료")
        print(f"   - 연관 SR: {result['sr_data']['total_count']}개")
        print(f"   - 유사 장애: {result['incident_data']['total_count']}개")
        
        # 요약 정보만 출력
        if result.get('risk_analysis') and 'summary' in result['risk_analysis']:
            summary = result['risk_analysis']['summary']
            print(f"\n📊 위험도 요약:")
            print(f"   - 전체 위험도: {summary.get('overall_risk_score', 'N/A')}/10")
            print(f"   - 고위험 요소: {summary.get('high_risk_count', 'N/A')}개")
            print(f"   - 중위험 요소: {summary.get('medium_risk_count', 'N/A')}개")
            print(f"   - 저위험 요소: {summary.get('low_risk_count', 'N/A')}개")
        else:
            print("⚠️ 위험도 분석 결과가 없습니다.")
        
    except Exception as e:
        print(f"❌ 체크 실패: {e}")

if __name__ == "__main__":
    print("🔍 통합 리스크 분석 시스템")
    print("=" * 80)
    print("1. 전체 테스트 실행")
    print("2. 대화형 리스크 분석")
    print("3. 빠른 리스크 체크")
    
    try:
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == "1":
            test_risk_analysis()
        elif choice == "2":
            interactive_risk_analysis()
        elif choice == "3":
            quick_risk_check()
        else:
            print("❌ 잘못된 선택입니다. 전체 테스트를 실행합니다.")
            test_risk_analysis()
            
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

"""
SR Impact Navigator 데모 실행 스크립트
사전 정의된 시나리오들을 자동으로 실행하여 데모 진행
"""
import streamlit as st
import time
import json
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.integrated_risk_analyzer import analyze_development_risk

# 데모 시나리오 데이터
DEMO_SCENARIOS = {
    "scenario_1": {
        "title": "신규 결제 시스템 개발",
        "description": "실시간 결제 처리 및 다중 결제 수단 지원",
        "detailed_content": """기존 결제 시스템의 성능 문제와 다중 결제 수단 지원 부족을 해결하기 위해 
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
- Monitoring: Prometheus + Grafana""",
        "sr_top_k": 8,
        "incident_top_k": 6,
        "expected_risks": 12,
        "expected_high_risks": 3
    },
    "scenario_2": {
        "title": "모바일 앱 리뉴얼",
        "description": "사용자 경험 개선 및 신규 기능 추가",
        "detailed_content": """기존 모바일 앱의 사용자 불만사항을 해결하고 새로운 기능을 추가하여 
사용자 경험을 대폭 개선하는 프로젝트입니다.

주요 요구사항:
1. 직관적인 UI/UX 디자인
2. 실시간 알림 시스템
3. 생체인증 (지문, 얼굴인식) 지원
4. 다크모드 지원
5. 오프라인 기능 (기본 기능)
6. 접근성 개선 (스크린 리더 지원)

기술 스택:
- Frontend: React Native
- Backend: Node.js + Express
- Database: MongoDB
- Push Notification: Firebase
- Biometric: React Native Biometrics""",
        "sr_top_k": 5,
        "incident_top_k": 4,
        "expected_risks": 8,
        "expected_high_risks": 2
    },
    "scenario_3": {
        "title": "마이크로서비스 아키텍처 전환",
        "description": "확장성 및 유지보수성 향상",
        "detailed_content": """기존 모놀리식 아키텍처를 마이크로서비스로 전환하여 
확장성과 유지보수성을 크게 향상시키는 대규모 리팩토링 프로젝트입니다.

주요 요구사항:
1. 도메인별 서비스 분리 (사용자, 상품, 주문, 결제, 배송)
2. API Gateway 구현
3. 서비스 간 통신 (REST, Message Queue)
4. 분산 트랜잭션 처리
5. 서비스 디스커버리
6. 중앙화된 로깅 및 모니터링

기술 스택:
- Backend: Spring Boot, Node.js
- API Gateway: Kong, Zuul
- Message Queue: Apache Kafka, RabbitMQ
- Database: PostgreSQL, MongoDB
- Container: Docker, Kubernetes
- Monitoring: ELK Stack, Prometheus""",
        "sr_top_k": 10,
        "incident_top_k": 8,
        "expected_risks": 15,
        "expected_high_risks": 4
    }
}

def run_demo_scenario(scenario_key: str):
    """데모 시나리오 실행"""
    scenario = DEMO_SCENARIOS[scenario_key]
    
    st.markdown(f"## 🎯 시나리오: {scenario['title']}")
    st.markdown(f"**{scenario['description']}**")
    
    # 개발 과제 통합
    development_task = f"{scenario['title']}\n\n{scenario['detailed_content']}"
    
    # 분석 실행
    with st.spinner("🔍 개발 리스크 분석 중... 잠시만 기다려주세요."):
        try:
            result = analyze_development_risk(
                development_task=development_task,
                sr_top_k=scenario['sr_top_k'],
                incident_top_k=scenario['incident_top_k'],
                use_llm=True
            )
            
            # 결과 저장
            st.session_state['demo_result'] = result
            st.session_state['demo_scenario'] = scenario_key
            st.session_state['analysis_completed'] = True
            
            return result
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
            return None

def display_demo_results(result, scenario_key):
    """데모 결과 표시"""
    scenario = DEMO_SCENARIOS[scenario_key]
    
    st.markdown("## 📊 분석 결과")
    
    # 위험도 요약 카드
    risk_analysis = result.get('risk_analysis', {})
    summary = risk_analysis.get('summary', {})
    
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="전체 위험 요소",
                value=f"{summary.get('total_risks', 'N/A')}개",
                help="발견된 총 위험 요소의 개수"
            )
        
        with col2:
            st.metric(
                label="고위험 요소",
                value=f"{summary.get('high_risk_count', 'N/A')}개",
                help="RPN > 100인 고위험 요소"
            )
        
        with col3:
            st.metric(
                label="중위험 요소",
                value=f"{summary.get('medium_risk_count', 'N/A')}개",
                help="RPN 50-100인 중위험 요소"
            )
        
        with col4:
            overall_score = summary.get('overall_risk_score', 0)
            risk_level = "높음" if overall_score >= 7 else "보통" if overall_score >= 4 else "낮음"
            st.metric(
                label="전체 위험도",
                value=f"{overall_score}/10",
                delta=risk_level,
                help="전체 위험도 점수 (0-10)"
            )
    
    # 예상 결과와 비교
    st.markdown("### 📈 예상 결과 대비")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**예상 위험 요소**: {scenario['expected_risks']}개")
        st.info(f"**예상 고위험 요소**: {scenario['expected_high_risks']}개")
    
    with col2:
        actual_risks = summary.get('total_risks', 0)
        actual_high_risks = summary.get('high_risk_count', 0)
        
        if actual_risks > 0:
            risk_accuracy = min(100, (actual_risks / scenario['expected_risks']) * 100)
            st.success(f"**위험 요소 정확도**: {risk_accuracy:.1f}%")
        
        if actual_high_risks > 0:
            high_risk_accuracy = min(100, (actual_high_risks / scenario['expected_high_risks']) * 100)
            st.success(f"**고위험 요소 정확도**: {high_risk_accuracy:.1f}%")

def main():
    """메인 데모 함수"""
    st.set_page_config(
        page_title="SR Impact Navigator - 데모",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 메인 헤더
    st.markdown('<h1 class="main-header">🎯 SR Impact Navigator - 데모</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #7f8c8d;">AI 기반 개발 리스크 분석 시스템</h2>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.markdown("## 🎭 데모 시나리오 선택")
        
        scenario_choice = st.selectbox(
            "시나리오를 선택하세요:",
            options=list(DEMO_SCENARIOS.keys()),
            format_func=lambda x: DEMO_SCENARIOS[x]['title']
        )
        
        st.markdown("---")
        st.markdown("### 📋 선택된 시나리오")
        if scenario_choice:
            scenario = DEMO_SCENARIOS[scenario_choice]
            st.write(f"**제목**: {scenario['title']}")
            st.write(f"**설명**: {scenario['description']}")
            st.write(f"**SR 검색 수**: {scenario['sr_top_k']}개")
            st.write(f"**장애 검색 수**: {scenario['incident_top_k']}개")
        
        st.markdown("---")
        st.markdown("### 🚀 데모 실행")
        
        if st.button("▶️ 시나리오 실행", type="primary", use_container_width=True):
            st.session_state['run_demo'] = True
            st.session_state['selected_scenario'] = scenario_choice
        
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # 메인 컨텐츠
    if st.session_state.get('run_demo', False) and 'selected_scenario' in st.session_state:
        scenario_key = st.session_state['selected_scenario']
        
        # 시나리오 실행
        result = run_demo_scenario(scenario_key)
        
        if result:
            # 결과 표시
            display_demo_results(result, scenario_key)
            
            # 상세 결과 표시 (기존 함수 활용)
            from app_streamlit import display_reference_summary, display_risk_factors, display_guidelines_and_recommendations
            
            display_reference_summary(result)
            display_risk_factors(result.get('risk_analysis', {}))
            display_guidelines_and_recommendations(result.get('risk_analysis', {}))
            
            # 데모 완료 메시지
            st.success("🎉 데모 시나리오가 성공적으로 완료되었습니다!")
            
            # 다음 단계 안내
            st.markdown("### 📝 다음 단계")
            st.info("""
            **실제 프로젝트에 적용하려면:**
            1. 개발 요구사항을 직접 입력하세요
            2. 분석 설정을 조정하세요
            3. 결과를 바탕으로 프로젝트 계획을 수립하세요
            """)
    
    else:
        # 데모 소개
        st.markdown("## 🎯 데모 소개")
        
        st.markdown("""
        **SR Impact Navigator**는 개발 요구사항을 입력받아 연관 SR과 유사 장애를 검색하고, 
        FMEA 기반으로 체계적인 위험도 분석을 수행하는 AI 기반 시스템입니다.
        
        ### 🚀 데모 시나리오
        """)
        
        # 시나리오 목록 표시
        for key, scenario in DEMO_SCENARIOS.items():
            with st.expander(f"📋 {scenario['title']}", expanded=False):
                st.write(f"**설명**: {scenario['description']}")
                st.write(f"**예상 위험 요소**: {scenario['expected_risks']}개")
                st.write(f"**예상 고위험 요소**: {scenario['expected_high_risks']}개")
                st.write(f"**SR 검색 수**: {scenario['sr_top_k']}개")
                st.write(f"**장애 검색 수**: {scenario['incident_top_k']}개")
        
        st.markdown("""
        ### 🎭 데모 실행 방법
        1. 왼쪽 사이드바에서 시나리오를 선택하세요
        2. "▶️ 시나리오 실행" 버튼을 클릭하세요
        3. AI가 자동으로 리스크 분석을 수행합니다
        4. 결과를 확인하고 실제 프로젝트에 적용해보세요
        """)

if __name__ == "__main__":
    main()

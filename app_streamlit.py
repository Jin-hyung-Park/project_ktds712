import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any
import time

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.integrated_risk_analyzer import analyze_development_risk, IntegratedRiskAnalyzer

# 페이지 설정
st.set_page_config(
    page_title="SR Impact Navigator - 개발 리스크 분석",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 4px solid #d32f2f;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(244, 67, 54, 0.1);
    }
    .risk-high h4 {
        color: #d32f2f;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .risk-high p {
        color: #424242;
        margin: 0.3rem 0;
    }
    .risk-medium {
        background-color: #fff8e1;
        border-left: 4px solid #f57c00;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(255, 152, 0, 0.1);
    }
    .risk-medium h4 {
        color: #f57c00;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .risk-medium p {
        color: #424242;
        margin: 0.3rem 0;
    }
    .risk-low {
        background-color: #e8f5e8;
        border-left: 4px solid #388e3c;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(76, 175, 80, 0.1);
    }
    .risk-low h4 {
        color: #388e3c;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .risk-low p {
        color: #424242;
        margin: 0.3rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 메인 헤더
    st.markdown('<h1 class="main-header">🔍 SR Impact Navigator</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #7f8c8d;">개발 리스크 분석 시스템</h2>', unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("## ⚙️ 분석 설정")
        
        sr_top_k = st.slider("연관 SR 검색 수", min_value=1, max_value=10, value=5, help="검색할 연관 SR의 최대 개수")
        incident_top_k = st.slider("유사 장애 검색 수", min_value=1, max_value=10, value=5, help="검색할 유사 장애의 최대 개수")
        
        st.markdown("---")
        st.markdown("### 📊 시스템 정보")
        st.info("이 시스템은 FMEA 기반으로 개발 과제의 위험도를 분석합니다.")
        
        if st.button("🔄 새로고침"):
            st.rerun()
    
    # 메인 컨텐츠
    st.markdown('<div class="section-header">📝 개발 요구사항 입력</div>', unsafe_allow_html=True)
    
    # 입력 폼
    with st.form("development_requirements_form"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 목적")
            title = st.text_input(
                "개발요청 목적",
                placeholder="예: 가입일 기준 월할 계산 기능 개발",
                help="분석할 개발 과제의 제목을 입력하세요"
            )
        
        with col2:
            st.markdown("###요청 상세 내용")
            description = st.text_area(
                "요청 상세 내용",
                placeholder="개발하고자 하는 기능의 상세한 내용을 입력하세요...",
                height=150,
                help="개발 과제의 구체적인 내용, 요구사항, 목표 등을 자세히 입력하세요"
            )
        
        # 분석 버튼
        analyze_button = st.form_submit_button(
            "🔍 리스크 분석 시작",
            type="primary",
            use_container_width=True
        )
    
    # 분석 실행
    if analyze_button:
        if not title.strip() or not description.strip():
            st.error("⚠️ 제목과 내용을 모두 입력해주세요.")
        else:
            # 분석 실행
            with st.spinner("🔍 개발 리스크 분석 중... 잠시만 기다려주세요."):
                try:
                    # 개발 과제 통합
                    development_task = f"{title}\n\n{description}"
                    
                    # 리스크 분석 실행
                    result = analyze_development_risk(
                        development_task=development_task,
                        sr_top_k=sr_top_k,
                        incident_top_k=incident_top_k,
                        use_llm=True
                    )
                    
                    # 분석 결과 저장
                    st.session_state['analysis_result'] = result
                    st.session_state['analysis_completed'] = True
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                    st.session_state['analysis_completed'] = False
    
    # 분석 결과 표시
    if st.session_state.get('analysis_completed', False) and 'analysis_result' in st.session_state:
        display_analysis_results(st.session_state['analysis_result'])

def display_analysis_results(result: Dict[str, Any]):
    """분석 결과를 표시하는 함수"""
    
    st.markdown('<div class="section-header">📊 분석 결과</div>', unsafe_allow_html=True)
    
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
    
    # 참조 정보 요약
    display_reference_summary(result)
    
    # 위험 요소 상세 분석
    display_risk_factors(risk_analysis)
    
    # 개발 가이드라인 및 모니터링 권장사항
    display_guidelines_and_recommendations(risk_analysis)

def display_reference_summary(result: Dict[str, Any]):
    """참조 SR 및 장애 정보 요약 표시"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 참조 SR 정보")
        sr_documents = result.get('sr_data', {}).get('documents', [])
        
        if sr_documents:
            for i, doc in enumerate(sr_documents[:3], 1):
                with st.expander(f"SR {i}: {doc.get('id', 'N/A')} - {doc.get('title', 'N/A')}"):
                    st.write(f"**시스템:** {doc.get('system', 'N/A')}")
                    st.write(f"**우선순위:** {doc.get('priority', 'N/A')}")
                    st.write(f"**카테고리:** {doc.get('category', 'N/A')}")
                    
                    desc = str(doc.get('description', '')).strip()
                    if desc:
                        st.write(f"**설명:** {desc[:200]}{'...' if len(desc) > 200 else ''}")
                    
                    tech_reqs = doc.get('technical_requirements', [])
                    if tech_reqs:
                        st.write("**기술요구사항:**")
                        for req in tech_reqs[:3]:
                            st.write(f"- {req}")
        else:
            st.info("참조할 수 있는 SR이 없습니다.")
    
    with col2:
        st.markdown("### 🚨 참조 장애 정보")
        incident_documents = result.get('incident_data', {}).get('documents', [])
        
        if incident_documents:
            for i, doc in enumerate(incident_documents[:3], 1):
                with st.expander(f"장애 {i}: {doc.get('title', 'N/A')}"):
                    chunk = str(doc.get('chunk', ''))
                    
                    # 장애 설명 추출
                    import re
                    desc_match = re.search(r'장애 설명\s*\n([\s\S]*?)(\n\n|\n\s*근본 원인|\n\s*해결 방법|$)', chunk)
                    if desc_match:
                        desc = desc_match.group(1).strip()
                        st.write(f"**장애 설명:** {desc[:200]}{'...' if len(desc) > 200 else ''}")
                    
                    # 근본 원인 추출
                    cause_match = re.search(r'근본 원인\s*\n([\s\S]*?)(\n\n|\n\s*해결 방법|\n\s*영향|$)', chunk)
                    if cause_match:
                        cause = cause_match.group(1).strip()
                        st.write(f"**근본 원인:** {cause[:200]}{'...' if len(cause) > 200 else ''}")
                    
                    # 해결 방법 추출
                    fix_match = re.search(r'해결 방법\s*\n([\s\S]*?)(\n\n|\n\s*영향|\n\s*비즈니스|$)', chunk)
                    if fix_match:
                        fix = fix_match.group(1).strip()
                        st.write(f"**해결 방법:** {fix[:200]}{'...' if len(fix) > 200 else ''}")
        else:
            st.info("참조할 수 있는 장애가 없습니다.")

def display_risk_factors(risk_analysis: Dict[str, Any]):
    """위험 요소 상세 분석 표시"""
    
    st.markdown("### ⚠️ 주요 위험 요소")
    
    risk_factors = risk_analysis.get('risk_factors', [])
    
    if not risk_factors:
        st.info("분석된 위험 요소가 없습니다.")
        return
    
    for factor in risk_factors:
        rpn = factor.get('rpn', 0)
        risk_level = factor.get('risk_level', 'Unknown')
        
        # 위험도에 따른 스타일 클래스 결정
        if rpn > 100:
            style_class = "risk-high"
            icon = "🔴"
        elif rpn > 50:
            style_class = "risk-medium"
            icon = "🟡"
        else:
            style_class = "risk-low"
            icon = "🟢"
        
        with st.container():
            st.markdown(f"""
            <div class="{style_class}">
                <h4>{icon} {factor.get('id', 'N/A')}. {factor.get('failure_mode', 'N/A')}</h4>
                <p><strong>🔍 원인:</strong> {factor.get('failure_cause', 'N/A')}</p>
                <p><strong>⚡ 영향:</strong> {factor.get('failure_effect', 'N/A')}</p>
                <p><strong>📊 RPN:</strong> <span style="font-weight: bold; color: #1976d2;">{rpn}</span> (발생:{factor.get('occurrence', 'N/A')} × 심각도:{factor.get('severity', 'N/A')} × 탐지:{factor.get('detection', 'N/A')})</p>
                <p><strong>⚠️ 위험도:</strong> <span style="font-weight: bold;">{risk_level}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # 완화 방안
            mitigation_measures = factor.get('mitigation_measures', [])
            if mitigation_measures:
                with st.expander("🛠️ 완화 방안 보기", expanded=False):
                    st.markdown("**권장 조치사항:**")
                    for i, measure in enumerate(mitigation_measures, 1):
                        st.markdown(f"**{i}.** {measure}")

def display_guidelines_and_recommendations(risk_analysis: Dict[str, Any]):
    """개발 가이드라인 및 모니터링 권장사항 표시"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 개발 가이드라인")
        guidelines = risk_analysis.get('development_guidelines', [])
        
        if guidelines:
            for i, guideline in enumerate(guidelines, 1):
                st.write(f"{i}. {guideline}")
        else:
            st.info("제공된 개발 가이드라인이 없습니다.")
    
    with col2:
        st.markdown("### 🔍 모니터링 권장사항")
        recommendations = risk_analysis.get('monitoring_recommendations', [])
        
        if recommendations:
            for i, recommendation in enumerate(recommendations, 1):
                st.write(f"{i}. {recommendation}")
        else:
            st.info("제공된 모니터링 권장사항이 없습니다.")

if __name__ == "__main__":
    main()

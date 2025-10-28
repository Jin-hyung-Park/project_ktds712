"""
SR Impact Navigator+ Streamlit 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import DataLoader
from src.risk_calculator import RiskCalculator
from src.search_engine import SearchEngine
from src.ai_risk_evaluator import AIRiskEvaluator

# 페이지 설정
st.set_page_config(
    page_title="SR Impact Navigator+",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-critical { color: #d62728; }
    .risk-high { color: #ff7f0e; }
    .risk-medium { color: #ffbb78; }
    .risk-low { color: #2ca02c; }
    .risk-minimal { color: #7f7f7f; }
</style>
""", unsafe_allow_html=True)

def initialize_components():
    """컴포넌트 초기화"""
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = DataLoader()
    if 'risk_calculator' not in st.session_state:
        st.session_state.risk_calculator = RiskCalculator(st.session_state.data_loader)
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = SearchEngine(st.session_state.data_loader)
    if 'ai_evaluator' not in st.session_state:
        st.session_state.ai_evaluator = AIRiskEvaluator(
            st.session_state.data_loader,
            st.session_state.search_engine
        )

def display_header():
    """헤더 표시"""
    st.markdown('<h1 class="main-header">🚀 SR Impact Navigator+</h1>', unsafe_allow_html=True)
    st.markdown("**SR 변경 영향도 및 장애연관 리스크 기반 과제 평가 AI**")
    st.markdown("---")

def display_overview():
    """개요 섹션"""
    st.subheader("📊 시스템 개요")
    
    # 데이터 요약
    summary = st.session_state.data_loader.get_data_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 SR 개수", summary['total_srs'])
    
    with col2:
        st.metric("총 장애 개수", summary['total_incidents'])
    
    with col3:
        st.metric("관련 시스템", len(summary['systems']))
    
    with col4:
        st.metric("최근 30일 장애", summary['recent_incidents'])

def display_sr_analysis():
    """SR 분석 섹션"""
    st.subheader("🔍 SR 리스크 분석")
    
    # SR 선택
    srs = st.session_state.data_loader.load_sr_data()
    sr_options = {f"{sr['id']}: {sr['title']}": sr for sr in srs}
    
    selected_sr_key = st.selectbox(
        "분석할 SR을 선택하세요:",
        options=list(sr_options.keys()),
        index=0
    )
    
    if selected_sr_key:
        selected_sr = sr_options[selected_sr_key]
        
        # SR 기본 정보
        with st.expander("📋 SR 기본 정보", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {selected_sr['id']}")
                st.write(f"**시스템:** {selected_sr['system']}")
                st.write(f"**우선순위:** {selected_sr['priority']}")
                st.write(f"**카테고리:** {selected_sr['category']}")
            
            with col2:
                st.write(f"**요청자:** {selected_sr['requester']}")
                st.write(f"**생성일:** {selected_sr['created_date']}")
                st.write(f"**목표일:** {selected_sr['target_date']}")
            
            st.write(f"**설명:** {selected_sr['description']}")
            st.write(f"**비즈니스 임팩트:** {selected_sr['business_impact']}")
        
        # 평가 방법 선택
        col1, col2 = st.columns([2, 1])
        with col1:
            use_openai = st.checkbox(
                "🤖 OpenAI 기반 AI 평가 사용",
                value=st.session_state.ai_evaluator.openai_available,
                disabled=not st.session_state.ai_evaluator.openai_available,
                help="OpenAI를 사용하여 맥락을 고려한 리스크 평가를 수행합니다. (설정되지 않은 경우 규칙 기반 평가 사용)"
            )
        with col2:
            if not st.session_state.ai_evaluator.openai_available:
                st.warning("⚠️ OpenAI 설정 필요")
        
        # 리스크 분석 실행
        if st.button("🚀 리스크 분석 실행", type="primary"):
            with st.spinner("리스크 분석 중..."):
                if use_openai and st.session_state.ai_evaluator.openai_available:
                    # OpenAI 기반 평가
                    ai_result = st.session_state.ai_evaluator.evaluate_risk(selected_sr, use_openai=True)
                    
                    # 검색 결과는 이미 ai_result에 포함됨
                    search_result = {
                        'similar_srs': ai_result.get('similar_srs', []),
                        'related_incidents': ai_result.get('related_incidents', []),
                        'similar_srs_count': len(ai_result.get('similar_srs', [])),
                        'related_incidents_count': len(ai_result.get('related_incidents', []))
                    }
                    
                    # 결과 표시 (AI 결과 형식)
                    display_ai_risk_results(ai_result, search_result)
                else:
                    # 규칙 기반 평가
                    risk_result = st.session_state.risk_calculator.calculate_risk_score(selected_sr)
                    search_result = st.session_state.search_engine.get_search_summary(selected_sr)
                    display_risk_results(risk_result, search_result)

def display_ai_risk_results(ai_result, search_result):
    """OpenAI 기반 리스크 분석 결과 표시"""
    st.subheader("📈 AI 기반 리스크 분석 결과")
    
    # 평가 방법 표시
    eval_method = ai_result.get('evaluation_method', 'unknown')
    method_badge = "🤖 AI" if eval_method == 'openai' else "📊 규칙 기반"
    st.info(f"**평가 방법:** {method_badge} ({eval_method})")
    
    # 리스크 점수 및 등급
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_score = ai_result['total_score']
        risk_level = ai_result['risk_level']
        risk_colors = {
            'Critical': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Minimal': '⚪'
        }
        risk_color = risk_colors.get(risk_level, '⚪')
        
        st.metric(
            "리스크 점수", 
            f"{risk_score:.3f}",
            delta=f"{risk_color} {risk_level}"
        )
    
    with col2:
        st.metric("유사 SR", f"{search_result['similar_srs_count']}개")
    
    with col3:
        st.metric("관련 장애", f"{search_result['related_incidents_count']}개")
    
    # AI 추론 설명
    if 'reasoning' in ai_result:
        st.subheader("🧠 AI 평가 근거")
        st.write(ai_result['reasoning'])
    
    # 주요 리스크
    if 'key_risks' in ai_result and ai_result['key_risks']:
        st.subheader("⚠️ 주요 리스크 요소")
        for risk in ai_result['key_risks']:
            st.write(f"- {risk}")
    
    # 리스크 구성 요소 차트
    st.subheader("📊 리스크 구성 요소 분석")
    
    components = ai_result.get('components', {})
    
    # 레이더 차트
    if components:
        categories = list(components.keys())
        values = list(components.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='현재 SR',
            line_color='rgb(31, 119, 180)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="리스크 구성 요소 분석"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 구성 요소별 상세 점수
        st.subheader("📋 구성 요소별 상세 점수")
        
        weights = {
            "sr_similarity": 0.25,
            "incident_correlation": 0.25,
            "system_importance": 0.25,
            "time_sensitivity": 0.15,
            "sr_complexity": 0.10
        }
        
        component_df = pd.DataFrame([
            {
                '구성 요소': comp,
                '점수': score,
                '가중치': weights.get(comp, 0.0),
                '가중 점수': score * weights.get(comp, 0.0)
            }
            for comp, score in components.items()
        ])
        
        st.dataframe(component_df, use_container_width=True)
    
    # 유사 SR 목록
    if search_result.get('similar_srs'):
        st.subheader("🔗 유사한 SR")
        
        similar_data = []
        for result in search_result['similar_srs']:
            sr_data = result.get('sr', {})
            similar_data.append({
                'ID': sr_data.get('id', ''),
                '제목': sr_data.get('title', ''),
                '유사도': f"{result.get('similarity_score', 0):.3f}",
                '매치 이유': result.get('match_reason', '')
            })
        
        similar_df = pd.DataFrame(similar_data)
        st.dataframe(similar_df, use_container_width=True)
    
    # 관련 장애 목록
    if search_result.get('related_incidents'):
        st.subheader("⚠️ 관련 장애")
        
        incident_data = []
        for result in search_result['related_incidents']:
            incident = result.get('incident', {})
            incident_data.append({
                'ID': incident.get('id', ''),
                '제목': incident.get('title', ''),
                '연관도': f"{result.get('correlation_score', 0):.3f}",
                '심각도': incident.get('severity', ''),
                '매치 이유': result.get('match_reason', '')
            })
        
        incident_df = pd.DataFrame(incident_data)
        st.dataframe(incident_df, use_container_width=True)
    
    # 권장사항
    st.subheader("💡 AI 권장사항")
    recommendations = ai_result.get('recommendations', [])
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    else:
        st.write("권장사항이 없습니다.")

def display_risk_results(risk_result, search_result):
    """리스크 분석 결과 표시"""
    st.subheader("📈 리스크 분석 결과")
    
    # 리스크 점수 및 등급
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_score = risk_result['total_score']
        risk_level = risk_result['risk_level']
        risk_color = st.session_state.risk_calculator.get_risk_color(risk_level)
        
        st.metric(
            "리스크 점수", 
            f"{risk_score:.3f}",
            delta=f"{risk_color} {risk_level}"
        )
    
    with col2:
        st.metric("유사 SR", f"{search_result['similar_srs_count']}개")
    
    with col3:
        st.metric("관련 장애", f"{search_result['related_incidents_count']}개")
    
    # 리스크 구성 요소 차트
    st.subheader("📊 리스크 구성 요소 분석")
    
    components = risk_result['components']
    weights = risk_result['weights']
    
    # 레이더 차트
    categories = list(components.keys())
    values = list(components.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='현재 SR',
        line_color='rgb(31, 119, 180)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="리스크 구성 요소 분석"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 구성 요소별 상세 점수
    st.subheader("📋 구성 요소별 상세 점수")
    
    component_df = pd.DataFrame([
        {
            '구성 요소': comp,
            '점수': score,
            '가중치': weights[comp],
            '가중 점수': score * weights[comp]
        }
        for comp, score in components.items()
    ])
    
    st.dataframe(component_df, use_container_width=True)
    
    # 유사 SR 목록
    if search_result['similar_srs']:
        st.subheader("🔗 유사한 SR")
        
        similar_data = []
        for result in search_result['similar_srs']:
            similar_data.append({
                'ID': result['sr']['id'],
                '제목': result['sr']['title'],
                '유사도': f"{result['similarity_score']:.3f}",
                '매치 이유': result['match_reason']
            })
        
        similar_df = pd.DataFrame(similar_data)
        st.dataframe(similar_df, use_container_width=True)
    
    # 관련 장애 목록
    if search_result['related_incidents']:
        st.subheader("⚠️ 관련 장애")
        
        incident_data = []
        for result in search_result['related_incidents']:
            incident = result['incident']
            incident_data.append({
                'ID': incident['id'],
                '제목': incident['title'],
                '연관도': f"{result['correlation_score']:.3f}",
                '심각도': incident['severity'],
                '매치 이유': result['match_reason']
            })
        
        incident_df = pd.DataFrame(incident_data)
        st.dataframe(incident_df, use_container_width=True)
    
    # 권장사항
    st.subheader("💡 권장사항")
    recommendations = st.session_state.risk_calculator.get_risk_recommendations(risk_result)
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")

def display_sr_list():
    """SR 목록 섹션"""
    st.subheader("📋 전체 SR 목록")
    
    srs = st.session_state.data_loader.load_sr_data()
    
    # SR 목록을 DataFrame으로 변환
    sr_data = []
    for sr in srs:
        # 각 SR의 리스크 점수 계산
        risk_result = st.session_state.risk_calculator.calculate_risk_score(sr)
        
        sr_data.append({
            'ID': sr['id'],
            '제목': sr['title'],
            '시스템': sr['system'],
            '우선순위': sr['priority'],
            '카테고리': sr['category'],
            '리스크 점수': f"{risk_result['total_score']:.3f}",
            '리스크 등급': risk_result['risk_level']
        })
    
    sr_df = pd.DataFrame(sr_data)
    
    # 리스크 등급별 색상 적용
    def color_risk_level(val):
        colors = {
            'Critical': 'background-color: #ffebee',
            'High': 'background-color: #fff3e0',
            'Medium': 'background-color: #fffde7',
            'Low': 'background-color: #e8f5e8',
            'Minimal': 'background-color: #f5f5f5'
        }
        return colors.get(val, '')
    
    styled_df = sr_df.style.applymap(color_risk_level, subset=['리스크 등급'])
    st.dataframe(styled_df, use_container_width=True)

def main():
    """메인 함수"""
    # 컴포넌트 초기화
    initialize_components()
    
    # 헤더 표시
    display_header()
    
    # 사이드바
    with st.sidebar:
        st.title("🎛️ 메뉴")
        
        page = st.radio(
            "페이지 선택:",
            ["개요", "SR 분석", "SR 목록"]
        )
    
    # 페이지별 내용 표시
    if page == "개요":
        display_overview()
        
        # 추가 통계 차트
        st.subheader("📈 시스템별 SR 분포")
        srs = st.session_state.data_loader.load_sr_data()
        
        if srs:
            system_counts = {}
            for sr in srs:
                system = sr.get('system', 'Unknown')
                system_counts[system] = system_counts.get(system, 0) + 1
            
            fig = px.pie(
                values=list(system_counts.values()),
                names=list(system_counts.keys()),
                title="시스템별 SR 분포"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif page == "SR 분석":
        display_sr_analysis()
    
    elif page == "SR 목록":
        display_sr_list()
    
    # 푸터
    st.markdown("---")
    st.markdown(
        "**SR Impact Navigator+** | FMEA 기반 리스크 평가 AI | "
        "Azure AI Search + OpenAI + Streamlit"
    )

if __name__ == "__main__":
    main()

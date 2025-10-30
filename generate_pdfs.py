"""
SR 및 장애 데이터를 PDF 파일로 생성하는 스크립트
한글 폰트 지원 포함
"""
import json
import html
from datetime import datetime
from pathlib import Path
import sys

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ reportlab이 설치되지 않았습니다. pip install reportlab을 실행하세요.")


# 한글 폰트 등록 함수
def register_korean_fonts():
    """한글 폰트 등록 (macOS)"""
    if not REPORTLAB_AVAILABLE:
        return
    
    try:
        # macOS 기본 한글 폰트 등록 (우선순위 순)
        # TTC 파일은 여러 폰트를 포함하므로 인덱스를 통해 선택
        font_candidates = [
            # (경로, 일반폰트 인덱스, 볼드폰트 인덱스)
            ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 0, 1),  # Apple SD Gothic Neo (일반, 볼드)
            ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", None, None),  # AppleGothic
            ("/Library/Fonts/AppleGothic.ttf", None, None),  # 대체 경로
        ]
        
        font_registered = False
        for font_info in font_candidates:
            font_path = font_info[0]
            normal_idx = font_info[1] if len(font_info) > 1 else None
            bold_idx = font_info[2] if len(font_info) > 2 else None
            
            if not Path(font_path).exists():
                continue
            
            try:
                # 일반 폰트 등록
                if font_path.endswith('.ttc') and normal_idx is not None:
                    pdfmetrics.registerFont(TTFont('KoreanFont', font_path, subfontIndex=normal_idx))
                else:
                    pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
                
                # 볼드 폰트 등록
                if font_path.endswith('.ttc') and bold_idx is not None:
                    try:
                        pdfmetrics.registerFont(TTFont('KoreanFont-Bold', font_path, subfontIndex=bold_idx))
                    except:
                        # 볼드 인덱스가 없으면 일반 폰트 사용
                        pdfmetrics.registerFont(TTFont('KoreanFont-Bold', font_path, subfontIndex=normal_idx))
                else:
                    # TTF 파일인 경우 같은 폰트를 볼드로도 등록
                    try:
                        pdfmetrics.registerFont(TTFont('KoreanFont-Bold', font_path))
                    except:
                        pdfmetrics.registerFont(TTFont('KoreanFont-Bold', font_path))
                
                font_registered = True
                print(f"✅ 한글 폰트 등록 완료: {Path(font_path).name}")
                break
            except Exception as e:
                # 다음 폰트 시도
                continue
        
        if not font_registered:
            print("⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            return False
        
        return True
    except Exception as e:
        print(f"⚠️ 한글 폰트 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def escape_html(text):
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return html.escape(str(text))


def format_date(date_str):
    """날짜 포맷팅"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%Y년 %m월 %d일')
    except:
        return date_str


def create_sr_pdf(sr_data, output_dir):
    """SR 데이터를 PDF로 생성"""
    if not REPORTLAB_AVAILABLE:
        print(f"⚠️ reportlab이 없어 PDF를 생성할 수 없습니다: {sr_data['id']}")
        return False
    
    output_path = Path(output_dir) / f"SR_{sr_data['id']}.pdf"
    
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # 한글 폰트 사용 스타일 생성
    korean_font_name = 'KoreanFont' if 'KoreanFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    korean_bold_name = 'KoreanFont-Bold' if 'KoreanFont-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
    
    # 타이틀 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=korean_bold_name,
        fontSize=18,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=1  # 중앙 정렬
    )
    
    # 한글 지원 스타일
    heading_style = ParagraphStyle(
        'KoreanHeading',
        parent=styles['Heading2'],
        fontName=korean_bold_name,
        fontSize=14,
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'KoreanNormal',
        parent=styles['Normal'],
        fontName=korean_font_name,
        fontSize=11,
        leading=16
    )
    
    # 제목 추가
    title_text = escape_html(f"SR 문서: {sr_data['id']}")
    title = Paragraph(f"<b>{title_text}</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # 기본 정보 테이블
    basic_info = [
        ['SR ID', escape_html(sr_data.get('id', ''))],
        ['제목', escape_html(sr_data.get('title', ''))],
        ['시스템', escape_html(sr_data.get('system', ''))],
        ['우선순위', escape_html(sr_data.get('priority', ''))],
        ['카테고리', escape_html(sr_data.get('category', ''))],
        ['요청자', escape_html(sr_data.get('requester', ''))],
        ['생성일', escape_html(format_date(sr_data.get('created_date', '')))],
        ['목표일', escape_html(format_date(sr_data.get('target_date', '')))],
    ]
    
    basic_table = Table(basic_info, colWidths=[4*cm, 13*cm])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), korean_bold_name),
        ('FONTNAME', (1, 0), (1, -1), korean_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 0.5*cm))
    
    # 설명
    story.append(Paragraph("<b>설명</b>", heading_style))
    story.append(Spacer(1, 0.2*cm))
    description = escape_html(sr_data.get('description', '')).replace('\n', '<br/>')
    story.append(Paragraph(description, normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 비즈니스 임팩트
    story.append(Paragraph("<b>비즈니스 임팩트</b>", heading_style))
    story.append(Spacer(1, 0.2*cm))
    business_impact = escape_html(sr_data.get('business_impact', '')).replace('\n', '<br/>')
    story.append(Paragraph(business_impact, normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 기술 요구사항
    tech_reqs = sr_data.get('technical_requirements', [])
    if tech_reqs:
        story.append(Paragraph("<b>기술 요구사항</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        for i, req in enumerate(tech_reqs, 1):
            req_text = escape_html(req)
            story.append(Paragraph(f"{i}. {req_text}", normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 영향받는 컴포넌트
    components = sr_data.get('affected_components', [])
    if components:
        story.append(Paragraph("<b>영향받는 컴포넌트</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        components_text = ", ".join([escape_html(comp) for comp in components])
        story.append(Paragraph(components_text, normal_style))
    
    # PDF 생성
    try:
        doc.build(story)
        print(f"✅ 생성 완료: {output_path}")
        return True
    except Exception as e:
        print(f"❌ PDF 생성 실패 ({sr_data['id']}): {e}")
        import traceback
        traceback.print_exc()
        return False


def create_incident_pdf(incident_data, output_dir):
    """장애 데이터를 PDF로 생성"""
    if not REPORTLAB_AVAILABLE:
        print(f"⚠️ reportlab이 없어 PDF를 생성할 수 없습니다: {incident_data['id']}")
        return False
    
    output_path = Path(output_dir) / f"INC_{incident_data['id']}.pdf"
    
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # 한글 폰트 사용 스타일 생성
    korean_font_name = 'KoreanFont' if 'KoreanFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    korean_bold_name = 'KoreanFont-Bold' if 'KoreanFont-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
    
    # 타이틀 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=korean_bold_name,
        fontSize=18,
        textColor=colors.HexColor('#d62728'),
        spaceAfter=30,
        alignment=1
    )
    
    # 한글 지원 스타일
    heading_style = ParagraphStyle(
        'KoreanHeading',
        parent=styles['Heading2'],
        fontName=korean_bold_name,
        fontSize=14,
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'KoreanNormal',
        parent=styles['Normal'],
        fontName=korean_font_name,
        fontSize=11,
        leading=16
    )
    
    # 제목 추가
    title_text = escape_html(f"장애 보고서: {incident_data['id']}")
    title = Paragraph(f"<b>{title_text}</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # 기본 정보 테이블
    basic_info = [
        ['장애 ID', escape_html(incident_data.get('id', ''))],
        ['제목', escape_html(incident_data.get('title', ''))],
        ['시스템', escape_html(incident_data.get('system', ''))],
        ['심각도', escape_html(incident_data.get('severity', ''))],
        ['상태', escape_html(incident_data.get('status', ''))],
        ['발생일', escape_html(format_date(incident_data.get('reported_date', '')))],
        ['해결일', escape_html(format_date(incident_data.get('resolved_date', '')))],
        ['지속 시간', f"{incident_data.get('duration_minutes', 0)}분"],
        ['영향받은 사용자', f"{incident_data.get('affected_users', 0)}명"],
    ]
    
    basic_table = Table(basic_info, colWidths=[4*cm, 13*cm])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ffe6e6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), korean_bold_name),
        ('FONTNAME', (1, 0), (1, -1), korean_font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 0.5*cm))
    
    # 설명
    story.append(Paragraph("<b>장애 설명</b>", heading_style))
    story.append(Spacer(1, 0.2*cm))
    description = escape_html(incident_data.get('description', '')).replace('\n', '<br/>')
    story.append(Paragraph(description, normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 근본 원인
    root_cause = incident_data.get('root_cause', '')
    if root_cause:
        story.append(Paragraph("<b>근본 원인</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        root_cause_text = escape_html(root_cause)
        story.append(Paragraph(root_cause_text, normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 해결 방법
    resolution = incident_data.get('resolution', '')
    if resolution:
        story.append(Paragraph("<b>해결 방법</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        resolution_text = escape_html(resolution)
        story.append(Paragraph(resolution_text, normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 영향
    impact = incident_data.get('impact', '')
    if impact:
        story.append(Paragraph("<b>영향</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        impact_text = escape_html(impact)
        story.append(Paragraph(impact_text, normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 비즈니스 임팩트
    business_impact = incident_data.get('business_impact', '')
    if business_impact:
        story.append(Paragraph("<b>비즈니스 임팩트</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        business_impact_text = escape_html(business_impact)
        story.append(Paragraph(business_impact_text, normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 재발 방지 조치
    prevention = incident_data.get('prevention_measures', [])
    if prevention:
        story.append(Paragraph("<b>재발 방지 조치</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        for i, measure in enumerate(prevention, 1):
            measure_text = escape_html(measure)
            story.append(Paragraph(f"{i}. {measure_text}", normal_style))
        story.append(Spacer(1, 0.5*cm))
    
    # 관련 컴포넌트
    components = incident_data.get('related_components', [])
    if components:
        story.append(Paragraph("<b>관련 컴포넌트</b>", heading_style))
        story.append(Spacer(1, 0.2*cm))
        components_text = ", ".join([escape_html(comp) for comp in components])
        story.append(Paragraph(components_text, normal_style))
    
    # PDF 생성
    try:
        doc.build(story)
        print(f"✅ 생성 완료: {output_path}")
        return True
    except Exception as e:
        print(f"❌ PDF 생성 실패 ({incident_data['id']}): {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    # 한글 폰트 등록
    print("🔤 한글 폰트 등록 중...")
    register_korean_fonts()
    
    # 출력 디렉토리 생성
    sr_output_dir = Path("pdfs/sr")
    incident_output_dir = Path("pdfs/incident")
    sr_output_dir.mkdir(parents=True, exist_ok=True)
    incident_output_dir.mkdir(parents=True, exist_ok=True)
    
    # SR 데이터 로드 및 PDF 생성
    print("\n📄 SR 문서 생성 중...")
    try:
        with open('sample_sr_data.json', 'r', encoding='utf-8') as f:
            sr_data = json.load(f)
        
        sr_count = 0
        for sr in sr_data:
            if create_sr_pdf(sr, sr_output_dir):
                sr_count += 1
        
        print(f"✅ {sr_count}/{len(sr_data)}개 SR PDF 생성 완료")
    except Exception as e:
        print(f"❌ SR 데이터 로드 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 장애 데이터 로드 및 PDF 생성
    print("\n📄 장애 보고서 생성 중...")
    try:
        with open('sample_incident_data.json', 'r', encoding='utf-8') as f:
            incident_data = json.load(f)
        
        incident_count = 0
        for incident in incident_data:
            if create_incident_pdf(incident, incident_output_dir):
                incident_count += 1
        
        print(f"✅ {incident_count}/{len(incident_data)}개 장애 PDF 생성 완료")
    except Exception as e:
        print(f"❌ 장애 데이터 로드 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📁 생성된 PDF 파일 위치:")
    print(f"   - SR 문서: {sr_output_dir.absolute()}/")
    print(f"   - 장애 보고서: {incident_output_dir.absolute()}/")


if __name__ == "__main__":
    main()

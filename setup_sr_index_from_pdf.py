"""
PDF 파일 구조에 맞춘 SR 인덱스 스키마 설정 스크립트
SR_SR-2024-001.pdf 구조와 일치하는 인덱스를 생성/확인합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.azure_search_client import AzureSearchClient
from src.config import Config
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError


def print_index_schema(index_name: str):
    """인덱스 스키마 출력"""
    config = Config()
    try:
        credential = AzureKeyCredential(config.AZURE_SEARCH_KEY)
        index_client = SearchIndexClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )
        
        index = index_client.get_index(index_name)
        
        print(f"\n📋 인덱스 '{index_name}' 스키마:")
        print("=" * 80)
        print(f"{'필드명':<25} {'타입':<20} {'속성'}")
        print("=" * 80)
        
        for field in index.fields:
            props = []
            if field.key:
                props.append("KEY")
            if hasattr(field, 'searchable') and field.searchable:
                props.append("SEARCHABLE")
            if hasattr(field, 'filterable') and field.filterable:
                props.append("FILTERABLE")
            if hasattr(field, 'facetable') and field.facetable:
                props.append("FACETABLE")
            if hasattr(field, 'sortable') and field.sortable:
                props.append("SORTABLE")
            if hasattr(field, 'analyzer_name') and field.analyzer_name:
                props.append(f"analyzer={field.analyzer_name}")
            
            field_type = str(field.type)
            if hasattr(field, 'collection') and field.collection:
                field_type = f"Collection({field_type})"
            
            props_str = ", ".join(props) if props else "-"
            print(f"{field.name:<25} {field_type:<20} {props_str}")
        
        print("=" * 80)
        
        return True
    except Exception as e:
        print(f"❌ 인덱스 스키마 조회 실패: {e}")
        return False


def verify_pdf_schema_match(index_name: str):
    """PDF 구조와 인덱스 스키마 일치 확인"""
    print("\n🔍 PDF 구조와 인덱스 스키마 일치 확인 중...")
    
    # PDF 파일에서 사용하는 필드 목록 (generate_pdfs.py 기반)
    pdf_fields = {
        'id': 'SR ID',
        'title': '제목',
        'system': '시스템',
        'priority': '우선순위',
        'category': '카테고리',
        'requester': '요청자',
        'created_date': '생성일',
        'target_date': '목표일',
        'description': '설명',
        'business_impact': '비즈니스 임팩트',
        'technical_requirements': '기술 요구사항 (배열)',
        'affected_components': '영향받는 컴포넌트 (배열)'
    }
    
    config = Config()
    try:
        credential = AzureKeyCredential(config.AZURE_SEARCH_KEY)
        index_client = SearchIndexClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )
        
        index = index_client.get_index(index_name)
        index_field_names = {field.name for field in index.fields}
        pdf_field_names = set(pdf_fields.keys())
        
        missing_fields = pdf_field_names - index_field_names
        extra_fields = index_field_names - pdf_field_names
        
        print(f"\n✅ 일치하는 필드: {len(pdf_field_names - missing_fields)}/{len(pdf_fields)}개")
        
        if missing_fields:
            print(f"\n⚠️  인덱스에 없지만 PDF에 있는 필드:")
            for field in missing_fields:
                print(f"   - {field} ({pdf_fields[field]})")
        
        if extra_fields:
            print(f"\nℹ️  PDF에는 없지만 인덱스에 있는 필드:")
            for field in extra_fields:
                print(f"   - {field}")
        
        if not missing_fields and not extra_fields:
            print("\n✅ 모든 필드가 PDF 구조와 일치합니다!")
            return True
        else:
            print("\n⚠️  일부 필드가 일치하지 않습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 확인 실패: {e}")
        return False


def recreate_index(index_name: str, confirm: bool = False):
    """PDF 구조에 맞춰 인덱스 재생성"""
    print(f"\n🔄 인덱스 '{index_name}' 재생성")
    
    if not confirm:
        response = input("⚠️  기존 인덱스의 모든 데이터가 삭제됩니다. 계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ 취소되었습니다.")
            return False
    
    try:
        azure_client = AzureSearchClient()
        
        # 기존 인덱스 삭제
        try:
            index_client = SearchIndexClient(
                endpoint=azure_client.config.AZURE_SEARCH_ENDPOINT,
                credential=azure_client.credential
            )
            index_client.delete_index(index_name)
            print(f"✅ 기존 인덱스 '{index_name}' 삭제 완료")
        except Exception as e:
            print(f"ℹ️  기존 인덱스가 없거나 삭제 실패: {e}")
        
        # 새 인덱스 생성 (PDF 구조에 맞춘 스키마)
        print("\n📝 PDF 구조에 맞춘 인덱스 생성 중...")
        success = azure_client.create_sr_index(index_name)
        
        if success:
            print(f"✅ 인덱스 '{index_name}' 생성 완료")
            print_index_schema(index_name)
            return True
        else:
            print(f"❌ 인덱스 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 인덱스 재생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("=" * 80)
    print("PDF 파일 구조 기반 SR 인덱스 관리 도구")
    print("=" * 80)
    
    config = Config()
    index_name = "key-sr-ktds712"  # search_rag.py에서 사용하는 인덱스명
    
    print(f"\n대상 인덱스: {index_name}")
    print(f"\nPDF 파일 구조에 포함된 필드:")
    print("  1. id - SR ID")
    print("  2. title - 제목")
    print("  3. description - 설명")
    print("  4. system - 시스템")
    print("  5. priority - 우선순위")
    print("  6. category - 카테고리")
    print("  7. requester - 요청자")
    print("  8. created_date - 생성일")
    print("  9. target_date - 목표일")
    print(" 10. business_impact - 비즈니스 임팩트")
    print(" 11. technical_requirements - 기술 요구사항 (배열)")
    print(" 12. affected_components - 영향받는 컴포넌트 (배열)")
    
    print("\n" + "=" * 80)
    print("선택하세요:")
    print("1. 현재 인덱스 스키마 확인")
    print("2. PDF 구조와 일치 확인")
    print("3. PDF 구조에 맞춰 인덱스 재생성")
    print("4. 모두 실행")
    print("0. 종료")
    
    choice = input("\n선택 (0-4): ").strip()
    
    if choice == "1":
        print_index_schema(index_name)
    elif choice == "2":
        verify_pdf_schema_match(index_name)
    elif choice == "3":
        recreate_index(index_name)
    elif choice == "4":
        print_index_schema(index_name)
        verify_pdf_schema_match(index_name)
        if input("\n인덱스를 재생성하시겠습니까? (yes/no): ").lower() == 'yes':
            recreate_index(index_name, confirm=True)
    elif choice == "0":
        print("종료합니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()


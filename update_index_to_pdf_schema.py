"""
Azure 인덱스 "key-sr-ktds712"에 PDF 구조 스키마를 반영하는 스크립트
기존 인덱스를 삭제하고 PDF 구조에 맞는 새 인덱스를 생성한 후 데이터를 재인덱싱합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.azure_search_client import AzureSearchClient
from src.config import Config
from src.data_loader import DataLoader
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError


def update_index_to_pdf_schema(index_name: str = "key-sr-ktds712", auto_confirm: bool = False):
    """
    PDF 구조에 맞춰 인덱스를 재생성하고 데이터를 재인덱싱합니다.
    
    Args:
        index_name: 업데이트할 인덱스 이름
        auto_confirm: True이면 확인 없이 진행
    """
    print("=" * 80)
    print(f"Azure 인덱스 '{index_name}' PDF 구조 스키마 반영")
    print("=" * 80)
    
    if not auto_confirm:
        print("\n⚠️  주의사항:")
        print("1. 기존 인덱스가 삭제됩니다.")
        print("2. 모든 데이터가 삭제됩니다.")
        print("3. 새 인덱스를 생성하고 데이터를 재인덱싱합니다.")
        response = input("\n계속하시겠습니까? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ 취소되었습니다.")
            return False
    
    try:
        # 1. Azure Search 클라이언트 초기화
        print("\n📡 Azure Search 연결 중...")
        azure_client = AzureSearchClient()
        config = Config()
        
        index_client = SearchIndexClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            credential=azure_client.credential
        )
        
        # 2. 기존 인덱스 확인 및 삭제
        print(f"\n🗑️  기존 인덱스 '{index_name}' 확인 중...")
        try:
            existing_index = index_client.get_index(index_name)
            field_count = len(existing_index.fields)
            print(f"   기존 인덱스 발견 (필드 수: {field_count}개)")
            
            print(f"   기존 인덱스 삭제 중...")
            index_client.delete_index(index_name)
            print(f"   ✅ 기존 인덱스 삭제 완료")
        except Exception as e:
            print(f"   ℹ️  기존 인덱스가 없습니다: {e}")
        
        # 3. 새 인덱스 생성 (PDF 구조 스키마)
        print(f"\n📝 PDF 구조에 맞는 새 인덱스 생성 중...")
        success = azure_client.create_sr_index(index_name)
        
        if not success:
            print(f"❌ 인덱스 생성 실패")
            return False
        
        print(f"✅ 인덱스 '{index_name}' 생성 완료")
        
        # 4. 생성된 인덱스 스키마 확인
        print(f"\n📋 생성된 인덱스 스키마:")
        print("-" * 80)
        new_index = index_client.get_index(index_name)
        for field in new_index.fields:
            field_type = str(field.type)
            if hasattr(field, 'collection') and field.collection:
                field_type = f"Collection({field_type})"
            
            props = []
            if field.key:
                props.append("KEY")
            if hasattr(field, 'searchable') and field.searchable:
                props.append("SEARCHABLE")
            if hasattr(field, 'filterable') and field.filterable:
                props.append("FILTERABLE")
            if hasattr(field, 'facetable') and field.facetable:
                props.append("FACETABLE")
            if hasattr(field, 'analyzer_name') and field.analyzer_name:
                props.append(f"analyzer={field.analyzer_name}")
            
            props_str = ", ".join(props) if props else "-"
            print(f"   {field.name:<25} {field_type:<20} {props_str}")
        print("-" * 80)
        
        # 5. 데이터 재인덱싱
        print(f"\n📤 SR 데이터 로드 및 인덱싱 중...")
        data_loader = DataLoader()
        srs = data_loader.load_sr_data()
        
        if not srs:
            print("⚠️  인덱싱할 SR 데이터가 없습니다.")
            print("✅ 인덱스는 생성되었지만 데이터가 없습니다.")
            return True
        
        print(f"   {len(srs)}개 SR 문서를 인덱싱합니다...")
        index_success = azure_client.index_sr_documents(srs, index_name)
        
        if index_success:
            print(f"\n✅ 인덱스 업데이트 완료!")
            print(f"   - 인덱스명: {index_name}")
            print(f"   - 필드 수: {len(new_index.fields)}개")
            print(f"   - 문서 수: {len(srs)}개")
            return True
        else:
            print(f"\n⚠️  인덱스는 생성되었지만 데이터 인덱싱 중 문제가 발생했습니다.")
            return False
            
    except ClientAuthenticationError as auth_error:
        print(f"❌ 인증 오류: {auth_error.message}")
        return False
    except HttpResponseError as http_error:
        print(f"❌ HTTP 오류: {http_error.message}")
        return False
    except Exception as e:
        print(f"❌ 인덱스 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Azure 인덱스를 PDF 구조 스키마로 업데이트')
    parser.add_argument('--index-name', default='key-sr-ktds712', help='업데이트할 인덱스 이름')
    parser.add_argument('--yes', action='store_true', help='확인 없이 진행')
    
    args = parser.parse_args()
    
    success = update_index_to_pdf_schema(args.index_name, auto_confirm=args.yes)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 완료! 이제 search_rag.py에서 업데이트된 인덱스를 사용할 수 있습니다.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ 실패! 오류를 확인하고 다시 시도하세요.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()


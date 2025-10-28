"""
환경 변수 설정 확인 스크립트
Azure AI Search와 OpenAI 설정이 제대로 되어 있는지 확인
"""
import os
from dotenv import load_dotenv

def check_env_setup():
    """환경 변수 설정 확인"""
    print("🔍 환경 변수 설정 확인 중...\n")
    
    # .env 파일 찾기 (현재 디렉토리와 상위 디렉토리)
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(parent_dir)  # SR_Impact_Navigator 디렉토리
    
    env_paths = [
        os.path.join(current_dir, '.env'),           # project_ktds712/.env
        os.path.join(parent_dir, '.env'),            # SR_Impact_Navigator/.env
        os.path.join(root_dir, '.env')               # 상위 디렉토리
    ]
    
    # 중복 제거
    env_paths = list(dict.fromkeys(env_paths))
    
    env_path = None
    for path in env_paths:
        if os.path.exists(path):
            env_path = path
            load_dotenv(path)
            print(f"✅ .env 파일 발견: {path}\n")
            break
    
    if not env_path:
        print("⚠️  .env 파일을 찾을 수 없습니다.")
        print(f"   검색 위치:")
        for path in env_paths:
            print(f"   - {path}")
        print("\n💡 env_example.txt를 참고하여 .env 파일을 생성하세요.\n")
        # .env 파일이 없어도 환경 변수는 로드 시도 (시스템 환경 변수 사용 가능)
        load_dotenv()
    
    # Azure AI Search 설정 확인
    print("=" * 60)
    print("📊 Azure AI Search 설정")
    print("=" * 60)
    
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    search_key = os.getenv("AZURE_SEARCH_KEY", "")
    
    if search_endpoint and search_endpoint != "https://your-search-service.search.windows.net":
        print(f"✅ Endpoint: {search_endpoint}")
    else:
        print("❌ AZURE_SEARCH_ENDPOINT가 설정되지 않았습니다.")
    
    if search_key and search_key != "your-search-key":
        masked_key = search_key[:8] + "..." + search_key[-4:] if len(search_key) > 12 else "***"
        print(f"✅ Key: {masked_key}")
    else:
        print("❌ AZURE_SEARCH_KEY가 설정되지 않았습니다.")
    
    search_configured = (search_endpoint and search_endpoint != "https://your-search-service.search.windows.net" and
                        search_key and search_key != "your-search-key")
    
    # Azure OpenAI 설정 확인
    print("\n" + "=" * 60)
    print("🤖 Azure OpenAI 설정")
    print("=" * 60)
    
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    openai_key = os.getenv("AZURE_OPENAI_KEY", "")
    openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    if openai_endpoint and openai_endpoint != "https://your-openai-service.openai.azure.com":
        print(f"✅ Endpoint: {openai_endpoint}")
    else:
        print("❌ AZURE_OPENAI_ENDPOINT가 설정되지 않았습니다.")
    
    if openai_key and openai_key != "your-openai-key":
        masked_key = openai_key[:8] + "..." + openai_key[-4:] if len(openai_key) > 12 else "***"
        print(f"✅ Key: {masked_key}")
    else:
        print("❌ AZURE_OPENAI_KEY가 설정되지 않았습니다.")
    
    print(f"✅ Deployment: {openai_deployment}")
    
    openai_configured = (openai_endpoint and openai_endpoint != "https://your-openai-service.openai.azure.com" and
                        openai_key and openai_key != "your-openai-key")
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("📋 최종 확인 결과")
    print("=" * 60)
    
    if search_configured:
        print("✅ Azure AI Search: 설정 완료")
    else:
        print("⚠️  Azure AI Search: 설정 필요 (시뮬레이션 모드로 동작)")
    
    if openai_configured:
        print("✅ Azure OpenAI: 설정 완료")
    else:
        print("⚠️  Azure OpenAI: 설정 필요 (규칙 기반 평가로 동작)")
    
    if search_configured and openai_configured:
        print("\n🎉 모든 설정이 완료되었습니다!")
        return True
    elif search_configured or openai_configured:
        print("\n⚠️  일부 설정이 완료되었습니다. 일부 기능은 시뮬레이션 모드로 동작합니다.")
        return True
    else:
        print("\n❌ 설정이 필요합니다. env_example.txt를 참고하여 .env 파일을 작성하세요.")
        return False

if __name__ == "__main__":
    check_env_setup()


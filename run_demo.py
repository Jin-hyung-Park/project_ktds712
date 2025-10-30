#!/usr/bin/env python3
"""
SR Impact Navigator 데모 빠른 실행 스크립트
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """데모 실행"""
    print("🎯 SR Impact Navigator 데모를 시작합니다...")
    
    # 현재 디렉토리 확인
    current_dir = Path(__file__).parent
    os.chdir(current_dir)
    
    # Streamlit 앱 실행
    try:
        print("🚀 Streamlit 앱을 실행합니다...")
        print("📱 브라우저에서 http://localhost:8501 으로 접속하세요")
        print("🛑 종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        # 데모 러너 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "demo_runner.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 데모가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

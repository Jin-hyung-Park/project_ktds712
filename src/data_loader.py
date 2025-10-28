"""
SR 및 장애 데이터 로더
"""
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

class DataLoader:
    """SR 및 장애 데이터를 로드하고 전처리하는 클래스"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.sr_data = None
        self.incident_data = None
        self.billing_config = None
        
    def load_sr_data(self) -> List[Dict[str, Any]]:
        """SR 데이터 로드"""
        try:
            with open(f"{self.data_dir}/sample_sr_data.json", 'r', encoding='utf-8') as f:
                self.sr_data = json.load(f)
            print(f"✅ SR 데이터 로드 완료: {len(self.sr_data)}개")
            return self.sr_data
        except FileNotFoundError:
            print("❌ SR 데이터 파일을 찾을 수 없습니다.")
            return []
    
    def load_incident_data(self) -> List[Dict[str, Any]]:
        """장애 데이터 로드"""
        try:
            with open(f"{self.data_dir}/sample_incident_data.json", 'r', encoding='utf-8') as f:
                self.incident_data = json.load(f)
            print(f"✅ 장애 데이터 로드 완료: {len(self.incident_data)}개")
            return self.incident_data
        except FileNotFoundError:
            print("❌ 장애 데이터 파일을 찾을 수 없습니다.")
            return []
    
    def load_billing_config(self) -> Dict[str, Any]:
        """요금 시스템 설정 로드"""
        try:
            with open(f"{self.data_dir}/billing_system_config.json", 'r', encoding='utf-8') as f:
                self.billing_config = json.load(f)
            print("✅ 요금 시스템 설정 로드 완료")
            return self.billing_config
        except FileNotFoundError:
            print("❌ 요금 시스템 설정 파일을 찾을 수 없습니다.")
            return {}
    
    def get_sr_by_id(self, sr_id: str) -> Dict[str, Any]:
        """ID로 특정 SR 조회"""
        if not self.sr_data:
            self.load_sr_data()
        
        for sr in self.sr_data:
            if sr['id'] == sr_id:
                return sr
        return {}
    
    def get_incidents_by_system(self, system: str) -> List[Dict[str, Any]]:
        """시스템별 장애 조회"""
        if not self.incident_data:
            self.load_incident_data()
        
        return [incident for incident in self.incident_data 
                if incident.get('system') == system]
    
    def get_recent_incidents(self, days: int = 30) -> List[Dict[str, Any]]:
        """최근 N일간의 장애 조회"""
        if not self.incident_data:
            self.load_incident_data()
        
        if not self.incident_data:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_incidents = []
        
        for incident in self.incident_data:
            try:
                incident_date = datetime.strptime(incident['reported_date'], '%Y-%m-%d')
                if incident_date >= cutoff_date:
                    recent_incidents.append(incident)
            except ValueError:
                continue
        
        return recent_incidents
    
    def get_system_importance(self, system: str) -> float:
        """시스템 중요도 조회"""
        if not self.billing_config:
            self.load_billing_config()
        
        # 기본 시스템 중요도 (실제로는 더 복잡한 로직 필요)
        system_importance_map = {
            "요금계산시스템": 1.0,
            "월정액계산엔진": 0.9,
            "사용료계산엔진": 0.9,
            "할인계산엔진": 0.8,
            "청구시스템": 0.7,
            "영업시스템": 0.6
        }
        
        return system_importance_map.get(system, 0.5)
    
    def calculate_sr_complexity(self, sr: Dict[str, Any]) -> float:
        """SR 복잡도 계산"""
        complexity_score = 0.0
        
        # 기술 요구사항 개수 (0.4 가중치)
        tech_requirements = sr.get('technical_requirements', [])
        complexity_score += min(len(tech_requirements) / 10, 1.0) * 0.4
        
        # 영향받는 컴포넌트 개수 (0.3 가중치)
        affected_components = sr.get('affected_components', [])
        complexity_score += min(len(affected_components) / 5, 1.0) * 0.3
        
        # 비즈니스 임팩트 심각도 (0.3 가중치)
        business_impact = sr.get('business_impact', '')
        if '매출 손실' in business_impact or 'Critical' in sr.get('priority', ''):
            complexity_score += 0.3
        elif '고객 불만' in business_impact or 'High' in sr.get('priority', ''):
            complexity_score += 0.2
        elif 'Medium' in sr.get('priority', ''):
            complexity_score += 0.1
        
        return min(complexity_score, 1.0)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """데이터 요약 정보 반환"""
        if not self.sr_data:
            self.load_sr_data()
        if not self.incident_data:
            self.load_incident_data()
        
        return {
            "total_srs": len(self.sr_data) if self.sr_data else 0,
            "total_incidents": len(self.incident_data) if self.incident_data else 0,
            "systems": list(set([sr.get('system', '') for sr in self.sr_data])) if self.sr_data else [],
            "recent_incidents": len(self.get_recent_incidents(30))
        }

# 사용 예시
if __name__ == "__main__":
    loader = DataLoader()
    
    # 데이터 로드
    srs = loader.load_sr_data()
    incidents = loader.load_incident_data()
    config = loader.load_billing_config()
    
    # 요약 정보 출력
    summary = loader.get_data_summary()
    print(f"\n📊 데이터 요약:")
    print(f"SR 개수: {summary['total_srs']}")
    print(f"장애 개수: {summary['total_incidents']}")
    print(f"시스템: {summary['systems']}")
    print(f"최근 30일 장애: {summary['recent_incidents']}")
    
    # SR 복잡도 계산 예시
    if srs:
        first_sr = srs[0]
        complexity = loader.calculate_sr_complexity(first_sr)
        print(f"\n🔍 첫 번째 SR 복잡도: {complexity:.2f}")
        print(f"SR: {first_sr['title']}")

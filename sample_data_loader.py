"""
SR Impact Navigator+ 샘플 데이터 로더
SR 설계문서와 장애보고서 샘플 데이터를 로드하는 유틸리티
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import random

class SampleDataLoader:
    def __init__(self):
        self.sr_data = None
        self.incident_data = None
        
    def load_sr_data(self, file_path="sample_sr_data.json"):
        """SR 설계문서 데이터 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.sr_data = json.load(f)
        return self.sr_data
    
    def load_incident_data(self, file_path="sample_incident_data.json"):
        """장애보고서 데이터 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.incident_data = json.load(f)
        return self.incident_data
    
    def get_sr_by_id(self, sr_id):
        """ID로 SR 데이터 조회"""
        if not self.sr_data:
            self.load_sr_data()
        
        for sr in self.sr_data:
            if sr['id'] == sr_id:
                return sr
        return None
    
    def get_incidents_by_system(self, system):
        """시스템별 장애보고서 조회"""
        if not self.incident_data:
            self.load_incident_data()
        
        return [incident for incident in self.incident_data 
                if incident['system'] == system]
    
    def get_recent_incidents(self, days=30):
        """최근 N일간의 장애보고서 조회"""
        if not self.incident_data:
            self.load_incident_data()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_incidents = []
        
        for incident in self.incident_data:
            incident_date = datetime.strptime(incident['reported_date'], '%Y-%m-%d')
            if incident_date >= cutoff_date:
                recent_incidents.append(incident)
        
        return recent_incidents
    
    def get_high_severity_incidents(self):
        """높은 심각도의 장애보고서 조회"""
        if not self.incident_data:
            self.load_incident_data()
        
        high_severity = ['Critical', 'High']
        return [incident for incident in self.incident_data 
                if incident['severity'] in high_severity]
    
    def get_srs_by_priority(self, priority):
        """우선순위별 SR 조회"""
        if not self.sr_data:
            self.load_sr_data()
        
        return [sr for sr in self.sr_data if sr['priority'] == priority]
    
    def get_srs_by_system(self, system):
        """시스템별 SR 조회"""
        if not self.sr_data:
            self.load_sr_data()
        
        return [sr for sr in self.sr_data if sr['system'] == system]
    
    def get_all_systems(self):
        """모든 시스템 목록 조회"""
        if not self.sr_data:
            self.load_sr_data()
        
        systems = set()
        for sr in self.sr_data:
            systems.add(sr['system'])
        return list(systems)
    
    def get_incident_statistics(self):
        """장애보고서 통계 정보"""
        if not self.incident_data:
            self.load_incident_data()
        
        stats = {
            'total_incidents': len(self.incident_data),
            'by_severity': {},
            'by_system': {},
            'avg_duration': 0,
            'total_affected_users': 0
        }
        
        total_duration = 0
        total_users = 0
        
        for incident in self.incident_data:
            # 심각도별 통계
            severity = incident['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # 시스템별 통계
            system = incident['system']
            stats['by_system'][system] = stats['by_system'].get(system, 0) + 1
            
            # 평균 지속시간
            total_duration += incident['duration_minutes']
            total_users += incident['affected_users']
        
        stats['avg_duration'] = total_duration / len(self.incident_data)
        stats['total_affected_users'] = total_users
        
        return stats
    
    def get_sr_statistics(self):
        """SR 통계 정보"""
        if not self.sr_data:
            self.load_sr_data()
        
        stats = {
            'total_srs': len(self.sr_data),
            'by_priority': {},
            'by_system': {},
            'by_category': {}
        }
        
        for sr in self.sr_data:
            # 우선순위별 통계
            priority = sr['priority']
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # 시스템별 통계
            system = sr['system']
            stats['by_system'][system] = stats['by_system'].get(system, 0) + 1
            
            # 카테고리별 통계
            category = sr['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats

def main():
    """샘플 데이터 로더 테스트"""
    loader = SampleDataLoader()
    
    # 데이터 로드
    sr_data = loader.load_sr_data()
    incident_data = loader.load_incident_data()
    
    print("=== SR Impact Navigator+ 샘플 데이터 ===")
    print(f"SR 설계문서: {len(sr_data)}개")
    print(f"장애보고서: {len(incident_data)}개")
    
    # 통계 정보 출력
    sr_stats = loader.get_sr_statistics()
    incident_stats = loader.get_incident_statistics()
    
    print("\n=== SR 통계 ===")
    print(f"총 SR 수: {sr_stats['total_srs']}")
    print("우선순위별:", sr_stats['by_priority'])
    print("시스템별:", sr_stats['by_system'])
    
    print("\n=== 장애보고서 통계 ===")
    print(f"총 장애 수: {incident_stats['total_incidents']}")
    print("심각도별:", incident_stats['by_severity'])
    print(f"평균 지속시간: {incident_stats['avg_duration']:.1f}분")
    print(f"총 영향 사용자: {incident_stats['total_affected_users']:,}명")

if __name__ == "__main__":
    main()

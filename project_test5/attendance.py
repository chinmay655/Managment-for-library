from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum

class VisitorType(Enum):
    MEMBER = "member"
    VISITOR = "visitor"
    STAFF = "staff"

class AttendanceRecord:
    """Represents a single attendance record."""
    
    def __init__(self, visitor_id: str, name: str, visitor_type: VisitorType, 
                 entry_time: datetime = None):
        self.visitor_id = visitor_id
        self.name = name
        self.visitor_type = visitor_type
        self.entry_time = entry_time or datetime.now()
        self.exit_time: Optional[datetime] = None
        self.purpose = ""  # Purpose of visit for non-members
        self.is_active = True
    
    def check_out(self, exit_time: datetime = None):
        """Mark the visitor as checked out."""
        self.exit_time = exit_time or datetime.now()
        self.is_active = False
    
    def get_duration(self) -> Optional[int]:
        """Get visit duration in minutes."""
        if self.exit_time:
            return int((self.exit_time - self.entry_time).total_seconds() / 60)
        return None
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Checked Out"
        return f"AttendanceRecord(ID: {self.visitor_id}, Name: {self.name}, Type: {self.visitor_type.value}, Status: {status})"

class AttendanceTracker:
    """Manages attendance and visitor tracking."""
    
    def __init__(self):
        self.attendance_records: List[AttendanceRecord] = []
        self.daily_stats = {}  # date -> stats dict
    
    def check_in(self, visitor_id: str, name: str, visitor_type: VisitorType, 
                 purpose: str = "") -> bool:
        """Check in a visitor."""
        # Check if already checked in
        if self.is_currently_present(visitor_id):
            return False
        
        record = AttendanceRecord(visitor_id, name, visitor_type)
        record.purpose = purpose
        self.attendance_records.append(record)
        
        # Update daily stats
        today = date.today()
        if today not in self.daily_stats:
            self.daily_stats[today] = {
                'total_visitors': 0,
                'members': 0,
                'visitors': 0,
                'staff': 0
            }
        
        self.daily_stats[today]['total_visitors'] += 1
        self.daily_stats[today][visitor_type.value + 's'] += 1
        
        return True
    
    def check_out(self, visitor_id: str) -> bool:
        """Check out a visitor."""
        for record in reversed(self.attendance_records):
            if record.visitor_id == visitor_id and record.is_active:
                record.check_out()
                return True
        return False
    
    def is_currently_present(self, visitor_id: str) -> bool:
        """Check if a visitor is currently in the library."""
        for record in reversed(self.attendance_records):
            if record.visitor_id == visitor_id and record.is_active:
                return True
        return False
    
    def get_current_visitors(self) -> List[AttendanceRecord]:
        """Get list of currently present visitors."""
        return [record for record in self.attendance_records if record.is_active]
    
    def get_daily_attendance(self, target_date: date = None) -> List[AttendanceRecord]:
        """Get attendance records for a specific date."""
        if target_date is None:
            target_date = date.today()
        
        return [
            record for record in self.attendance_records
            if record.entry_time.date() == target_date
        ]
    
    def get_visitor_history(self, visitor_id: str) -> List[AttendanceRecord]:
        """Get attendance history for a specific visitor."""
        return [
            record for record in self.attendance_records
            if record.visitor_id == visitor_id
        ]
    
    def get_daily_stats(self, target_date: date = None) -> Dict:
        """Get statistics for a specific date."""
        if target_date is None:
            target_date = date.today()
        
        return self.daily_stats.get(target_date, {
            'total_visitors': 0,
            'members': 0,
            'visitors': 0,
            'staff': 0
        })
    
    def get_weekly_stats(self, week_start: date) -> Dict:
        """Get statistics for a week."""
        weekly_stats = {
            'total_visitors': 0,
            'members': 0,
            'visitors': 0,
            'staff': 0,
            'daily_breakdown': {}
        }
        
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            daily_stats = self.get_daily_stats(current_date)
            weekly_stats['daily_breakdown'][current_date.strftime('%Y-%m-%d')] = daily_stats
            
            weekly_stats['total_visitors'] += daily_stats['total_visitors']
            weekly_stats['members'] += daily_stats['members']
            weekly_stats['visitors'] += daily_stats['visitors']
            weekly_stats['staff'] += daily_stats['staff']
        
        return weekly_stats
    
    def get_peak_hours(self, target_date: date = None) -> Dict:
        """Get peak hours analysis for a specific date."""
        if target_date is None:
            target_date = date.today()
        
        hourly_counts = {}
        daily_records = self.get_daily_attendance(target_date)
        
        for record in daily_records:
            hour = record.entry_time.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (0, 0)
        
        return {
            'hourly_breakdown': hourly_counts,
            'peak_hour': peak_hour[0],
            'peak_count': peak_hour[1]
        }
    
    def export_attendance_report(self, start_date: date, end_date: date) -> List[Dict]:
        """Export attendance report for a date range."""
        report = []
        
        for record in self.attendance_records:
            record_date = record.entry_time.date()
            if start_date <= record_date <= end_date:
                report.append({
                    'visitor_id': record.visitor_id,
                    'name': record.name,
                    'type': record.visitor_type.value,
                    'entry_time': record.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'exit_time': record.exit_time.strftime('%Y-%m-%d %H:%M:%S') if record.exit_time else 'Still Present',
                    'duration_minutes': record.get_duration(),
                    'purpose': record.purpose
                })
        
        return report

from datetime import timedelta

from datetime import datetime, time, timedelta
import pytz
from typing import Dict, List, Optional
from pydantic import BaseModel

# Defined in JST for simplicity based on design doc, 
# but internal logic should handle UTC conversion ideally.
# Design Doc says:
# Tokyo: 09:00 - 15:00 JST (00:00 - 06:00 UTC)
# London: 17:00 - 02:00 JST (approx 08:00 - 17:00 UTC, ignoring DST for now based on simple design)
# NY: 22:00 - 07:00 JST (approx 13:00 - 22:00 UTC)

# Let's stick to design doc specific times relative to JST for consistency
SESSION_DEFINITIONS = {
    "tokyo": {"name": "Tokyo", "start": time(9, 0), "end": time(15, 0), "color": "bg-blue-500"},
    "london": {"name": "London", "start": time(16, 0), "end": time(1, 0), "color": "bg-yellow-500"}, # Adjusted slightly for overlap
    "newyork": {"name": "New York", "start": time(21, 0), "end": time(6, 0), "color": "bg-green-500"}
}

class SessionInfo(BaseModel):
    id: str
    name: str
    status: str # 'active', 'upcoming', 'closed'
    start_time_str: str
    end_time_str: str
    remaining_duration: str # e.g. "4h 30m"
    is_active: bool

class SessionService:
    def __init__(self):
        self.timezone = pytz.timezone('Asia/Tokyo')

    def _is_time_in_range(self, current: time, start: time, end: time) -> bool:
        if start <= end:
            return start <= current < end
        else: # Crosses midnight
            return start <= current or current < end

    def _get_next_start_datetime(self, now: datetime, start: time) -> datetime:
        target = now.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    def _get_upcoming_duration(self, now: datetime, start: time) -> str:
        next_start = self._get_next_start_datetime(now, start)
        diff = next_start - now
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def _get_remaining_duration(self, now: datetime, start: time, end: time) -> str:
        # Calculate end datetime
        end_dt = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if start > end: # Crosses midnight logic for end time relative to now
             if now.time() >= start:
                 end_dt += timedelta(days=1)
        elif now.time() >= end: # Should not happen if confirmed active, but for safety
             end_dt += timedelta(days=1)
             
        diff = end_dt - now
        # If diff is negative (just closed), handle gracefully
        if diff.total_seconds() < 0:
            return "0h 0m"
            
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def get_session_status(self) -> Dict[str, SessionInfo]:
        now = datetime.now(self.timezone)
        current_time = now.time()
        
        results = {}
        for session_id, config in SESSION_DEFINITIONS.items():
            is_active = self._is_time_in_range(current_time, config['start'], config['end'])
            
            status = "closed"
            remaining = ""
            
            if is_active:
                status = "active"
                remaining = self._get_remaining_duration(now, config['start'], config['end'])
            else:
                # Check if it is upcoming (arbitrary definition: starts within 12 hours)
                # For now just mark non-actives as upcoming/closed based on logic
                status = "upcoming"
                remaining = self._get_upcoming_duration(now, config['start'])

            results[session_id] = SessionInfo(
                id=session_id,
                name=config['name'],
                status=status,
                start_time_str=config['start'].strftime("%H:%M"),
                end_time_str=config['end'].strftime("%H:%M"),
                remaining_duration=remaining,
                is_active=is_active
            )
            
        return results
    
    def get_timeline_progress(self) -> float:
        """Get progress percentage of current day (09:00 to 09:00 next day for FX day?) or just 0-24h JST"""
        # Simple 0-24h JST progress
        now = datetime.now(self.timezone)
        seconds_in_day = 24 * 3600
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        return (current_seconds / seconds_in_day) * 100

session_service = SessionService()

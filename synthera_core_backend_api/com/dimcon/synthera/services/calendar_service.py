# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import hashlib
import uuid
import logging
import pytz
import calendar
import holidays

# ================================
# Third-party imports
# ================================

# ================================
# Project-specific imports
# ================================
from com.dimcon.synthera.utilities.log_handler import LoggerManager
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility
from com.dimcon.synthera.utilities.calendar.calendar_utils import (
    RecurrenceHelper, TimezoneHelper
)

from com.dimcon.synthera.resources.tasks.task import Task
from com.dimcon.synthera.resources.meeting.meeting import Meeting

# ================================
# Calendar Service
# ================================
class CalendarService:
    """
    Calendar service using Python libraries for grid and holiday logic.
    """
    
    def __init__(self):
        """Initialize the calendar service with database connection."""
        self.engine = get_engine()
        self.db_util = DBSessionUtil(self.engine)
        self.cognito_util = CognitoUserUtility()
        logger.info("CalendarService initialized successfully")

    def get_month_calendar(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get calendar data for month view with 42-day grid.
        
        Args:
            event: API Gateway event with query parameters and auth
            
        Returns:
            Formatted calendar response
        """
        logger.info("🗓️ Processing month calendar request")
        
        try:
            # Extract user context from API Gateway authorizer
            user_context = self.cognito_util.extract_user_context_from_event(event)
            if not user_context:
                logger.warning("Missing user context from API Gateway authorizer")
                return ResponseBuilder.build_response(401, {"error": "Unauthorized - missing user context"})
            
            logger.info(f"Request authenticated for user: {user_context['user_id']}")
            
            # Extract and validate query parameters
            query_params = event.get('queryStringParameters') or {}
            
            # Parse start parameter (should be YYYY-MM-01)
            start_param = query_params.get('start')
            if not start_param:
                return ResponseBuilder.build_response(400, {"error": "Missing 'start' parameter"})
            
            try:
                start_date = datetime.fromisoformat(start_param.replace('Z', ''))
                logger.debug(f"Parsed start date: {start_date}")
            except ValueError:
                return ResponseBuilder.build_response(400, 
                    {"error": "Invalid 'start' parameter format. Expected YYYY-MM-DD"})
            
            # Parse timezone parameter
            tz_param = query_params.get('tz', 'UTC')
            if not TimezoneHelper.validate_timezone(tz_param):
                return ResponseBuilder.build_response(400, 
                    {"error": f"Invalid timezone: {tz_param}"})
            
            logger.debug(f"Using timezone: {tz_param}")
            
            # Generate calendar grid and window
            calendar_data = self._generate_calendar_grid(
                year=start_date.year,
                month=start_date.month,
                timezone=tz_param,
                user_context=user_context
            )
            
            # Generate ETag for caching
            etag = self._generate_etag(user_context, start_date, tz_param, calendar_data)
            
            # Check if client has cached version
            if_none_match = event.get('headers', {}).get('if-none-match')
            if if_none_match and if_none_match.strip('"') == etag:
                logger.info("Returning 304 Not Modified for cached content")
                return ResponseBuilder.build_cors_response(304, {})
            
            logger.info("✅ Month calendar request completed successfully")
            
            # Build response with caching headers
            response = ResponseBuilder.build_cors_response(200, calendar_data)
            response['headers']['ETag'] = f'"{etag}"'
            response['headers']['Cache-Control'] = 'max-age=30'
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing month calendar request: {str(e)}")
            logger.exception("Calendar request error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    def _generate_calendar_grid(self, year: int, month: int, timezone: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the complete 42-day calendar grid with events.
        
        Args:
            year: Year for the calendar
            month: Month for the calendar
            timezone: IANA timezone for display
            user_context: Authenticated user context
            
        Returns:
            Complete calendar data structure
        """
        logger.debug(f"Generating calendar grid for {year}-{month} in {timezone}")
        
        # Generate month boundaries and grid
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Use Python's calendar lib to generate a 6-week grid (42 days)
        cal = calendar.Calendar(firstweekday=6)  # Sunday start
        month_days = cal.monthdayscalendar(year, month)
        grid_dates = []
        for week in month_days:
            for day in week:
                if day == 0:
                    # Fill with previous/next month days
                    if len(grid_dates) == 0:
                        # Previous month
                        prev_month = month - 1 if month > 1 else 12
                        prev_year = year if month > 1 else year - 1
                        last_day_prev_month = calendar.monthrange(prev_year, prev_month)[1]
                        grid_dates.append(date(prev_year, prev_month, last_day_prev_month))
                    else:
                        # Next month
                        next_month = month + 1 if month < 12 else 1
                        next_year = year if month < 12 else year + 1
                        grid_dates.append(date(next_year, next_month, 1))
                else:
                    grid_dates.append(date(year, month, day))
        
        # Ensure 42 days
        while len(grid_dates) < 42:
            last_date = grid_dates[-1]
            next_date = last_date + timedelta(days=1)
            grid_dates.append(next_date)
        
        grid_start = grid_dates[0]
        grid_end = grid_dates[-1]
        
        # Convert grid boundaries to UTC for database queries
        grid_start_utc = datetime.combine(grid_start, datetime.min.time()).replace(tzinfo=pytz.utc)
        grid_end_utc = datetime.combine(grid_end + timedelta(days=1), datetime.min.time()).replace(tzinfo=pytz.utc)
        
        # Fetch events from database
        with self.db_util.session_scope() as session:
            events = self._fetch_calendar_events(
                session, user_context, grid_start_utc, grid_end_utc
            )
        
        # Process and distribute events across grid days
        grid_data = self._distribute_events_to_grid(
            grid_dates, month, timezone, events
        )
        
        # Generate today panel data
        today_panel = self._generate_today_panel(events, timezone)
        
        # Build complete response
        return {
            "tz": timezone,
            "window": {
                "monthStart": datetime.combine(month_start, datetime.min.time()).isoformat() + "Z",
                "monthEnd": datetime.combine(month_end, datetime.max.time()).isoformat() + "Z",
                "gridStart": grid_start_utc.isoformat(),
                "gridEnd": grid_end_utc.isoformat()
            },
            "labels": {
                "monthTitle": month_start.strftime("%B %Y"),
                "daysOfWeek": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            },
            "days": grid_data,
            "todayPanel": today_panel
        }

    def _fetch_calendar_events(self, session, user_context: Dict[str, Any], start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """
        Fetch meetings (organized by user) and tasks (assigned to user) using ORM queries.
        """
        events: List[Dict[str, Any]] = []
        try:
            user_id = int(user_context['user_id'])  # Assuming user_id is integer (Employee.emp_id)

            # Fetch meetings organized by the user
            meetings = session.query(Meeting).filter(
                Meeting.created_by == user_id,
                Meeting.scheduled_start_time < end_utc,
                Meeting.scheduled_end_time >= start_utc
            ).all()

            for m in meetings:
                events.append({
                    "kind": "MEETING",
                    "id": m.meeting_id,
                    "title": m.meeting_title,
                    "start_at": m.scheduled_start_time,
                    "end_at": m.scheduled_end_time ,
                    "timezone": m.timezone or "UTC",
                    "recurrence_rule": m.recurrence_rule,
                    "all_day": False,
                    "exdates": []
                })

            # Fetch tasks assigned to the user
            tasks = session.query(Task).filter(
                Task.assigned_to == user_id,
                ((Task.due_date < end_utc) | (Task.created_at < end_utc)),
                ((Task.due_date >= start_utc) | (Task.created_at >= start_utc))
            ).all()

            for t in tasks:
                events.append({
                    "kind": "TASK",
                    "id": t.task_id,
                    "title": t.task_title,
                    "start_at": t.due_date or t.created_at,
                    "end_at": t.due_date or (t.created_at + timedelta(hours=1)),
                    "timezone": t.timezone or "UTC",
                    "recurrence_rule": t.recurrence_rule,
                    "all_day": True,
                    "exdates": [],
                    "metadata": {
                        "created_by": t.created_by,
                        "updated_by": t.updated_by,
                        "org_id": t.org_id,
                        "assigned_to": t.assigned_to
                    }
                })
            return events
        except Exception as ex:
            logger.error(f"_fetch_calendar_events failed: {ex}")
            logger.exception("Details:")
            return []

    def _distribute_events_to_grid(self, grid_dates: List[date], target_month: int, timezone: str, events: List[Dict]) -> List[Dict]:
        """
        Distribute events across the 42-day calendar grid.
        
        Args:
            grid_dates: List of 42 grid dates
            target_month: Target month number
            timezone: Display timezone
            events: List of events to distribute
            
        Returns:
            List of 42 day objects with events
        """
        logger.debug(f"Distributing events across {len(grid_dates)} grid days")
        
        # Get US holidays for all years in grid
        years = set(d.year for d in grid_dates)
        us_holidays = holidays.US(years=years)
        grid_data = []
        day_lookup = {}
        for d in grid_dates:
            day_str = d.strftime('%Y-%m-%d')
            is_weekend = d.weekday() in [5, 6]
            is_us_holiday = d in us_holidays
            grid_data.append({
                "date": day_str,
                "isHoliday": is_weekend or is_us_holiday,
                "holidayName": us_holidays.get(d) if is_us_holiday else None,
                "events": [],
                "inMonth": d.month == target_month
            })
            day_lookup[day_str] = grid_data[-1]
        for event in events:
            try:
                event_instances = self._expand_event_instances(
                    event, grid_dates[0], grid_dates[-1] + timedelta(days=1), timezone
                )
                for instance in event_instances:
                    touched_days = self._get_touched_days(
                        instance['localStart'], instance['localEnd'], instance['allDay']
                    )
                    for day_str in touched_days:
                        if day_str in day_lookup:
                            day_lookup[day_str]['events'].append(instance)
            except Exception as e:
                logger.error(f"Error processing event {event.get('id', 'unknown')}: {str(e)}")
                continue
        for day_info in grid_data:
            day_info['events'].sort(key=lambda e: (
                e['localStart'] if not e['allDay'] else '1900-01-01T00:00:00',
                e['title']
            ))
        logger.debug(f"Distributed events to grid successfully")
        return grid_data

    def _expand_event_instances(self, event: Dict, window_start: date, window_end: date, timezone: str) -> List[Dict]:
        """
        Expand a single event into multiple instances if recurring.
        
        Args:
            event: Event dictionary
            window_start: Window start date
            window_end: Window end date
            timezone: Display timezone
            
        Returns:
            List of event instances
        """
        instances = []
        
        try:
            # Convert window to datetime for comparison
            window_start_dt = datetime.combine(window_start, datetime.min.time()).replace(tzinfo=pytz.utc)
            window_end_dt = datetime.combine(window_end, datetime.min.time()).replace(tzinfo=pytz.utc)
            
            if event.get('recurrence_rule'):
                # Expand recurring event
                occurrences = RecurrenceHelper.expand_rrule_instances(
                    rrule_str=event['recurrence_rule'],
                    start_dt=event['start_at'],
                    end_dt=event['end_at'],
                    window_start=window_start_dt,
                    window_end=window_end_dt,
                    exdates=event.get('exdates', [])
                )
                
                # Create instance for each occurrence
                event_duration = event['end_at'] - event['start_at'] if event['end_at'] and event['start_at'] else timedelta(hours=1)
                
                for occurrence_start in occurrences:
                    occurrence_end = occurrence_start + event_duration
                    instance = self._create_event_instance(
                        event, occurrence_start, occurrence_end, timezone
                    )
                    instances.append(instance)
            else:
                # Single occurrence
                if event['start_at'] and event['end_at']:
                    # Check if event overlaps with window
                    if event['start_at'] < window_end_dt and event['end_at'] >= window_start_dt:
                        instance = self._create_event_instance(
                            event, event['start_at'], event['end_at'], timezone
                        )
                        instances.append(instance)
            
            return instances
            
        except Exception as e:
            logger.error(f"Error expanding event instances: {str(e)}")
            return []

    def _create_event_instance(self, event: Dict, start_utc: datetime, end_utc: datetime, timezone: str) -> Dict:
        """
        Create a single event instance with timezone conversion.
        
        Args:
            event: Original event data
            start_utc: Instance start time (UTC)
            end_utc: Instance end time (UTC)
            timezone: Display timezone
            
        Returns:
            Event instance dictionary
        """
        try:
            # Convert to display timezone
            local_start = TimezoneHelper.convert_to_timezone(start_utc, timezone)
            local_end = TimezoneHelper.convert_to_timezone(end_utc, timezone)
            
            # Generate instance ID
            instance_id = f"{event['kind'].lower()}:{event['id']}:{start_utc.isoformat()}"
            
            # Format time label
            time_label = TimezoneHelper.format_time_label(local_start, local_end, event.get('all_day', False))
            
            return {
                "id": f"{event['kind'].lower()}:{event['id']}",
                "instanceId": instance_id,
                "kind": event['kind'],
                "title": event['title'],
                "start": start_utc.isoformat(),
                "end": end_utc.isoformat(),
                "localStart": local_start.isoformat(),
                "localEnd": local_end.isoformat(),
                "timeLabel": time_label,
                "allDay": event.get('all_day', False),
                "conference": event.get('conference')
            }
            
        except Exception as e:
            logger.error(f"Error creating event instance: {str(e)}")
            return {
                "id": f"{event['kind'].lower()}:{event['id']}",
                "instanceId": f"{event['kind'].lower()}:{event['id']}:error",
                "kind": event['kind'],
                "title": event['title'],
                "start": start_utc.isoformat() if start_utc else "",
                "end": end_utc.isoformat() if end_utc else "",
                "localStart": start_utc.isoformat() if start_utc else "",
                "localEnd": end_utc.isoformat() if end_utc else "",
                "timeLabel": "Error",
                "allDay": event.get('all_day', False),
                "conference": None
            }

    def _get_touched_days(self, local_start: str, local_end: str, all_day: bool) -> List[str]:
        """
        Get list of day strings that an event touches.
        
        Args:
            local_start: Local start time ISO string
            local_end: Local end time ISO string
            all_day: Whether event is all-day
            
        Returns:
            List of YYYY-MM-DD date strings
        """
        try:
            start_dt = datetime.fromisoformat(local_start.replace('Z', ''))
            end_dt = datetime.fromisoformat(local_end.replace('Z', ''))
            
            touched_days = []
            
            if all_day:
                # All-day events touch all days from start to end (inclusive)
                current_date = start_dt.date()
                end_date = end_dt.date()
                
                while current_date <= end_date:
                    touched_days.append(current_date.strftime('%Y-%m-%d'))
                    current_date += timedelta(days=1)
            else:
                # Timed events touch days they overlap with
                start_date = start_dt.date()
                end_date = end_dt.date()
                
                touched_days.append(start_date.strftime('%Y-%m-%d'))
                if end_date != start_date:
                    touched_days.append(end_date.strftime('%Y-%m-%d'))
            
            return touched_days
            
        except Exception as e:
            logger.error(f"Error calculating touched days: {str(e)}")
            return []

    def _generate_today_panel(self, events: List[Dict], timezone: str) -> Dict:
        """
        Generate today panel data with today's meetings and open tasks.
        
        Args:
            events: List of all events
            timezone: Display timezone
            
        Returns:
            Today panel data
        """
        try:
            today = date.today()
            today_str = today.strftime('%Y-%m-%d')
            
            # Convert today to timezone boundaries
            today_start = TimezoneHelper.convert_from_timezone(
                datetime.combine(today, datetime.min.time()), timezone
            )
            today_end = TimezoneHelper.convert_from_timezone(
                datetime.combine(today, datetime.max.time()), timezone
            )
            
            meetings_today = []
            tasks_today = []
            
            for event in events:
                try:
                    # Check if event has instances today
                    event_instances = self._expand_event_instances(
                        event, today, today + timedelta(days=1), timezone
                    )
                    
                    for instance in event_instances:
                        if instance['localStart'].startswith(today_str):
                            if event['kind'] == 'MEETING':
                                meetings_today.append({
                                    'timeLabel': instance['timeLabel'],
                                    'title': instance['title']
                                })
                            elif event['kind'] == 'TASK':
                                tasks_today.append(instance['title'])
                    
                except Exception as e:
                    logger.error(f"Error processing event for today panel: {str(e)}")
                    continue
            
            # Sort meetings by time
            meetings_today.sort(key=lambda m: m['timeLabel'])
            
            return {
                "today": today_str,
                "meetingsCalls": {
                    "count": len(meetings_today),
                    "items": meetings_today[:5]  # Limit to 5 items
                },
                "tasksOpen": {
                    "count": len(tasks_today),
                    "items": tasks_today[:5]  # Limit to 5 items
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating today panel: {str(e)}")
            return {
                "today": date.today().strftime('%Y-%m-%d'),
                "meetingsCalls": {"count": 0, "items": []},
                "tasksOpen": {"count": 0, "items": []}
            }

    def _generate_etag(self, user_context: Dict, start_date: datetime, timezone: str, calendar_data: Dict) -> str:
        """
        Generate ETag for caching based on request parameters and data.
        """
        try:
            # Use default value 1 for org_id if missing
            org_id = user_context.get('org_id', 1)
            hash_input = f"{user_context['user_id']}:{org_id}:{start_date.isoformat()}:{timezone}"

            content_str = json.dumps(calendar_data, sort_keys=True, default=str)
            content_hash = hashlib.md5(content_str.encode()).hexdigest()[:8]

            etag = hashlib.md5(f"{hash_input}:{content_hash}".encode()).hexdigest()

            logger.debug(f"Generated ETag: {etag}")
            return etag

        except Exception as e:
            logger.error(f"Error generating ETag: {str(e)}")
            return "error"

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Testing CalendarService")
    try:
        service = CalendarService()
        logger.info("CalendarService instantiated successfully")
        sample_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "34f84428-20b1-7052-98cf-8d3ac200c040",
                        "email": "vamsikrishna.solleti@dimcon.com",
                        "cognito:username": "vksolleti"
                    }
                }
            },
            "queryStringParameters": {
                "start": "2025-10-01",
                "tz": "America/New_York"
            },
            "headers": {
                "Authorization": "Bearer eyJraWQiOiJwVWZ1..."
            }
        }
        logger.info("Sample event structure created for testing")
        
        result = service.get_month_calendar(sample_event)
        print(result)
    except Exception as e:
        logger.error(f"Error testing CalendarService: {str(e)}")
        logger.exception("Service test error details:")
        raise

# ================================
# Add project root to sys.path
# ================================
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import pytz
from dateutil import rrule
from dateutil.rrule import rrulestr

# ================================
# Project-specific imports
# ================================
import logging
from com.dimcon.synthera.utilities.log_handler import LoggerManager
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

# ================================
# Recurrence Utilities
# ================================
class RecurrenceHelper:
    """
    Helper class for handling RFC 5545 RRULE recurrence patterns.
    Provides methods to expand recurring events within date windows.
    """
    
    @staticmethod
    def expand_rrule_instances(rrule_str: str, start_dt: datetime, end_dt: datetime, 
                              window_start: datetime, window_end: datetime,
                              exdates: List[datetime] = None) -> List[datetime]:
        """
        Expand RRULE instances within the specified window.
        
        Args:
            rrule_str: RFC 5545 RRULE string
            start_dt: Original event start datetime (UTC)
            end_dt: Original event end datetime (UTC)
            window_start: Window start datetime (UTC)
            window_end: Window end datetime (UTC)
            exdates: List of exception dates to exclude (UTC)
            
        Returns:
            List of occurrence start datetimes within the window
        """
        logger.debug(f"Expanding RRULE: {rrule_str}")
        logger.debug(f"Original event: {start_dt} to {end_dt}")
        logger.debug(f"Window: {window_start} to {window_end}")
        
        if not rrule_str:
            logger.debug("No RRULE provided, returning empty list")
            return []
        
        try:
            # Parse the RRULE with the original event start time
            rule = rrulestr(rrule_str, dtstart=start_dt)
            
            # Get occurrences within an expanded window to catch events that might overlap
            # Expand the window by the event duration to catch events that start before but overlap
            event_duration = end_dt - start_dt if end_dt and start_dt else timedelta(hours=1)
            expanded_window_start = window_start - event_duration
            
            # Generate occurrences within the expanded window
            occurrences = list(rule.between(expanded_window_start, window_end, inc=True))
            
            logger.debug(f"Generated {len(occurrences)} raw occurrences")
            
            # Filter out exdates if provided
            exdates_set = set(exdates or [])
            if exdates_set:
                logger.debug(f"Filtering out {len(exdates_set)} exception dates")
                occurrences = [occ for occ in occurrences if occ not in exdates_set]
            
            # Filter to only include occurrences where the event would overlap with the window
            filtered_occurrences = []
            for occurrence in occurrences:
                occurrence_end = occurrence + event_duration
                # Check if this occurrence overlaps with the window
                if occurrence < window_end and occurrence_end >= window_start:
                    filtered_occurrences.append(occurrence)
            
            logger.debug(f"Final filtered occurrences: {len(filtered_occurrences)}")
            return filtered_occurrences
            
        except Exception as e:
            logger.error(f"Error expanding RRULE '{rrule_str}': {str(e)}")
            logger.exception("RRULE expansion error details:")
            return []

    @staticmethod
    def build_rrule_from_params(freq: str, interval: int = 1, by_day: List[str] = None,
                               by_month_day: List[int] = None, by_day_rule: Dict = None,
                               ends: Dict = None) -> str:
        """
        Build RRULE string from structured parameters.
        
        Args:
            freq: Frequency (DAILY, WEEKLY, MONTHLY, YEARLY)
            interval: Interval between occurrences
            by_day: Days of week for WEEKLY (e.g., ['MO', 'WE', 'FR'])
            by_month_day: Days of month for MONTHLY (e.g., [15, 30])
            by_day_rule: Complex day rule for MONTHLY (e.g., {"weekday": "FR", "position": -1})
            ends: End condition (e.g., {"type": "UNTIL", "date": "2025-12-31"})
            
        Returns:
            RFC 5545 RRULE string
        """
        logger.debug(f"Building RRULE - freq: {freq}, interval: {interval}")
        
        try:
            parts = [f"FREQ={freq.upper()}"]
            
            if interval and interval > 1:
                parts.append(f"INTERVAL={interval}")
            
            # Handle by-day rules for weekly
            if freq.upper() == 'WEEKLY' and by_day:
                parts.append(f"BYDAY={','.join(by_day)}")
                logger.debug(f"Added BYDAY for weekly: {by_day}")
            
            # Handle by-month-day for monthly
            if freq.upper() == 'MONTHLY' and by_month_day:
                parts.append(f"BYMONTHDAY={','.join(map(str, by_month_day))}")
                logger.debug(f"Added BYMONTHDAY for monthly: {by_month_day}")
            
            # Handle complex by-day rules for monthly (e.g., last Friday)
            if freq.upper() == 'MONTHLY' and by_day_rule:
                weekday = by_day_rule.get('weekday', '').upper()[:2]  # MO, TU, WE, etc.
                position = by_day_rule.get('position', 1)  # 1=first, -1=last
                if weekday and position:
                    parts.append(f"BYDAY={position}{weekday}")
                    logger.debug(f"Added complex BYDAY for monthly: {position}{weekday}")
            
            # Handle end conditions
            if ends:
                end_type = ends.get('type', '').upper()
                if end_type == 'UNTIL' and ends.get('date'):
                    # Parse date and format for RRULE
                    until_date = datetime.fromisoformat(ends['date'].replace('Z', '+00:00'))
                    parts.append(f"UNTIL={until_date.strftime('%Y%m%dT%H%M%SZ')}")
                    logger.debug(f"Added UNTIL: {ends['date']}")
                elif end_type == 'COUNT' and ends.get('count'):
                    parts.append(f"COUNT={ends['count']}")
                    logger.debug(f"Added COUNT: {ends['count']}")
            
            rrule_string = ';'.join(parts)
            logger.debug(f"Built RRULE: {rrule_string}")
            return rrule_string
            
        except Exception as e:
            logger.error(f"Error building RRULE: {str(e)}")
            logger.exception("RRULE building error details:")
            raise ValueError(f"Invalid recurrence parameters: {str(e)}")

    @staticmethod
    def validate_rrule(rrule_str: str) -> bool:
        """
        Validate that an RRULE string is properly formatted.
        
        Args:
            rrule_str: RRULE string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not rrule_str:
                return True  # Empty RRULE is valid (no recurrence)
            
            # Try to parse the RRULE
            test_start = datetime.now()
            rule = rrulestr(rrule_str, dtstart=test_start)
            
            # Try to generate a few occurrences to ensure it works
            list(rule[:5])  # Get first 5 occurrences
            
            logger.debug(f"RRULE validation passed: {rrule_str}")
            return True
            
        except Exception as e:
            logger.warning(f"RRULE validation failed for '{rrule_str}': {str(e)}")
            return False

# ================================
# Timezone Utilities
# ================================
class TimezoneHelper:
    """Utility functions for timezone validation and conversions."""

    @staticmethod
    def validate_timezone(tz_str: str) -> bool:
        """
        Validate that a timezone string is a valid IANA timezone.
        Supports both zoneinfo (Python 3.9+) and pytz.
        """
        if not tz_str or not isinstance(tz_str, str):
            return False

        tz_str = tz_str.strip()

        # Try with zoneinfo
        try:
            ZoneInfo(tz_str)
            return True
        except Exception:
            pass

        # Try with pytz
        try:
            pytz.timezone(tz_str)
            return True
        except Exception:
            pass

        logger.warning(f"Invalid timezone: {tz_str}")
        return False

    @staticmethod
    def convert_from_timezone(dt: datetime, tz_str: str) -> datetime:
        """
        Convert a local datetime (naive or tz-aware) in the given timezone to UTC.
        Example: "2025-09-01T10:00:00" in America/New_York → 2025-09-01T14:00:00Z
        """
        if not TimezoneHelper.validate_timezone(tz_str):
            raise ValueError(f"Invalid timezone: {tz_str}")

        tz_str = tz_str.strip()

        if dt.tzinfo is None:
            # Naive datetime → localize
            try:
                tz = ZoneInfo(tz_str)
                dt = dt.replace(tzinfo=tz)
            except Exception:
                tz = pytz.timezone(tz_str)
                dt = tz.localize(dt)
        else:
            # Aware datetime → convert
            try:
                tz = ZoneInfo(tz_str)
                dt = dt.astimezone(tz)
            except Exception:
                tz = pytz.timezone(tz_str)
                dt = dt.astimezone(tz)

        return dt.astimezone(timezone.utc)

    @staticmethod
    def convert_to_timezone(dt: datetime, tz_str: str) -> datetime:
        """
        Convert a UTC datetime to the given timezone.
        Example: 2025-09-01T14:00:00Z → 2025-09-01T10:00:00 in America/New_York
        """
        if not TimezoneHelper.validate_timezone(tz_str):
            raise ValueError(f"Invalid timezone: {tz_str}")

        tz_str = tz_str.strip()

        # Ensure input is UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        # Convert to target zone
        try:
            tz = ZoneInfo(tz_str)
            return dt.astimezone(tz)
        except Exception:
            tz = pytz.timezone(tz_str)
            return dt.astimezone(tz)

    @staticmethod
    def format_time_label(start_dt: datetime, end_dt: datetime, all_day: bool = False) -> str:
        """
        Format a time label for display (e.g., "9:00–9:30 AM").
        
        Args:
            start_dt: Start datetime (should be in display timezone)
            end_dt: End datetime (should be in display timezone)
            all_day: Whether this is an all-day event
            
        Returns:
            Formatted time label string
        """
        if all_day:
            return "All day"
        
        if not start_dt or not end_dt:
            return ""
        
        try:
            # Check if times are on the same day
            if start_dt.date() == end_dt.date():
                # Same day - format as "9:00–9:30 AM" or "9:00 AM–5:00 PM"
                start_time = start_dt.strftime("%I:%M").lstrip('0')
                end_time = end_dt.strftime("%I:%M").lstrip('0')
                
                # Check if AM/PM are the same
                if start_dt.strftime("%p") == end_dt.strftime("%p"):
                    return f"{start_time}–{end_time} {start_dt.strftime('%p')}"
                else:
                    return f"{start_time} {start_dt.strftime('%p')}–{end_time} {end_dt.strftime('%p')}"
            else:
                # Different days - include dates
                start_str = start_dt.strftime("%m/%d %I:%M %p").lstrip('0')
                end_str = end_dt.strftime("%m/%d %I:%M %p").lstrip('0')
                return f"{start_str}–{end_str}"
                
        except Exception as e:
            logger.error(f"Error formatting time label: {str(e)}")
            return f"{start_dt}–{end_dt}"

    
    @staticmethod
    def get_week_boundaries(date_obj: date, week_start_day: int = 6) -> Tuple[date, date]:
        """
        Get the start and end dates of the week containing the given date.
        
        Args:
            date_obj: Date to find week boundaries for
            week_start_day: Day of week that starts the week (0=Monday, 6=Sunday)
            
        Returns:
            Tuple of (week_start_date, week_end_date)
        """
        try:
            # Find the start of the week
            days_from_start = (date_obj.weekday() - week_start_day) % 7
            week_start = date_obj - timedelta(days=days_from_start)
            week_end = week_start + timedelta(days=6)
            
            logger.debug(f"Week boundaries for {date_obj}: {week_start} to {week_end}")
            return week_start, week_end
            
        except Exception as e:
            logger.error(f"Error calculating week boundaries: {str(e)}")
            return date_obj, date_obj

    @staticmethod
    def get_month_boundaries(year: int, month: int) -> Tuple[date, date]:
        """
        Get the start and end dates of the given month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            Tuple of (month_start_date, month_end_date)
        """
        try:
            month_start = date(year, month, 1)
            
            # Calculate last day of month
            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)
            
            month_end = next_month_start - timedelta(days=1)
            
            logger.debug(f"Month boundaries for {year}-{month}: {month_start} to {month_end}")
            return month_start, month_end
            
        except Exception as e:
            logger.error(f"Error calculating month boundaries: {str(e)}")
            raise ValueError(f"Invalid year/month: {year}/{month}")

# ================================
# Calendar Grid Utilities
# ================================
class CalendarGridHelper:
    """
    Helper class for generating calendar grid layouts.
    """
    
    @staticmethod
    def generate_42_day_grid(year: int, month: int, week_start_day: int = 6) -> List[date]:
        """
        Generate a 42-day calendar grid (6 weeks × 7 days) for the given month.
        
        Args:
            year: Year
            month: Month (1-12)
            week_start_day: Day of week that starts the week (0=Monday, 6=Sunday)
            
        Returns:
            List of 42 date objects representing the grid
        """
        logger.debug(f"Generating 42-day grid for {year}-{month}")
        
        try:
            # Get the first day of the month
            first_day = date(year, month, 1)
            
            # Find the start of the calendar grid (may be in previous month)
            days_from_week_start = (first_day.weekday() - week_start_day) % 7
            grid_start = first_day - timedelta(days=days_from_week_start)
            
            # Generate 42 consecutive days
            grid_dates = []
            for i in range(42):
                grid_dates.append(grid_start + timedelta(days=i))
            
            logger.debug(f"Grid starts on {grid_start} and ends on {grid_dates[-1]}")
            return grid_dates
            
        except Exception as e:
            logger.error(f"Error generating calendar grid: {str(e)}")
            raise ValueError(f"Invalid year/month: {year}/{month}")

    @staticmethod
    def categorize_grid_dates(grid_dates: List[date], target_month: int) -> List[Dict[str, Any]]:
        """
        Categorize grid dates with metadata for calendar display.
        
        Args:
            grid_dates: List of dates in the grid
            target_month: The target month being displayed
            
        Returns:
            List of date info dictionaries
        """
        logger.debug(f"Categorizing {len(grid_dates)} grid dates for month {target_month}")
        
        date_info = []
        today = date.today()
        
        for grid_date in grid_dates:
            info = {
                'date': grid_date.strftime('%Y-%m-%d'),
                'is_current_month': grid_date.month == target_month,
                'is_weekend': grid_date.weekday() in [5, 6],  # Saturday=5, Sunday=6
                'is_today': grid_date == today,
                'is_holiday': False,  # Will be set by calendar service
                'events': []  # Will be populated by calendar service
            }
            date_info.append(info)
        
        return date_info

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Testing calendar utilities")
    
    try:
        # Test RRULE building
        rrule_str = RecurrenceHelper.build_rrule_from_params(
            freq='WEEKLY',
            interval=2,
            by_day=['MO', 'WE', 'FR'],
            ends={'type': 'COUNT', 'count': 10}
        )
        print(f"Built RRULE: {rrule_str}")
        
        # Test timezone conversion
        utc_time = datetime.now()
        ny_time = TimezoneHelper.convert_to_timezone(utc_time, 'America/New_York')
        print(f"UTC: {utc_time} -> NY: {ny_time}")
        
        # Test calendar grid generation
        grid = CalendarGridHelper.generate_42_day_grid(2025, 8)
        print(f"Generated {len(grid)} grid dates for August 2025")
        
        logger.info("Calendar utilities test completed successfully")
        
    except Exception as e:
        logger.error(f"Error testing calendar utilities: {str(e)}")
        logger.exception("Test error details:")
        raise

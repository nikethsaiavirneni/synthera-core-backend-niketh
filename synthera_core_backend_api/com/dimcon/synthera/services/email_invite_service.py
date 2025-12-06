# com/dimcon/synthera/services/email_invite_service.py
import os, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ===== SMTP config (use env vars; do NOT hardcode secrets) =====
SMTP_SERVER   = os.environ.get("SMTP_SERVER",  "email-smtp.us-east-1.amazonaws.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")        # e.g., SES SMTP user
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")        # e.g., SES SMTP password
DEFAULT_FROM  = os.environ.get("FROM_EMAIL")           # verified sender in SES
BRAND         = os.environ.get("BRAND", "Synthera")

def _fmt(dt_utc):
    # dt_utc must be timezone-aware UTC
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")

def _build_ics(uid, method, organizer_email, attendee_email, start_utc=None, end_utc=None,
               location_url="", sequence=0, summary=None):
    """
    Build a minimal ICS. No topic/agenda; uses a generic summary like 'Meeting' or 'Synthera Meeting'.
    """
    generic_summary = summary or f"{BRAND} Meeting"
    lines = [
        "BEGIN:VCALENDAR",
        f"PRODID:-//{BRAND}//Calendar//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        f"METHOD:{method}",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_fmt(datetime.utcnow())}",
    ]
    if method != "CANCEL":
        lines += [
            f"DTSTART:{_fmt(start_utc)}",
            f"DTEND:{_fmt(end_utc)}",
            f"SUMMARY:{generic_summary}",
            "DESCRIPTION:",              # intentionally blank (no agenda)
            f"ORGANIZER:mailto:{organizer_email}",
            f"ATTENDEE;CN={attendee_email};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{attendee_email}",
            f"LOCATION:{location_url}",
            f"SEQUENCE:{sequence}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
        ]
    else:
        lines += [
            f"ORGANIZER:mailto:{organizer_email}",
            f"ATTENDEE;CN={attendee_email};ROLE=REQ-PARTICIPANT:mailto:{attendee_email}",
            f"SEQUENCE:{sequence}",
            "STATUS:CANCELLED",
        ]
    lines += ["END:VEVENT", "END:VCALENDAR", ""]
    return "\r\n".join(lines)

def _send_calendar_email(from_email, to_email, subject, html_body, ics_text):
    print(f"[EMAIL INVITE] Preparing to send calendar email: from={from_email}, to={to_email}, subject={subject}")
    logger.debug(f"Preparing to send calendar email: from={from_email}, to={to_email}, subject={subject}")
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html"))
        msg.attach(alt)

        method_is_cancel = "METHOD:CANCEL" in ics_text
        cal_method = "calendar;method=CANCEL" if method_is_cancel else "calendar;method=REQUEST"
        ics_part = MIMEText(ics_text, cal_method)
        ics_part.add_header("Content-Class", "urn:content-classes:calendarmessage")
        msg.attach(ics_part)

        print(f"[EMAIL INVITE] Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        logger.debug(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            print(f"[EMAIL INVITE] Logging in as: {SMTP_USERNAME or from_email}")
            logger.debug(f"Logging in as: {SMTP_USERNAME or from_email}")
            s.login(SMTP_USERNAME or from_email, SMTP_PASSWORD)
            print(f"[EMAIL INVITE] Sending email to: {to_email}")
            logger.debug(f"Sending email to: {to_email}")
            s.sendmail(from_email, [to_email], msg.as_string())
        print(f"[EMAIL INVITE] Calendar email sent successfully to {to_email}")
        logger.info(f"Calendar email sent successfully to {to_email}")
    except Exception as e:
        print(f"[EMAIL INVITE] Failed to send calendar email to {to_email}: {e}")
        logger.error(f"Failed to send calendar email to {to_email}: {e}")
        raise

# ========== Public helpers (NO topic/agenda in content) ==========

def send_created_invite(uid, organizer_email, attendee_email, attendee_name,
                                                join_url, start_utc, end_utc, from_email=None, subject=None, authorizer_name=None):
        from_email = from_email or organizer_email or DEFAULT_FROM
        subject = subject or f"{BRAND} Meeting Invite"
        signature = authorizer_name or organizer_email
        html = f"""
            <p>Hi {attendee_name},</p>
            <p>Your meeting is scheduled.</p>
            <p><b>When:</b> {start_utc.strftime('%Y-%m-%d %H:%M UTC')} – {end_utc.strftime('%H:%M UTC')}<br/>
                 <b>Join:</b> <a href=\"{join_url}\">{join_url}</a></p>
            <p>Thanks,<br/>{signature}</p>
        """
        ics = _build_ics(uid, "REQUEST", organizer_email, attendee_email,
                                         start_utc=start_utc, end_utc=end_utc, location_url=join_url, sequence=0)
        _send_calendar_email(from_email, attendee_email, subject, html, ics)

def send_updated_invite(uid, organizer_email, attendee_email, attendee_name,
                                                join_url, start_utc, end_utc, sequence=1, from_email=None, subject=None, authorizer_name=None):
        from_email = from_email or organizer_email or DEFAULT_FROM
        subject = subject or f"{BRAND} Meeting Updated"
        signature = authorizer_name or organizer_email
        html = f"""
            <p>Hi {attendee_name},</p>
            <p>Your meeting details have been updated.</p>
            <p><b>When:</b> {start_utc.strftime('%Y-%m-%d %H:%M UTC')} – {end_utc.strftime('%H:%M UTC')}<br/>
                 <b>Join:</b> <a href=\"{join_url}\">{join_url}</a></p>
            <p>Thanks,<br/>{signature}</p>
        """
        ics = _build_ics(uid, "REQUEST", organizer_email, attendee_email,
                                         start_utc=start_utc, end_utc=end_utc, location_url=join_url, sequence=sequence)
        _send_calendar_email(from_email, attendee_email, subject, html, ics)

def send_cancel_invite(uid, organizer_email, attendee_email, attendee_name,
                                             sequence=2, from_email=None, subject=None, authorizer_name=None):
        from_email = from_email or organizer_email or DEFAULT_FROM
        subject = subject or f"{BRAND} Meeting Cancelled"
        signature = authorizer_name or organizer_email
        html = f"""
            <p>Hi {attendee_name},</p>
            <p>Your meeting has been cancelled.</p>
            <p>Thanks,<br/>{signature}</p>
        """
        ics = _build_ics(uid, "CANCEL", organizer_email, attendee_email,
                                         start_utc=None, end_utc=None, location_url="", sequence=sequence)
        _send_calendar_email(from_email, attendee_email, subject, html, ics)

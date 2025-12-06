# com/dimcon/synthera/services/zoom_meeting_service.py
import json
import logging
from datetime import datetime, timedelta
import pytz
from com.dimcon.synthera.services.email_invite_service import send_created_invite, send_updated_invite, send_cancel_invite, DEFAULT_FROM

from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil

from com.dimcon.synthera.resources.integration.zoom_meeting_integration import ZoomMeetingIntegration
from com.dimcon.synthera.resources.meeting.meeting import Meeting
from com.dimcon.synthera.resources.leads.leads_details import LeadDetail
from com.dimcon.synthera.resources.projects.projects_lead import Project
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee

from .zoom_auth_service import ZoomAuthService, _zoom_request
from com.dimcon.synthera.services.email_invite_service import send_created_invite, send_updated_invite, send_cancel_invite

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

engine = get_engine()
db_util = DBSessionUtil(engine)


class ZoomMeetingService:
    # -----------------------------
    # ROUTE ENTRY (public): create / update / delete
    # -----------------------------
    @classmethod
    def route_create(cls, event):
        app_user_id = ZoomAuthService._resolve_app_user_id(event)
        if not app_user_id:
            return ResponseBuilder.build_response(401, {"error": "Unauthorized"})
        return cls.create(event, app_user_id)

    @classmethod
    def route_update(cls, event):
        app_user_id = ZoomAuthService._resolve_app_user_id(event)
        if not app_user_id:
            return ResponseBuilder.build_response(401, {"error": "Unauthorized"})
        mid = cls._extract_meeting_id(event)
        if not mid:
            return ResponseBuilder.build_response(400, {"error": "Missing meeting_id"})
        return cls.update(mid, event, app_user_id)

    @classmethod
    def route_delete(cls, event):
        app_user_id = ZoomAuthService._resolve_app_user_id(event)
        if not app_user_id:
            return ResponseBuilder.build_response(401, {"error": "Unauthorized"})
        mid = cls._extract_meeting_id(event)
        if not mid:
            return ResponseBuilder.build_response(400, {"error": "Missing meeting_id"})
        return cls.delete(mid, app_user_id)

    @classmethod
    def route_fetch(cls, event):
        return cls.fetch(event)

    # -----------------------------
    # CORE LOGIC (only for the 3 meeting ops)
    # -----------------------------
    @classmethod
    def create(cls, event, app_user_id):
        """
        Create a Zoom meeting, add the lead as a registrant, and persist to DB.
        Required JSON body keys:
          topic, scheduled_start_time(ISO), project_id, project_name,
          lead_id, lead_full_name, created_by, updated_by
        Optional: duration, agenda, status_id, integration_id, project_code
        """
        logger.info("Creating Zoom meeting for app_user_id: %s", app_user_id)

        try:
            body = json.loads(event.get("body") or "{}")
        except Exception:
            return ResponseBuilder.build_response(400, {"error": "Invalid JSON"})


        # Validate required fields except created_by/updated_by
        required = ["topic", "scheduled_start_time", "lead_id", "lead_full_name", "project_id", "project_name"]
        missing = [f for f in required if not body.get(f)]
        if missing:
            return ResponseBuilder.build_response(400, {"error": "Missing required fields", "fields": missing})

        # If created_by or updated_by missing, extract from Cognito claims and lookup emp_id
        if not body.get("created_by") or not body.get("updated_by"):
            claims = (event.get("requestContext", {}).get("authorizer", {}).get("claims") or {})
            email = claims.get("email")
            sub = claims.get("sub")
            emp = None
            with db_util.session_scope() as session:
                if email:
                    emp = session.query(Employee).filter_by(emp_org_email=email).first()
                if not emp and sub:
                    emp = session.query(Employee).filter_by(cognito_sub=sub).first()
                if emp:
                    if not body.get("created_by"):
                        body["created_by"] = emp.emp_id
                    if not body.get("updated_by"):
                        body["updated_by"] = emp.emp_id
                else:
                    return ResponseBuilder.build_response(400, {"error": "Could not resolve employee from Cognito claims"})

        with db_util.session_scope() as session:
            # Validate users
            if not session.query(Employee).filter_by(emp_id=body["created_by"]).first():
                return ResponseBuilder.build_response(400, {"error": "Invalid created_by emp_id"})
            if not session.query(Employee).filter_by(emp_id=body["updated_by"]).first():
                return ResponseBuilder.build_response(400, {"error": "Invalid updated_by emp_id"})

            # Validate project + lead (IDs authoritative; warn on name mismatch)
            project = session.query(Project).filter(Project.project_id == body["project_id"]).first()
            if not project:
                return ResponseBuilder.build_response(404, {"error": "Project not found"})
            if project.project_name and project.project_name.strip().lower() != body["project_name"].strip().lower():
                logger.warning("Project name mismatch for %s: '%s' vs '%s'",
                               project.project_id, project.project_name, body.get("project_name"))

            lead = session.query(LeadDetail).filter(LeadDetail.lead_id == body["lead_id"]).first()
            if not lead:
                return ResponseBuilder.build_response(404, {"error": "Lead not found"})
            if lead.lead_full_name.strip().lower() != body["lead_full_name"].strip().lower():
                logger.warning("Lead name mismatch for %s: '%s' vs '%s'",
                               lead.lead_id, lead.lead_full_name, body.get("lead_full_name"))

            # Conflict check (same lead at same time)
            scheduled_start_time, scheduled_end_time = _normalize_times(
                body["scheduled_start_time"], body.get("duration", 30)
            )
            exists = session.query(Meeting).filter(
                Meeting.scheduled_start_time == scheduled_start_time,
                Meeting.lead_id == body["lead_id"],
            ).first()
            if exists:
                return ResponseBuilder.build_response(409, {"error": "Meeting already scheduled for this lead at that time"})

            # Zoom API: create meeting
            access_token, zoom_user_id = ZoomAuthService.get_access_token_and_user(app_user_id)
            payload = {
                "topic": body["topic"],
                "type": 2,
                "start_time": scheduled_start_time.isoformat(),
                "duration": body.get("duration", 30),
                "timezone": "UTC",
                "agenda": body.get("agenda", ""),
                "settings": {
                    "join_before_host": True,
                    "mute_upon_entry": True,
                    "approval_type": 0,
                    "registration_type": 1,
                    "registrants_email_notification": True
                }
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            url = f"https://api.zoom.us/v2/users/{zoom_user_id}/meetings"

            r = _zoom_request("POST", url, headers=headers, json=payload)
            if r.status_code == 401:
                headers["Authorization"] = f"Bearer {ZoomAuthService._refresh_access_token(app_user_id)}"
                r = _zoom_request("POST", url, headers=headers, json=payload)
            r.raise_for_status()
            zm = r.json()

            # Ensure registration is on, then add registrant (lead)
            chk = _zoom_request("GET", f"https://api.zoom.us/v2/meetings/{zm['id']}", headers=headers)
            chk.raise_for_status()
            if not chk.json().get("registration_url"):
                logger.warning("Registration not enabled for meeting %s", zm["id"])

            registrant = None
            try:
                registrant = cls._add_registrant(zm["id"], lead.email, lead.lead_full_name, app_user_id)
            except Exception as e:
                logger.warning("Failed to add registrant: %s", e)

            join_url = (registrant or {}).get("join_url") or zm.get("join_url")

            # Persist integration + meeting
            ZoomMeetingIntegration.insert_table(
                meeting_id=zm["id"],
                host_url=zm.get("start_url"),
                join_url=join_url,
                start_url=zm.get("start_url"),
                meeting_password=zm.get("password"),
                meeting_topic=zm.get("topic"),
                meeting_agenda=body.get("agenda", ""),
                start_time=scheduled_start_time,
                duration_minutes=body.get("duration"),
                timezone="UTC",
                status_id=body.get("status_id"),
                integration_id=body.get("integration_id"),
                created_by=body.get("created_by"),
                updated_by=body.get("updated_by"),
                app_user_id=app_user_id,
                project_id=body.get("project_id"),
                project_code=body.get("project_code"),
            )

            meeting = Meeting(
                meeting_title=body["topic"],
                meeting_description=body.get("agenda", "Zoom Meeting Scheduled"),
                meeting_type_id=1,
                meeting_priority_id=1,
                lead_id=body["lead_id"],
                lead_full_name=body["lead_full_name"],
                scheduled_start_time=scheduled_start_time,
                scheduled_end_time=scheduled_end_time,
                scheduled_at=datetime.now(pytz.utc),
                meeting_link=join_url,
                created_by=body["created_by"],
                updated_by=body["updated_by"],
                created_at=datetime.now(pytz.utc),
                updated_at=datetime.now(pytz.utc),
                project_id=body["project_id"],
                project_name=body["project_name"],
            )
            session.add(meeting)
            session.commit()
            session.refresh(meeting)

            # Send email invite to lead after meeting creation
            try:
                # from_email is now a module-level variable
                print(f"[EMAIL INVITE DIAG] lead object: {lead}")
                print(f"[EMAIL INVITE DIAG] emp object: {emp}")
                attendee_email = getattr(lead, "email", None)
                attendee_name = getattr(lead, "lead_full_name", DEFAULT_FROM)
                organizer_email = DEFAULT_FROM
                # Get authorizer name from Cognito claims
                claims = (event.get("requestContext", {}).get("authorizer", {}).get("claims") or {})
                authorizer_name = claims.get("name") or claims.get("email") or claims.get("cognito:username") or DEFAULT_FROM
                if attendee_email:
                    print(f"[EMAIL INVITE DIAG] Sending invite from {DEFAULT_FROM} to lead {attendee_email}")
                    send_created_invite(
                        uid=str(zm["id"]),
                        organizer_email=organizer_email,
                        attendee_email=attendee_email,
                        attendee_name=attendee_name,
                        join_url=join_url,
                        start_utc=scheduled_start_time,
                        end_utc=scheduled_end_time,
                        from_email=DEFAULT_FROM,
                        authorizer_name=authorizer_name
                    )
                else:
                    print(f"[EMAIL INVITE DIAG] No lead email found, not sending invite.")
            except Exception as e:
                print(f"[EMAIL INVITE DIAG] Exception: {e}")
                logger.error(f"Failed to send invite email: {e}")
            return ResponseBuilder.build_response(201, {
                "message": "Zoom Meeting created successfully.",
                "data": {
                    "zoom_meeting_id": zm.get("id"),
                    "zoom_join_url": join_url,
                    "meeting_topic": zm.get("topic"),
                    "start_time": zm.get("start_time"),
                    "duration": zm.get("duration"),
                    "timezone": zm.get("timezone", "UTC"),
                    "meeting_id_in_db": meeting.meeting_id,
                },
            })

    @classmethod
    def update(cls, meeting_id, event, app_user_id):
        try:
            body = json.loads(event.get("body") or "{}")
        except Exception:
            return ResponseBuilder.build_response(400, {"error": "Invalid JSON"})

        access_token, _ = ZoomAuthService.get_access_token_and_user(app_user_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://api.zoom.us/v2/meetings/{meeting_id}"

        r = _zoom_request("PATCH", url, headers=headers, json=body)
        if r.status_code == 401:
            headers["Authorization"] = f"Bearer {ZoomAuthService._refresh_access_token(app_user_id)}"
            r = _zoom_request("PATCH", url, headers=headers, json=body)
        logger.debug("Zoom PATCH /meetings/%s -> %s %s", meeting_id, r.status_code, r.text)
        r.raise_for_status()

        # Zoom returns 204 No Content for success; sync DB if needed
        if r.status_code == 204:
            with db_util.session_scope() as session:
                # Prefer using integration table by meeting_id
                integ = session.query(ZoomMeetingIntegration).filter_by(meeting_id=meeting_id).first()
                m = None
                if integ:
                    m = session.query(Meeting).filter(Meeting.meeting_link == integ.join_url).first()
                # Update Meeting table
                if m:
                    if "start_time" in body:
                        m.scheduled_start_time = _parse_iso(body["start_time"])
                    if "topic" in body:
                        m.meeting_title = body["topic"]
                    if "agenda" in body:
                        m.meeting_description = body["agenda"]
                    if "duration" in body and m.scheduled_start_time:
                        m.scheduled_end_time = m.scheduled_start_time + timedelta(minutes=body["duration"])
                # Update ZoomMeetingIntegration table
                if integ:
                    if "start_time" in body:
                        integ.start_time = _parse_iso(body["start_time"])
                    if "topic" in body:
                        integ.meeting_topic = body["topic"]
                    if "agenda" in body:
                        integ.meeting_agenda = body["agenda"]
                    if "duration" in body:
                        integ.duration_minutes = body["duration"]
                if m or integ:
                    session.commit()
                # Send updated invite email
                try:
                    # Deep debug for update invite logic
                    if m:
                        print("[DEEP DEBUG] Meeting object found:", m)
                        # Always get attendee email from LeadDetail using lead_id
                        lead = session.query(LeadDetail).filter_by(lead_id=m.lead_id).first()
                        attendee_email = getattr(lead, "email", None) if lead else None
                        attendee_name = getattr(m, "lead_full_name", DEFAULT_FROM)
                        organizer_email = DEFAULT_FROM
                        join_url = getattr(m, "meeting_link", None)
                        start_utc = getattr(m, "scheduled_start_time", None)
                        end_utc = getattr(m, "scheduled_end_time", None)
                        print(f"[DEEP DEBUG] attendee_email: {attendee_email}")
                        print(f"[DEEP DEBUG] attendee_name: {attendee_name}")
                        print(f"[DEEP DEBUG] organizer_email: {organizer_email}")
                        print(f"[DEEP DEBUG] join_url: {join_url}")
                        print(f"[DEEP DEBUG] start_utc: {start_utc}")
                        print(f"[DEEP DEBUG] end_utc: {end_utc}")
                        if attendee_email and organizer_email and join_url and start_utc and end_utc:
                            print("[DEEP DEBUG] All fields present, sending updated invite...")
                            send_updated_invite(
                                uid=str(meeting_id),
                                organizer_email=organizer_email,
                                attendee_email=attendee_email,
                                attendee_name=attendee_name,
                                join_url=join_url,
                                start_utc=start_utc,
                                end_utc=end_utc,
                                sequence=1,
                                from_email=DEFAULT_FROM,
                                authorizer_name=organizer_email
                            )
                        else:
                            print("[DEEP DEBUG] Missing field(s), invite not sent.")
                    else:
                        print("[DEEP DEBUG] No meeting object found for meeting_id:", meeting_id)
                except Exception as e:
                    logger.error(f"Failed to send updated invite email: {e}")
            return ResponseBuilder.build_response(200, {"message": "Meeting updated successfully"})

        # If Zoom sent a body, return it
        try:
            return ResponseBuilder.build_response(200, r.json())
        except Exception:
            return ResponseBuilder.build_response(200, {"message": "Meeting updated"})

    @classmethod
    def delete(cls, meeting_id, app_user_id):
        access_token, _ = ZoomAuthService.get_access_token_and_user(app_user_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://api.zoom.us/v2/meetings/{meeting_id}"

        r = _zoom_request("DELETE", url, headers=headers)
        if r.status_code == 401:
            headers["Authorization"] = f"Bearer {ZoomAuthService._refresh_access_token(app_user_id)}"
            r = _zoom_request("DELETE", url, headers=headers)
        if r.status_code not in (200, 204):
            r.raise_for_status()

        with db_util.session_scope() as session:
            session.query(ZoomMeetingIntegration).filter_by(meeting_id=meeting_id).delete()
            # If you store zoom_meeting_id on Meeting, delete by that; otherwise best-effort by join_url mapping
            deleted_meetings = session.query(Meeting).filter(Meeting.meeting_link.like(f"%{meeting_id}%")).all()
            # from_email is now a module-level variable
            for m in deleted_meetings:
                # Send cancel invite email before deleting
                try:
                    # Always get attendee email from LeadDetail using lead_id
                    lead = session.query(LeadDetail).filter_by(lead_id=m.lead_id).first()
                    attendee_email = getattr(lead, "email", None) if lead else None
                    attendee_name = getattr(m, "lead_full_name", DEFAULT_FROM)
                    organizer_email = DEFAULT_FROM
                    if attendee_email and organizer_email:
                        send_cancel_invite(
                            uid=str(meeting_id),
                            organizer_email=organizer_email,
                            attendee_email=attendee_email,
                            attendee_name=attendee_name,
                            sequence=2,
                            from_email=DEFAULT_FROM,
                            authorizer_name=organizer_email
                        )
                except Exception as e:
                    logger.error(f"Failed to send cancel invite email: {e}")
            session.query(Meeting).filter(Meeting.meeting_link.like(f"%{meeting_id}%")).delete()
            session.commit()

        return ResponseBuilder.build_response(200, {"message": "Meeting deleted successfully from Zoom and database."})

    @classmethod
    def fetch(cls, event):
        """
        Fetch all Zoom meeting records for the authenticated user.
        Resolves the user's emp_id from Cognito claims and returns only meetings created by that user.
        """
        logger.info("Fetching Zoom meetings")

        # Extract Cognito claims to resolve emp_id (same pattern as create method)
        claims = (event.get("requestContext", {}).get("authorizer", {}).get("claims") or {})
        email = claims.get("email")
        sub = claims.get("sub")
        
        emp = None
        with db_util.session_scope() as session:
            if email:
                emp = session.query(Employee).filter_by(emp_org_email=email).first()
            if not emp and sub:
                emp = session.query(Employee).filter_by(cognito_sub=sub).first()
            
            if not emp:
                return ResponseBuilder.build_response(400, {"error": "Could not resolve employee from Cognito claims"})
            
            # Fetch zoom meeting integration records where created_by matches the user's emp_id
            zoom_meetings = session.query(ZoomMeetingIntegration).filter_by(created_by=emp.emp_id).all()
            
            # Convert to list of dictionaries
            meetings_data = [meeting.to_dict() for meeting in zoom_meetings]
            
            logger.info("Found %d Zoom meetings for user emp_id: %s", len(meetings_data), emp.emp_id)
            
            return ResponseBuilder.build_response(200, {
                "message": "Zoom meetings fetched successfully",
                "data": meetings_data,
                "count": len(meetings_data)
            })

    # -----------------------------
    # Helpers
    # -----------------------------
    @staticmethod
    def _extract_meeting_id(event):
        # Prefer JSON body
        try:
            body = json.loads(event.get("body") or "{}")
            mid = body.get("meeting_id")
            if mid:
                return str(mid).strip()
        except Exception:
            pass
        # Optionally parse from resource if your API Gateway uses /zoom/meeting/{id}
        rp = (event.get("resource") or "").rstrip("/")
        if "/zoom/meeting/" in rp:
            try:
                return rp.rsplit("/zoom/meeting/", 1)[1].split("/", 1)[0]
            except Exception:
                pass
        return None

    @staticmethod
    def _add_registrant(meeting_id, email, full_name, app_user_id):
        access_token, _ = ZoomAuthService.get_access_token_and_user(app_user_id)
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        url = f"https://api.zoom.us/v2/meetings/{meeting_id}/registrants"
        first, *rest = (full_name or "").split(" ", 1)
        last = rest[0] if rest else ""
        r = _zoom_request("POST", url, headers=headers,
                          json={"email": email, "first_name": first or email.split("@")[0], "last_name": last})
        if r.status_code == 401:
            headers["Authorization"] = f"Bearer {ZoomAuthService._refresh_access_token(app_user_id)}"
            r = _zoom_request("POST", url, headers=headers,
                              json={"email": email, "first_name": first or email.split("@")[0], "last_name": last})
        r.raise_for_status()
        return r.json()

# -----------------------------
# Module-level helpers
# -----------------------------
def _parse_iso(dt_str: str) -> datetime:
    s = (dt_str or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)

def _normalize_times(start_iso: str, duration_min: int = 30):
    dt = _parse_iso(start_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    start = dt.astimezone(pytz.utc)
    end = start + timedelta(minutes=duration_min or 30)
    return start, end

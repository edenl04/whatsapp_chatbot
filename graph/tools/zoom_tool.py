from typing import Dict, Any, Optional, List, Union, ClassVar, Tuple
from datetime import datetime, timedelta

import pyshorteners
from langchain.tools import BaseTool
from dotenv import load_dotenv
import os
import requests
import json


load_dotenv()

class ZoomTool(BaseTool):
    """Tool for creating and managing Zoom meetings with conflict detection"""
    
    name: ClassVar[str] = "zoom_meeting_creator"
    description: ClassVar[str] = """Create a new meeting and check for conflicts.
    Input should be a JSON object with meeting details including:
    - start_time: ISO format date/time (YYYY-MM-DDTHH:MM:SS)
    - duration: Meeting length in minutes (default: 30)
    - agenda: Optional meeting description
    - password: Optional meeting password
    """

    return_direct: ClassVar[bool] = True

    def _run(self, meeting_details: Union[Dict[str, Any], str]) -> Union[Dict[str, Any], str]:
        """Create a Zoom meeting after checking for conflicts"""
        try:
            # Parse JSON string if provided
            if isinstance(meeting_details, str):
                try:
                    meeting_details = json.loads(meeting_details)
                except json.JSONDecodeError:
                    return "Error: Invalid JSON input"

            # Extract parameters
            meeting_params = {}
            for key in ["topic", "start_time", "duration", "agenda", "password"]:
                if key in meeting_details:
                    meeting_params[key] = meeting_details[key]

            # Validate required parameters
            if "topic" not in meeting_params:
                meeting_params["topic"] = "meeting"
            if "start_time" not in meeting_params:
                return "Error: Missing required field 'start_time'"

            # Set default duration if not provided
            if "duration" not in meeting_params:
                meeting_params["duration"] = 30

            # Check for meeting conflicts
            has_conflict, conflict_details = self._check_conflicts(meeting_params["start_time"], meeting_params["duration"])
            if has_conflict:
                conflict_time = conflict_details.get("start_time", "unknown time")
                conflict_topic = conflict_details.get("topic", "Untitled meeting")
                conflict_duration = conflict_details.get("duration", "unknown duration")

                return {
                    "success": False,
                    "error": "Scheduling conflict detected",
                    "message": f"Sorry, there is a meeting already occurring during this time: '{conflict_topic}' at {conflict_time} (duration: {conflict_duration} minutes)",
                    "conflict_details": conflict_details
                }

            # Create the meeting
            result = self._create_zoom_meeting(meeting_params)
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "message": f"Error creating meeting: {result['error']}"
                }
            url_meeting = result.get("start_url")
            try:
                shortener = pyshorteners.Shortener()
                url_meeting = shortener.tinyurl.short(result.get("start_url"))
            except:
                print("can't create a shorter link")

            # Format the successful response
            return {
                "success": True,
                "message": f"Meeting '{meeting_params['topic']}' created successfully!",
                "meeting_id": result.get("id"),
                "join_url": url_meeting,
                # "start_url": result.get("start_url"), a link that people can enter as a hosts
                # "join_url": result.get("join_url"), a link that enter people as participant
                "password": result.get("password", "No password set"),
                # "app_url": f"zoommtg://zoom.us/join?confno={result.get('id')}&pwd={result.get('password', '')}",
                "start_time": meeting_params["start_time"],
                "duration": f"{meeting_params['duration']} minutes"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error: {str(e)}"
            }

    def _check_conflicts(self, start_time: str, duration: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if there are any meeting conflicts with the proposed time

        Returns:
            Tuple containing:
            - Boolean indicating if conflict exists
            - Dictionary with conflict details (or None if no conflict)
        """
        try:
            # Parse the proposed meeting time
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(minutes=duration)

            # Get list of existing meetings
            meetings = self._list_meetings()

            if not meetings:
                print("No existing meetings found")
                return False, None

            print(f"Checking for conflicts: Proposed meeting {start_dt} to {end_dt}")
            print(f"Found {len(meetings)} existing meetings to check against")

            # Check for overlaps
            for meeting in meetings:
                # Extract meeting times
                meeting_start_str = meeting.get("start_time")
                meeting_duration = meeting.get("duration", 60)  # Default to 60 minutes if not specified

                if not meeting_start_str:
                    print(f"Warning: Meeting {meeting.get('id', 'unknown')} has no start time")
                    continue

                # Parse meeting time
                try:
                    meeting_start = datetime.fromisoformat(meeting_start_str.replace('Z', '+00:00'))
                    meeting_end = meeting_start + timedelta(minutes=meeting_duration)

                    # Debug info
                    print(f"Checking conflict with: {meeting.get('topic')} ({meeting_start} to {meeting_end})")

                    # Check for overlap using the standard interval overlap test:
                    # Two intervals overlap if one starts before the other ends and ends after the other starts
                    if (start_dt < meeting_end and end_dt > meeting_start):
                        print(f"Conflict detected: {meeting.get('topic')} overlaps with proposed meeting")
                        return True, meeting
                except Exception as parsing_error:
                    print(f"Error parsing meeting time '{meeting_start_str}': {str(parsing_error)}")
                    continue

            # No conflicts found
            print("No conflicts found")
            return False, None

        except Exception as e:
            print(f"Error checking conflicts: {str(e)}")
            # Return True for safety - better to prevent a potential conflict
            return True, {"topic": "Unknown meeting", "start_time": "unknown", "error": str(e)}

    def _list_meetings(self) -> List[Dict[str, Any]]:
        """Get a list of upcoming Zoom meetings"""
        try:
            # Get access token
            token = self._get_access_token()
            if not token:
                print("Failed to get access token")
                return []

            # Calculate date range (next 30 days)
            now = datetime.now()
            from_date = now.strftime("%Y-%m-%d")
            to_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")

            # Set up API request
            url = "https://api.zoom.us/v2/users/me/meetings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "type": "scheduled",
                "page_size": 100,
                "from": from_date,
                "to": to_date
            }

            # Send the request
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                meetings = response.json().get("meetings", [])
                print(f"Retrieved {len(meetings)} meetings from Zoom API")
                return meetings
            else:
                print(f"Error listing meetings: {response.status_code}, {response.text}")
                return []

        except Exception as e:
            print(f"Error listing meetings: {str(e)}")
            return []

    def _create_zoom_meeting(self, meeting_params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Zoom meeting via API"""
        try:
            # Double-check for conflicts before creating meeting
            has_conflict, conflict_details = self._check_conflicts(meeting_params["start_time"], meeting_params["duration"])
            if has_conflict:
                return {
                    "error": f"Conflict detected with meeting '{conflict_details.get('topic', 'Untitled')}' at {conflict_details.get('start_time', 'unknown time')}"
                }

            # Get access token
            token = self._get_access_token()
            if not token:
                return {"error": "Failed to get access token"}

            # Prepare meeting data
            meeting_data = {
                "topic": meeting_params["topic"],
                "type": 1,  # Scheduled meeting
                "start_time": meeting_params["start_time"],
                "duration": meeting_params["duration"],
                "timezone": "UTC",
                "settings": {
                    "join_before_host": True,
                    "waiting_room": False,
                    "auto_recording": "none"
                }
            }
            
            # Add optional parameters if provided
            if "agenda" in meeting_params and meeting_params["agenda"]:
                meeting_data["agenda"] = meeting_params["agenda"]
                
            if "password" in meeting_params and meeting_params["password"]:
                meeting_data["password"] = meeting_params["password"]
                
            # Set up API request
            url = "https://api.zoom.us/v2/users/me/meetings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Send the request
            response = requests.post(url, headers=headers, json=meeting_data)
            
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": f"API error {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Exception: {str(e)}"}
    
    def _get_access_token(self) -> Optional[str]:
        """Get Zoom API OAuth access token"""
        try:
            # Get credentials from environment
            client_id = os.getenv("ZOOM_CLIENT_ID")
            client_secret = os.getenv("ZOOM_CLIENT_SECRET")
            account_id = os.getenv("ZOOM_ACCOUNT_ID")
            
            if not (client_id and client_secret and account_id):
                print("Missing Zoom API credentials in environment variables")
                return None
                
            # Set up token request
            url = "https://zoom.us/oauth/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "account_credentials",
                "account_id": account_id
            }
            
            # Send request
            response = requests.post(
                url,
                auth=(client_id, client_secret),
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                print(f"Failed to get access token: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting token: {str(e)}")
            return None 
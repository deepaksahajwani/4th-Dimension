"""
Smart WhatsApp Forwarding System
Handles incoming WhatsApp messages and forwards them to relevant project team members

Flow:
1. Receive incoming WhatsApp message via Twilio webhook
2. Identify sender by phone number
3. Find associated projects
4. If multiple projects, ask user to select
5. Allow sender to choose recipients from project participants
6. Forward message to selected recipients
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from notification_service import notification_service
import httpx

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# App URL
APP_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://mobile-first-14.preview.emergentagent.com')

# Conversation states
CONVERSATION_STATES = {}  # In-memory state (consider Redis for production)


class ConversationState:
    """Track conversation state for multi-step interactions"""
    
    IDLE = "idle"
    SELECTING_PROJECT = "selecting_project"
    SELECTING_RECIPIENTS = "selecting_recipients"
    CONFIRMING_FORWARD = "confirming_forward"
    
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.state = self.IDLE
        self.projects = []  # Available projects
        self.selected_project = None
        self.participants = []  # Available participants
        self.selected_recipients = []
        self.pending_message = None  # Message waiting to be forwarded
        self.pending_media_url = None  # Media URL if voice note
        self.last_activity = datetime.now(timezone.utc)
        self.sender_info = None  # Sender's user info
    
    def is_expired(self) -> bool:
        """Check if conversation state has expired (30 min timeout)"""
        return datetime.now(timezone.utc) - self.last_activity > timedelta(minutes=30)
    
    def reset(self):
        """Reset conversation state"""
        self.state = self.IDLE
        self.projects = []
        self.selected_project = None
        self.participants = []
        self.selected_recipients = []
        self.pending_message = None
        self.pending_media_url = None
        self.last_activity = datetime.now(timezone.utc)


def get_conversation_state(phone_number: str) -> ConversationState:
    """Get or create conversation state for a phone number"""
    # Normalize phone number
    phone = normalize_phone(phone_number)
    
    if phone not in CONVERSATION_STATES or CONVERSATION_STATES[phone].is_expired():
        CONVERSATION_STATES[phone] = ConversationState(phone)
    
    state = CONVERSATION_STATES[phone]
    state.last_activity = datetime.now(timezone.utc)
    return state


def normalize_phone(phone: str) -> str:
    """Normalize phone number for comparison"""
    # Remove whatsapp: prefix if present
    if phone.startswith('whatsapp:'):
        phone = phone[9:]
    # Remove + and spaces
    phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    return phone


async def find_sender_info(phone_number: str) -> Optional[Dict]:
    """Find sender info from users, clients, contractors, or consultants"""
    phone = normalize_phone(phone_number)
    
    # Search in multiple collections
    collections = ['users', 'clients', 'contractors', 'consultants']
    
    for collection in collections:
        # Try different phone field names
        for field in ['mobile', 'phone']:
            query = {field: {"$regex": phone[-10:], "$options": "i"}}
            person = await db[collection].find_one(query, {"_id": 0})
            if person:
                person['_collection'] = collection
                return person
    
    return None


async def find_projects_for_sender(sender_info: Dict) -> List[Dict]:
    """Find all projects associated with the sender"""
    projects = []
    sender_id = sender_info.get('id')
    sender_collection = sender_info.get('_collection')
    
    if not sender_id:
        return projects
    
    # Build query based on sender type
    if sender_collection == 'clients':
        # Client - find projects where they are the client
        cursor = db.projects.find({"client_id": sender_id}, {"_id": 0})
        async for project in cursor:
            projects.append(project)
    
    elif sender_collection == 'users':
        role = sender_info.get('role', '')
        
        if sender_info.get('is_owner'):
            # Owner can see all active projects
            cursor = db.projects.find({"status": {"$ne": "archived"}}, {"_id": 0}).limit(20)
            async for project in cursor:
                projects.append(project)
        else:
            # Team member - find projects where they are team leader
            cursor = db.projects.find({"team_leader_id": sender_id}, {"_id": 0})
            async for project in cursor:
                projects.append(project)
    
    elif sender_collection in ['contractors', 'consultants']:
        # Contractor/Consultant - find projects where they are assigned
        field = "assigned_contractors" if sender_collection == 'contractors' else "assigned_consultants"
        cursor = db.projects.find({}, {"_id": 0})
        async for project in cursor:
            assigned = project.get(field, {})
            if isinstance(assigned, dict) and sender_id in assigned.values():
                projects.append(project)
            elif isinstance(assigned, list) and sender_id in assigned:
                projects.append(project)
    
    return projects


async def get_project_participants(project: Dict) -> List[Dict]:
    """Get all participants of a project"""
    participants = []
    
    # Get owner
    owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
    if owner:
        participants.append({
            "id": owner['id'],
            "name": owner['name'],
            "role": "Owner",
            "phone": owner.get('mobile'),
            "type": "owner"
        })
    
    # Get team leader
    if project.get('team_leader_id'):
        team_leader = await db.users.find_one({"id": project['team_leader_id']}, {"_id": 0})
        if team_leader:
            participants.append({
                "id": team_leader['id'],
                "name": team_leader['name'],
                "role": "Team Leader",
                "phone": team_leader.get('mobile'),
                "type": "team_leader"
            })
    
    # Get client
    if project.get('client_id'):
        client = await db.clients.find_one({"id": project['client_id']}, {"_id": 0})
        if not client:
            client = await db.users.find_one({"id": project['client_id']}, {"_id": 0})
        if client:
            participants.append({
                "id": client['id'],
                "name": client.get('name', client.get('contact_person', 'Client')),
                "role": "Client",
                "phone": client.get('phone', client.get('mobile')),
                "type": "client"
            })
    
    # Get assigned contractors
    assigned_contractors = project.get('assigned_contractors', {})
    if isinstance(assigned_contractors, dict):
        for contractor_type, contractor_id in assigned_contractors.items():
            contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
            if not contractor:
                contractor = await db.users.find_one({"id": contractor_id}, {"_id": 0})
            if contractor:
                participants.append({
                    "id": contractor['id'],
                    "name": contractor.get('name', 'Contractor'),
                    "role": f"{contractor_type} Contractor",
                    "phone": contractor.get('phone', contractor.get('mobile')),
                    "type": "contractor"
                })
    
    # Get assigned consultants
    assigned_consultants = project.get('assigned_consultants', {})
    if isinstance(assigned_consultants, dict):
        for consultant_type, consultant_id in assigned_consultants.items():
            consultant = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
            if not consultant:
                consultant = await db.users.find_one({"id": consultant_id}, {"_id": 0})
            if consultant:
                participants.append({
                    "id": consultant['id'],
                    "name": consultant.get('name', 'Consultant'),
                    "role": f"{consultant_type} Consultant",
                    "phone": consultant.get('phone', consultant.get('mobile')),
                    "type": "consultant"
                })
    
    # Remove duplicates based on id
    seen_ids = set()
    unique_participants = []
    for p in participants:
        if p['id'] not in seen_ids:
            seen_ids.add(p['id'])
            unique_participants.append(p)
    
    return unique_participants


async def forward_message_to_recipients(
    sender_name: str,
    project_name: str,
    message: str,
    recipients: List[Dict],
    media_url: Optional[str] = None,
    is_voice_note: bool = False
):
    """Forward message to selected recipients"""
    
    # Format the forwarded message
    if is_voice_note:
        forward_text = f"""📱 *Forwarded Voice Note*

👤 *From:* {sender_name}
📁 *Project:* {project_name}
🎤 *Voice Message* attached

{f'📝 Message: {message}' if message else ''}

---
_Forwarded via 4D WhatsApp System_"""
    else:
        forward_text = f"""📱 *Forwarded Message*

👤 *From:* {sender_name}
📁 *Project:* {project_name}

💬 *Message:*
{message}

---
_Forwarded via 4D WhatsApp System_"""
    
    results = []
    for recipient in recipients:
        phone = recipient.get('phone')
        if not phone:
            logger.warning(f"No phone number for recipient: {recipient.get('name')}")
            continue
        
        try:
            if media_url and is_voice_note:
                # Send voice note with message
                result = await send_whatsapp_with_media(phone, forward_text, media_url)
            else:
                # Send text only
                result = await notification_service.send_whatsapp(phone, forward_text)
            
            results.append({
                "recipient": recipient.get('name'),
                "success": result.get('success', False)
            })
            
            if result.get('success'):
                logger.info(f"Forwarded message to {recipient.get('name')}")
            else:
                logger.warning(f"Failed to forward to {recipient.get('name')}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error forwarding to {recipient.get('name')}: {str(e)}")
            results.append({
                "recipient": recipient.get('name'),
                "success": False,
                "error": str(e)
            })
    
    return results


async def send_whatsapp_with_media(phone_number: str, message: str, media_url: str) -> Dict:
    """Send WhatsApp message with media attachment"""
    try:
        TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        # Format phone number
        if not phone_number.startswith('whatsapp:'):
            phone_number = phone_number.strip()
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            phone_number = f"whatsapp:{phone_number}"
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        
        data = {
            "From": TWILIO_WHATSAPP_FROM,
            "To": phone_number,
            "Body": message,
            "MediaUrl": media_url
        }
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                data=data,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get('sid'),
                    "status": result.get('status')
                }
            else:
                return {"success": False, "error": response.text}
                
    except Exception as e:
        logger.error(f"WhatsApp with media error: {str(e)}")
        return {"success": False, "error": str(e)}


async def handle_incoming_whatsapp(
    from_number: str,
    body: str,
    num_media: int = 0,
    media_url: Optional[str] = None,
    media_content_type: Optional[str] = None
) -> str:
    """
    Main handler for incoming WhatsApp messages
    Returns response message to send back to user
    """
    try:
        state = get_conversation_state(from_number)
        
        # Check for cancel command
        if body.lower().strip() in ['cancel', 'exit', 'quit', '0']:
            state.reset()
            return "❌ Operation cancelled. Send any message to start again."
        
        # Find sender info if not cached
        if not state.sender_info:
            state.sender_info = await find_sender_info(from_number)
        
        # Handle based on current state
        if state.state == ConversationState.IDLE:
            return await handle_idle_state(state, body, num_media, media_url, media_content_type)
        
        elif state.state == ConversationState.SELECTING_PROJECT:
            return await handle_project_selection(state, body)
        
        elif state.state == ConversationState.SELECTING_RECIPIENTS:
            return await handle_recipient_selection(state, body)
        
        elif state.state == ConversationState.CONFIRMING_FORWARD:
            return await handle_forward_confirmation(state, body)
        
        else:
            state.reset()
            return "Something went wrong. Please try again."
            
    except Exception as e:
        logger.error(f"Error handling incoming WhatsApp: {str(e)}")
        return "Sorry, an error occurred. Please try again later."


async def handle_idle_state(
    state: ConversationState,
    body: str,
    num_media: int,
    media_url: Optional[str],
    media_content_type: Optional[str]
) -> str:
    """Handle messages when in idle state"""
    
    # Store the incoming message
    state.pending_message = body
    
    # Check if it's a voice note
    is_voice = num_media > 0 and media_content_type and 'audio' in media_content_type.lower()
    if is_voice and media_url:
        state.pending_media_url = media_url
    
    # If sender not found, ask them to register
    if not state.sender_info:
        return """👋 Welcome to 4th Dimension WhatsApp!

We couldn't find your phone number in our system. 

To use this feature, please ensure you're registered with us using this phone number.

Contact us at contact@4thdimensionarchitect.com for assistance."""
    
    sender_name = state.sender_info.get('name', 'User')
    
    # Find projects for this sender
    projects = await find_projects_for_sender(state.sender_info)
    
    if not projects:
        return f"""👋 Hi {sender_name}!

You don't have any active projects at the moment.

If you believe this is an error, please contact us at contact@4thdimensionarchitect.com"""
    
    if len(projects) == 1:
        # Auto-select single project
        state.selected_project = projects[0]
        state.participants = await get_project_participants(projects[0])
        state.state = ConversationState.SELECTING_RECIPIENTS
        
        return await format_recipient_selection(state, sender_name)
    
    else:
        # Multiple projects - ask user to select
        state.projects = projects
        state.state = ConversationState.SELECTING_PROJECT
        
        project_list = "\n".join([
            f"{i+1}. {p.get('title', p.get('name', 'Untitled'))}"
            for i, p in enumerate(projects)
        ])
        
        return f"""👋 Hi {sender_name}!

📁 *Select a Project*

You have {len(projects)} active projects:

{project_list}

Reply with the *number* of the project you want to message about.

Send *0* to cancel."""


async def handle_project_selection(state: ConversationState, body: str) -> str:
    """Handle project selection response"""
    try:
        selection = int(body.strip())
        
        if selection < 1 or selection > len(state.projects):
            return f"Please enter a number between 1 and {len(state.projects)}, or 0 to cancel."
        
        state.selected_project = state.projects[selection - 1]
        state.participants = await get_project_participants(state.selected_project)
        state.state = ConversationState.SELECTING_RECIPIENTS
        
        sender_name = state.sender_info.get('name', 'User')
        return await format_recipient_selection(state, sender_name)
        
    except ValueError:
        return "Please enter a valid number."


async def format_recipient_selection(state: ConversationState, sender_name: str) -> str:
    """Format the recipient selection message"""
    project_name = state.selected_project.get('title', state.selected_project.get('name', 'Project'))
    
    # Filter out the sender from participants
    sender_id = state.sender_info.get('id')
    available_participants = [p for p in state.participants if p['id'] != sender_id]
    
    if not available_participants:
        state.reset()
        return f"No other participants found for project '{project_name}'."
    
    participant_list = "\n".join([
        f"{i+1}. {p['name']} ({p['role']})"
        for i, p in enumerate(available_participants)
    ])
    
    # Store filtered participants
    state.participants = available_participants
    
    message_preview = state.pending_message[:50] + "..." if len(state.pending_message or '') > 50 else (state.pending_message or '[Voice Note]')
    
    return f"""📁 *Project:* {project_name}

📨 *Your message:*
"{message_preview}"

👥 *Select Recipients:*

{participant_list}

*A* - Send to ALL
*T* - Send to Team Leader & Owner only

Or reply with numbers separated by commas (e.g., "1,3,4")

Send *0* to cancel."""


async def handle_recipient_selection(state: ConversationState, body: str) -> str:
    """Handle recipient selection response"""
    body = body.strip().upper()
    
    selected = []
    
    if body == 'A':
        # All participants
        selected = state.participants
    elif body == 'T':
        # Team Leader and Owner only
        selected = [p for p in state.participants if p['type'] in ['owner', 'team_leader']]
        if not selected:
            return "No Team Leader or Owner found. Please select specific recipients."
    else:
        # Parse comma-separated numbers
        try:
            indices = [int(x.strip()) for x in body.split(',')]
            for idx in indices:
                if 1 <= idx <= len(state.participants):
                    selected.append(state.participants[idx - 1])
        except ValueError:
            return "Please enter valid numbers separated by commas, 'A' for all, or 'T' for Team Leader & Owner."
    
    if not selected:
        return "No valid recipients selected. Please try again."
    
    state.selected_recipients = selected
    state.state = ConversationState.CONFIRMING_FORWARD
    
    recipient_names = ", ".join([r['name'] for r in selected])
    project_name = state.selected_project.get('title', state.selected_project.get('name', 'Project'))
    
    return f"""✅ *Confirm Forward*

📁 *Project:* {project_name}
👥 *Recipients:* {recipient_names}
💬 *Message:* {state.pending_message[:100] if state.pending_message else '[Voice Note]'}{'...' if len(state.pending_message or '') > 100 else ''}

Reply *YES* to send, or *0* to cancel."""


async def handle_forward_confirmation(state: ConversationState, body: str) -> str:
    """Handle forward confirmation response"""
    if body.strip().upper() != 'YES':
        state.reset()
        return "❌ Message not sent. Send any message to start again."
    
    # Forward the message
    sender_name = state.sender_info.get('name', 'Unknown')
    project_name = state.selected_project.get('title', state.selected_project.get('name', 'Project'))
    is_voice = state.pending_media_url is not None
    
    results = await forward_message_to_recipients(
        sender_name=sender_name,
        project_name=project_name,
        message=state.pending_message or '',
        recipients=state.selected_recipients,
        media_url=state.pending_media_url,
        is_voice_note=is_voice
    )
    
    # Count successes
    success_count = sum(1 for r in results if r.get('success'))
    total_count = len(results)
    
    # Log the forwarded message
    await log_forwarded_message(
        sender_id=state.sender_info.get('id'),
        sender_name=sender_name,
        project_id=state.selected_project.get('id'),
        project_name=project_name,
        message=state.pending_message,
        media_url=state.pending_media_url,
        recipients=[r['name'] for r in state.selected_recipients],
        results=results
    )
    
    # Reset state
    state.reset()
    
    if success_count == total_count:
        return f"""✅ *Message Forwarded Successfully!*

Your message has been sent to {success_count} recipient(s).

They will receive it on WhatsApp shortly."""
    elif success_count > 0:
        return f"""⚠️ *Partially Sent*

Message sent to {success_count} of {total_count} recipients.

Some recipients may not have valid WhatsApp numbers."""
    else:
        return """❌ *Failed to Send*

Unable to forward your message. Please try again later or contact us directly."""


async def log_forwarded_message(
    sender_id: str,
    sender_name: str,
    project_id: str,
    project_name: str,
    message: str,
    media_url: Optional[str],
    recipients: List[str],
    results: List[Dict]
):
    """Log forwarded message for audit trail"""
    try:
        log_entry = {
            "id": f"fwd_{datetime.now(timezone.utc).timestamp()}",
            "sender_id": sender_id,
            "sender_name": sender_name,
            "project_id": project_id,
            "project_name": project_name,
            "message": message,
            "media_url": media_url,
            "recipients": recipients,
            "results": results,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.whatsapp_forwards.insert_one(log_entry)
        logger.info(f"Logged forwarded message from {sender_name} for project {project_name}")
        
    except Exception as e:
        logger.error(f"Error logging forwarded message: {str(e)}")

"""
WhatsApp Template Configuration
All approved WhatsApp Business API templates for 4th Dimension Architects
"""

# Template Content SIDs (from Twilio Console)
WHATSAPP_TEMPLATES = {
    # Invitation template - for inviting new users
    "invitation": "HX6b1d5f9a7a01af474f0875e734e9d548",
    
    # Project created - notification to client
    "project_created_client": "HX465fd35b0d97f4b51b6bce3e14cb9afd",
    
    # Project created - notification to team leader
    "project_created_team": "HXa8d19f666431bbae451c42409d809cca",
    
    # Drawing issued - notification to recipients
    "drawing_issued": "HX379f0ac393af21dfebcb69cbcc339634",
    
    # User approved - welcome message after approval
    "user_approved": "HXb8c0e008927cef963fa02616e0d8611a",
    
    # Task assigned - notification when task is assigned
    "task_assigned": "HXddd309318f33cb50eb38a4b40aaa13e2",
}

# Template variable mappings (for reference)
TEMPLATE_VARIABLES = {
    "invitation": {
        "1": "name",           # Person being invited
        "2": "invited_by",     # Person sending invite
        "3": "role",           # Client, Team Member, etc.
        "4": "register_url"    # Registration URL
    },
    "project_created_client": {
        "1": "client_name",
        "2": "project_name",
        "3": "team_leader_name",
        "4": "team_leader_phone",
        "5": "app_url"
    },
    "project_created_team": {
        "1": "project_name",
        "2": "client_name",
        "3": "client_phone",
        "4": "app_url"
    },
    "drawing_issued": {
        "1": "recipient_name",
        "2": "project_name",
        "3": "drawing_name",
        "4": "issue_date",
        "5": "drawing_url"
    },
    "user_approved": {
        "1": "user_name",
        "2": "app_url"
    },
    "task_assigned": {
        "1": "assignee_name",
        "2": "assigner_name",
        "3": "task_title",
        "4": "due_date",
        "5": "task_url"
    }
}


def get_template_sid(template_name: str) -> str:
    """Get template SID by name"""
    return WHATSAPP_TEMPLATES.get(template_name)


def get_all_templates() -> dict:
    """Get all template SIDs"""
    return WHATSAPP_TEMPLATES.copy()

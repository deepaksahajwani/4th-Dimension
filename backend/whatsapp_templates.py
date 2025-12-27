"""
WhatsApp Template Configuration
All approved WhatsApp Business API templates for 4th Dimension Architects

IMPORTANT: Only templates that ACTUALLY EXIST in Twilio are listed here.
To add a new template:
1. Create it in Twilio Console → Messaging → Content Template Builder
2. Submit for WhatsApp approval (takes 1-3 days)
3. Once approved, add the SID here

Last Updated: Dec 2024
"""

# Template Content SIDs (from Twilio Console)
WHATSAPP_TEMPLATES = {
    # ============================================
    # INVITATION TEMPLATES
    # ============================================
    
    # Original invitation template (keeping active)
    # Variables: {{1}}=name, {{2}}=inviter, {{3}}=role, {{4}}=register_url
    "invitation": "HX6b1d5f9a7a01af474f0875e734e9d548",
    
    # New invitation template with START prompt (preferred)
    # Variables: {{1}}=invitee_name, {{2}}=inviter_name, {{3}}=role, {{4}}=register_url
    "new_invitation": "HX2a73a67f15f212fc2d7e5b1295468d2c",
    
    # ============================================
    # USER APPROVAL TEMPLATE
    # ============================================
    
    # User approved v2 - welcome message after approval (5 variables)
    # Variables: {{1}}=user_name, {{2}}=role, {{3}}=approver_name, {{4}}=approval_date, {{5}}=login_url
    "user_approved": "HX8756b3df94104dcf48df9e8819b1e13d",
    
    # ============================================
    # PROJECT TEMPLATES
    # ============================================
    
    # Project created - notification to client
    # Variables: {{1}}=client_name, {{2}}=project_name, {{3}}=team_leader_name, {{4}}=team_leader_phone, {{5}}=app_url
    "project_created_client": "HX465fd35b0d97f4b51b6bce3e14cb9afd",
    
    # Project created - notification to team leader
    # Variables: {{1}}=project_name, {{2}}=client_name, {{3}}=client_phone, {{4}}=app_url
    "project_created_team": "HXa8d19f666431bbae451c42409d809cca",
    
    # ============================================
    # DRAWING & TASK TEMPLATES
    # ============================================
    
    # Drawing issued - notification to recipients
    # Variables: {{1}}=recipient_name, {{2}}=project_name, {{3}}=drawing_name, {{4}}=issue_date, {{5}}=drawing_url
    "drawing_issued": "HX379f0ac393af21dfebcb69cbcc339634",
    
    # Task assigned - notification when task is assigned
    # Variables: {{1}}=assignee_name, {{2}}=assigner_name, {{3}}=task_title, {{4}}=due_date, {{5}}=task_url
    "task_assigned": "HXddd309318f33cb50eb38a4b40aaa13e2",
}

# Template variable mappings (for reference and validation)
TEMPLATE_VARIABLES = {
    "invitation": {
        "1": "invitee_name",
        "2": "inviter_name",
        "3": "role",
        "4": "register_url"
    },
    "new_invitation": {
        "1": "invitee_name",
        "2": "inviter_name",
        "3": "role",
        "4": "register_url"
    },
    "user_approved": {
        "1": "user_name",
        "2": "role",
        "3": "approver_name",
        "4": "approval_date",
        "5": "login_url"
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
    "task_assigned": {
        "1": "assignee_name",
        "2": "assigner_name",
        "3": "task_title",
        "4": "due_date",
        "5": "task_url"
    }
}


def get_template_sid(template_name: str) -> str:
    """Get template SID by name. Returns None if template doesn't exist."""
    return WHATSAPP_TEMPLATES.get(template_name)


def get_all_templates() -> dict:
    """Get all template SIDs"""
    return WHATSAPP_TEMPLATES.copy()


def validate_template_variables(template_name: str, variables: dict) -> bool:
    """Validate that provided variables match expected template variables"""
    expected = TEMPLATE_VARIABLES.get(template_name, {})
    if not expected:
        return True  # No validation for unknown templates
    
    expected_keys = set(expected.keys())
    provided_keys = set(variables.keys())
    
    return expected_keys == provided_keys

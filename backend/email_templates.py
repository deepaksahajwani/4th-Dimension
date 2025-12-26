"""
Email Templates for 4th Dimension Architecture Firm
Role-specific welcome emails for approved users
Supports: English, Hindi, Tamil, Marathi, Gujarati
"""

import os

def get_language_toggle_bar(user_id: str, role: str, backend_url: str) -> str:
    """Generate language toggle bar for emails"""
    base_url = f"{backend_url}/email-preview"
    return f"""
    <div style="background: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; border: 1px solid #E5E7EB;">
        <p style="margin: 0 0 10px 0; font-size: 13px; color: #6B7280;"><strong>🌐 Read this email in your language:</strong></p>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;">
            <a href="{base_url}?user={user_id}&role={role}&lang=en" style="background: #4F46E5; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">English</a>
            <a href="{base_url}?user={user_id}&role={role}&lang=hi" style="background: #10B981; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">हिंदी</a>
            <a href="{base_url}?user={user_id}&role={role}&lang=ta" style="background: #F59E0B; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">தமிழ்</a>
            <a href="{base_url}?user={user_id}&role={role}&lang=mr" style="background: #EF4444; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">मराठी</a>
            <a href="{base_url}?user={user_id}&role={role}&lang=gu" style="background: #8B5CF6; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">ગુજરાતી</a>
        </div>
    </div>
    """

def get_welcome_email_content(user: dict, login_url: str) -> tuple[str, str]:
    """
    Generate role-specific welcome email content (English only)
    Returns: (subject, html_content)
    """
    
    role = user.get('role', '').lower()
    name = user['name']
    email = user['email']
    user_id = user.get('id', '')
    registered_via = user.get('registered_via', 'email')
    
    # Format the role for display (e.g., "senior_interior_designer" -> "Senior Interior Designer")
    display_role = role.replace('_', ' ').title()
    
    # Determine the role category for template selection
    # Team members include various designations
    team_member_roles = [
        'team_member', 'owner', 'principal_architect', 'senior_architect', 'junior_architect',
        'senior_interior_designer', 'junior_interior_designer', 'interior_designer',
        'project_manager', 'site_engineer', 'draftsman', 'cad_operator',
        'design_lead', 'design_associate', 'team_lead', 'team_leader'
    ]
    
    # Contractor types
    contractor_roles = [
        'contractor', 'furniture_contractor', 'electrical_contractor', 'plumbing_contractor',
        'civil_contractor', 'painting_contractor', 'flooring_contractor', 'hvac_contractor',
        'glass_contractor', 'false_ceiling_contractor', 'landscaping_contractor'
    ]
    
    # Consultant types
    consultant_roles = [
        'consultant', 'structural_consultant', 'mep_consultant', 'electrical_consultant',
        'plumbing_consultant', 'hvac_consultant', 'fire_consultant', 'acoustics_consultant',
        'lighting_consultant', 'landscape_consultant', 'vastu_consultant'
    ]
    
    # Determine category
    if role in team_member_roles or role in ['owner']:
        role_category = 'team_member'
    elif role in contractor_roles or 'contractor' in role:
        role_category = 'contractor'
    elif role in consultant_roles or 'consultant' in role:
        role_category = 'consultant'
    elif role == 'client':
        role_category = 'client'
    elif role == 'vendor':
        role_category = 'vendor'
    else:
        # Default to team member for unrecognized internal roles
        role_category = 'team_member'
    
    # Common styling
    header_style = "text-align: center; margin-bottom: 30px;"
    section_style = "background: #F3F4F6; padding: 25px; border-radius: 10px; margin: 25px 0;"
    feature_style = "background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4F46E5;"
    button_style = "display: inline-block; background: #4F46E5; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin-top: 20px; font-weight: bold; font-size: 16px;"
    
    # Login credentials section
    credentials_html = f"""
    <div style="background: #D1FAE5; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center; border: 2px solid #10B981;">
        <p style="margin: 0 0 15px 0; font-size: 18px;"><strong>🔐 Your Login Credentials</strong></p>
        <p style="margin: 10px 0;"><strong>Email:</strong> {email}</p>
        {f'<p style="margin: 10px 0;"><strong>Password:</strong> As set during registration</p>' if registered_via == 'email' else '<p style="margin: 10px 0;"><strong>Login Method:</strong> Use your Google account</p>'}
        
        <a href="{login_url}" style="{button_style}">
            🚀 Login to Your Dashboard
        </a>
    </div>
    """
    
    # Role-specific content
    if role_category == 'client':
        subject = "Welcome to 4th Dimension - Your Architectural Journey Begins! 🏛️"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome to 4th Dimension! 🎉</h1>
                        <p style="color: #6B7280; font-size: 16px;">Architecture & Design Excellence</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">We are absolutely delighted to welcome you as our valued client! Your architectural journey with 4th Dimension begins today, and we're committed to transforming your vision into stunning reality.</p>
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">🌟 What We Offer You</h3>
                        
                        <div style="{feature_style}">
                            <strong>🎨 Innovative Design Excellence</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Our award-winning architects blend creativity with functionality, crafting spaces that inspire and delight. Every project is a masterpiece tailored to your unique vision.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📱 Real-Time Project Transparency</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Stay informed 24/7 with live updates on your project's progress. View drawings, approve designs, and track milestones—all from your personalized dashboard.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>💬 Direct Communication Channel</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Connect directly with our design team, share feedback instantly, and collaborate seamlessly throughout your project journey.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📐 Professional Drawing Management</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access all architectural drawings, revisions, and documentation in one secure location. Review, comment, and approve designs at your convenience.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>🏗️ Quality Assurance</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">We maintain the highest standards of quality and compliance, ensuring your project meets all regulatory requirements and exceeds your expectations.</p>
                        </div>
                    </div>
                    
                    {credentials_html}
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">📱 How to Use Your Client Portal</h3>
                        
                        <ol style="padding-left: 20px; color: #4B5563;">
                            <li style="margin: 12px 0;"><strong>View Your Projects:</strong> Access all your ongoing and completed projects from your dashboard.</li>
                            <li style="margin: 12px 0;"><strong>Review Drawings:</strong> Browse through architectural plans, elevations, and 3D renderings with zoom and annotation tools.</li>
                            <li style="margin: 12px 0;"><strong>Track Progress:</strong> Monitor project milestones, timelines, and completion percentages in real-time.</li>
                            <li style="margin: 12px 0;"><strong>Provide Feedback:</strong> Comment directly on drawings and designs to share your thoughts with our team.</li>
                            <li style="margin: 12px 0;"><strong>Approve Designs:</strong> Review and approve design iterations with a simple click.</li>
                            <li style="margin: 12px 0;"><strong>Access Documents:</strong> Download contracts, invoices, and project documentation anytime.</li>
                            <li style="margin: 12px 0;"><strong>Stay Updated:</strong> Receive instant notifications about important project updates and milestones.</li>
                        </ol>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #92400E;"><strong>💡 Pro Tip:</strong> Enable notifications in your account settings to receive real-time updates on your project progress!</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">We're honored that you've chosen 4th Dimension to bring your architectural dreams to life. Our team is ready to exceed your expectations at every step.</p>
                    
                    <p style="font-size: 16px;"><strong>Let's build something extraordinary together!</strong></p>
                    
                    <p style="margin-top: 30px;">Warm regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Need Help? Contact us at <a href="mailto:support@4thdimension.com" style="color: #4F46E5;">support@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    elif role_category == 'team_member':
        subject = f"Welcome to 4th Dimension - {display_role}! 🎯"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome to the Team! 🎉</h1>
                        <p style="color: #6B7280; font-size: 16px;">4th Dimension - Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <div style="background: #EEF2FF; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; border: 2px solid #4F46E5;">
                        <p style="margin: 0; font-size: 14px; color: #6B7280;">Your Role</p>
                        <p style="margin: 10px 0 0 0; font-size: 24px; font-weight: bold; color: #4F46E5;">{display_role}</p>
                    </div>
                    
                    <p style="font-size: 16px; line-height: 1.8;">Congratulations and welcome to 4th Dimension! We're thrilled to have you join our talented team as <strong>{display_role}</strong>. Together, we'll continue to create exceptional spaces that inspire and transform lives.</p>
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">🎯 What 4th Dimension Offers You</h3>
                        
                        <div style="{feature_style}">
                            <strong>🚀 Professional Growth</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Work on diverse, challenging projects that will expand your skills and portfolio. We invest in continuous learning and development for all team members.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>🤝 Collaborative Environment</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Join a supportive team where ideas are valued, creativity is encouraged, and collaboration drives innovation in every project.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>⚡ Streamlined Workflow Tools</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access powerful project management tools designed specifically for architectural workflows, making your work more efficient and organized.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>🏆 Recognition & Rewards</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Your contributions matter. We celebrate achievements, recognize excellence, and provide opportunities for career advancement.</p>
                        </div>
                    </div>
                    
                    {credentials_html}
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">📱 Your Team Dashboard - Quick Guide</h3>
                        
                        <ol style="padding-left: 20px; color: #4B5563;">
                            <li style="margin: 12px 0;"><strong>Manage Your Projects:</strong> View all assigned projects, tasks, and deadlines in your personalized dashboard.</li>
                            <li style="margin: 12px 0;"><strong>Upload & Share Drawings:</strong> Create, upload, and collaborate on architectural drawings with version control and revision tracking.</li>
                            <li style="margin: 12px 0;"><strong>Task Management:</strong> Track your daily tasks, set priorities, and update progress with our intuitive task system.</li>
                            <li style="margin: 12px 0;"><strong>Team Collaboration:</strong> Communicate with team members, clients, and contractors through integrated messaging and comments.</li>
                            <li style="margin: 12px 0;"><strong>Document Library:</strong> Access shared resources, templates, and standards library for consistent project delivery.</li>
                            <li style="margin: 12px 0;"><strong>Time & Progress Tracking:</strong> Log work hours, submit daily targets, and track weekly accomplishments.</li>
                            <li style="margin: 12px 0;"><strong>Site Visit Reports:</strong> Document site visits with photos, notes, and observations directly from the field.</li>
                            <li style="margin: 12px 0;"><strong>Client Updates:</strong> Prepare and share professional updates with clients through the portal.</li>
                        </ol>
                    </div>
                    
                    <div style="background: #DBEAFE; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #3B82F6;">
                        <p style="margin: 0; color: #1E40AF;"><strong>🎓 Getting Started:</strong> Check the "Resources" section in your dashboard for onboarding materials, company standards, and helpful tutorials!</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">We're excited to see the amazing work you'll create as part of our team. Your unique talents and perspective will contribute to our continued success and innovation.</p>
                    
                    <p style="font-size: 16px;"><strong>Welcome aboard, and let's create something extraordinary!</strong></p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Leadership Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Questions? Reach out to HR at <a href="mailto:hr@4thdimension.com" style="color: #4F46E5;">hr@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    elif role == 'contractor':
        subject = "Welcome to 4th Dimension Partnership - Contractor Portal Access 🏗️"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome Partner! 🤝</h1>
                        <p style="color: #6B7280; font-size: 16px;">4th Dimension - Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">Welcome to the 4th Dimension contractor network! We're pleased to partner with you and look forward to successful project collaborations. Your expertise is crucial to bringing our architectural visions to life.</p>
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">🏗️ Partnership Benefits</h3>
                        
                        <div style="{feature_style}">
                            <strong>📋 Streamlined Project Access</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access all project details, drawings, specifications, and timelines from your dedicated contractor portal—no more email chains or lost documents.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📐 Technical Drawing Access</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">View and download construction drawings, details, and specifications with zoom, measurement, and annotation tools for accuracy.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>💬 Direct Communication</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Communicate directly with architects and project managers, ask questions, and receive clarifications quickly through integrated messaging.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📸 Progress Documentation</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Submit progress photos, site reports, and updates directly through the portal for transparent project tracking.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>💼 Efficient Payment Processing</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Track work completed, submit invoices, and manage payment schedules seamlessly through the system.</p>
                        </div>
                    </div>
                    
                    {credentials_html}
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">📱 Contractor Portal Guide</h3>
                        
                        <ol style="padding-left: 20px; color: #4B5563;">
                            <li style="margin: 12px 0;"><strong>View Assigned Projects:</strong> See all projects you're contracted for with full details and timelines.</li>
                            <li style="margin: 12px 0;"><strong>Access Construction Drawings:</strong> Download architectural plans, structural drawings, and specifications in high resolution.</li>
                            <li style="margin: 12px 0;"><strong>Review Project Requirements:</strong> Check materials, finishes, and specifications for accurate execution.</li>
                            <li style="margin: 12px 0;"><strong>Submit Progress Reports:</strong> Upload site photos, update work status, and document milestone completions.</li>
                            <li style="margin: 12px 0;"><strong>Communicate Issues:</strong> Report site issues, request clarifications, or highlight concerns immediately.</li>
                            <li style="margin: 12px 0;"><strong>Track Payments:</strong> Monitor payment schedules, submit invoices, and view payment history.</li>
                            <li style="margin: 12px 0;"><strong>Access Site Schedules:</strong> View project timelines and coordinate your work with other contractors.</li>
                            <li style="margin: 12px 0;"><strong>Download Documents:</strong> Access contracts, change orders, and compliance documentation.</li>
                        </ol>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #92400E;"><strong>⚠️ Important:</strong> Always verify you're working from the latest drawing revision. Check the portal daily for updates and change notifications!</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">We believe in building strong partnerships based on quality, transparency, and mutual success. We're committed to providing you with all the tools and support needed for smooth project execution.</p>
                    
                    <p style="font-size: 16px;"><strong>Looking forward to successful projects together!</strong></p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Project Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Project Support: <a href="mailto:projects@4thdimension.com" style="color: #4F46E5;">projects@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    elif role == 'consultant':
        subject = "Welcome to 4th Dimension Consultant Network 🎓"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome Expert Consultant! 🎓</h1>
                        <p style="color: #6B7280; font-size: 16px;">4th Dimension - Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">Welcome to the 4th Dimension consultant network! We're honored to collaborate with your expertise. Your specialized knowledge will be instrumental in delivering exceptional projects and innovative solutions to our clients.</p>
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">🌟 Collaboration Value</h3>
                        
                        <div style="{feature_style}">
                            <strong>🔍 Project-Specific Access</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access relevant project documentation, drawings, and technical details for the projects requiring your consultation.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📊 Comprehensive Information</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Review complete project scope, design intent, and technical requirements to provide informed recommendations.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>💡 Professional Collaboration</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Work seamlessly with our architectural team through integrated communication tools and document sharing.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📝 Streamlined Reporting</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Submit reports, recommendations, and technical analyses directly through the portal with version tracking.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>⏱️ Efficient Workflow</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Reduce coordination overhead with centralized project information and clear communication channels.</p>
                        </div>
                    </div>
                    
                    {credentials_html}
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">📱 Consultant Portal Features</h3>
                        
                        <ol style="padding-left: 20px; color: #4B5563;">
                            <li style="margin: 12px 0;"><strong>Project Dashboard:</strong> View all projects where your consultation is required with status and deadlines.</li>
                            <li style="margin: 12px 0;"><strong>Technical Documentation:</strong> Access architectural drawings, specifications, and technical details relevant to your expertise.</li>
                            <li style="margin: 12px 0;"><strong>Review & Comment:</strong> Provide feedback, mark up drawings, and highlight areas requiring attention.</li>
                            <li style="margin: 12px 0;"><strong>Submit Reports:</strong> Upload consultation reports, analysis documents, and recommendations with version control.</li>
                            <li style="margin: 12px 0;"><strong>Direct Communication:</strong> Discuss technical matters directly with architects and project managers.</li>
                            <li style="margin: 12px 0;"><strong>Meeting Coordination:</strong> Schedule and document consultation meetings and site visits.</li>
                            <li style="margin: 12px 0;"><strong>Document Library:</strong> Access previous reports and maintain a record of all consultation work.</li>
                            <li style="margin: 12px 0;"><strong>Invoice Management:</strong> Submit consultation fees and track payment status.</li>
                        </ol>
                    </div>
                    
                    <div style="background: #E0E7FF; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #6366F1;">
                        <p style="margin: 0; color: #3730A3;"><strong>🎯 Best Practice:</strong> Review project information thoroughly before consultation calls. All relevant documents are available in your project folder!</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">Your professional expertise is valued and respected. We're committed to fostering a collaborative environment where your insights can truly make a difference in project outcomes.</p>
                    
                    <p style="font-size: 16px;"><strong>We look forward to productive collaborations!</strong></p>
                    
                    <p style="margin-top: 30px;">Warm regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Design Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Technical Support: <a href="mailto:technical@4thdimension.com" style="color: #4F46E5;">technical@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    elif role == 'vendor':
        subject = "Welcome to 4th Dimension Vendor Network 🏪"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome Vendor Partner! 🏪</h1>
                        <p style="color: #6B7280; font-size: 16px;">4th Dimension - Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">Welcome to the 4th Dimension vendor network! We're excited to partner with you for supplying quality materials and products for our architectural projects. Your reliability and product excellence are crucial to our project success.</p>
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">🤝 Partnership Benefits</h3>
                        
                        <div style="{feature_style}">
                            <strong>📦 Streamlined Procurement</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Receive material requirements, specifications, and purchase orders directly through the vendor portal.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📋 Clear Specifications</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access detailed product specifications, quantities, and delivery schedules for accurate fulfillment.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>💰 Transparent Transactions</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Submit quotations, track orders, manage invoices, and monitor payment status in one centralized system.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>🚚 Delivery Coordination</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Update delivery schedules, confirm shipments, and coordinate logistics efficiently with project teams.</p>
                        </div>
                        
                        <div style="{feature_style}">
                            <strong>📈 Business Growth</strong>
                            <p style="margin: 8px 0 0 0; color: #4B5563;">Access ongoing projects and opportunities for consistent business relationships and growth.</p>
                        </div>
                    </div>
                    
                    {credentials_html}
                    
                    <div style="{section_style}">
                        <h3 style="color: #4F46E5; margin-top: 0;">📱 Vendor Portal Guide</h3>
                        
                        <ol style="padding-left: 20px; color: #4B5563;">
                            <li style="margin: 12px 0;"><strong>View Projects:</strong> See all projects where your products/materials are specified or required.</li>
                            <li style="margin: 12px 0;"><strong>Receive Requirements:</strong> Get material requisitions with specifications, quantities, and delivery timelines.</li>
                            <li style="margin: 12px 0;"><strong>Submit Quotations:</strong> Provide pricing, availability, and lead time information for requested materials.</li>
                            <li style="margin: 12px 0;"><strong>Manage Orders:</strong> Track purchase orders, confirm acceptance, and update order status.</li>
                            <li style="margin: 12px 0;"><strong>Update Deliveries:</strong> Schedule deliveries, update shipment tracking, and confirm deliveries.</li>
                            <li style="margin: 12px 0;"><strong>Upload Documents:</strong> Share product catalogs, technical data sheets, warranties, and certifications.</li>
                            <li style="margin: 12px 0;"><strong>Submit Invoices:</strong> Upload invoices with proper documentation and track payment status.</li>
                            <li style="margin: 12px 0;"><strong>Communication:</strong> Clarify specifications, discuss alternatives, and resolve issues directly.</li>
                        </ol>
                    </div>
                    
                    <div style="background: #FEE2E2; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #EF4444;">
                        <p style="margin: 0; color: #991B1B;"><strong>⚡ Quick Tip:</strong> Enable portal notifications to receive instant alerts for new orders, delivery updates, and payment confirmations!</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">We value reliable vendor partnerships and are committed to timely payments, clear communication, and mutually beneficial business relationships. Your quality products contribute directly to our project success.</p>
                    
                    <p style="font-size: 16px;"><strong>Looking forward to a successful partnership!</strong></p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Procurement Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Procurement: <a href="mailto:procurement@4thdimension.com" style="color: #4F46E5;">procurement@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    else:
        # Default/fallback template
        subject = "Welcome to 4th Dimension! 🎉"
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="{header_style}">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">Welcome to 4th Dimension! 🎉</h1>
                        <p style="color: #6B7280; font-size: 16px;">Architecture & Design Excellence</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 24px;">Dear {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">Welcome! Your account has been approved and you now have access to the 4th Dimension portal.</p>
                    
                    {credentials_html}
                    
                    <p style="font-size: 16px; margin-top: 30px;">We look forward to working with you!</p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>
                    <strong style="color: #4F46E5;">The 4th Dimension Team</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">Architecture & Design</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    return subject, html_content

def get_translated_email_content(user: dict, login_url: str, lang: str = 'en') -> tuple[str, str]:
    """
    Generate translated email content for Hindi and Gujarati
    For other languages, falls back to English
    """
    from email_translations import TRANSLATIONS
    
    if lang not in ['hi', 'gu']:
        # Fall back to English for unsupported languages
        return get_welcome_email_content(user, login_url)
    
    role = user.get('role', '').lower()
    name = user['name']
    email = user['email']
    user_id = user.get('id', '')
    registered_via = user.get('registered_via', 'email')
    backend_url = os.getenv('REACT_APP_BACKEND_URL', login_url)
    
    # Get translations
    t = TRANSLATIONS[lang]
    
    # Common styling
    button_style = "display: inline-block; background: #4F46E5; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin-top: 20px; font-weight: bold; font-size: 16px;"
    
    # Language toggle bar
    language_toggle = get_language_toggle_bar(user_id, role, backend_url)
    
    # Login credentials
    credentials_html = f"""
    <div style="background: #D1FAE5; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center; border: 2px solid #10B981;">
        <p style="margin: 0 0 15px 0; font-size: 18px;"><strong>{t['client']['login_credentials']}</strong></p>
        <p style="margin: 10px 0;"><strong>{t['client']['email_label']}</strong> {email}</p>
        {f'<p style="margin: 10px 0;"><strong>{t["client"]["password_label"]}</strong> {t["client"]["password_set"]}</p>' if registered_via == 'email' else f'<p style="margin: 10px 0;"><strong>{t["client"]["login_method"]}</strong> {t["client"]["use_google"]}</p>'}
        
        <a href="{login_url}" style="{button_style}">
            {t['client']['login_button']}
        </a>
    </div>
    """
    
    if role == 'client':
        role_data = t['client']
        subject = role_data['subject']
        
        # Build features HTML
        features_html = ""
        for feature in role_data['features']:
            features_html += f"""
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4F46E5;">
                <strong>{feature['title']}</strong>
                <p style="margin: 8px 0 0 0; color: #4B5563;">{feature['desc']}</p>
            </div>
            """
        
        # Build steps HTML
        steps_html = ""
        for idx, step in enumerate(role_data['steps'], 1):
            steps_html += f'<li style="margin: 12px 0;">{step}</li>'
        
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">{t['welcome']}</h1>
                        <p style="color: #6B7280; font-size: 16px;">{t['architecture_design']}</p>
                    </div>
                    
                    {language_toggle}
                    
                    <h2 style="color: #1F2937; font-size: 24px;">{t['dear']} {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">{role_data['intro']}</p>
                    
                    <div style="background: #F3F4F6; padding: 25px; border-radius: 10px; margin: 25px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">{role_data['what_we_offer']}</h3>
                        {features_html}
                    </div>
                    
                    {credentials_html}
                    
                    <div style="background: #F3F4F6; padding: 25px; border-radius: 10px; margin: 25px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">{role_data['how_to_use']}</h3>
                        <ol style="padding-left: 20px; color: #4B5563;">
                            {steps_html}
                        </ol>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #92400E;"><strong>{role_data['pro_tip']}</strong> {role_data['pro_tip_text']}</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">{role_data['closing']}</p>
                    
                    <p style="font-size: 16px;"><strong>{role_data['lets_build']}</strong></p>
                    
                    <p style="margin-top: 30px;">{role_data['warm_regards']}<br>
                    <strong style="color: #4F46E5;">{role_data['team']}</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">{t['architecture_design']}</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - {t['architecture_design']}</strong></p>
                        <p style="margin: 5px 0;">{role_data['tagline']}</p>
                        <p style="margin: 15px 0 5px 0;">{role_data['need_help']} <a href="mailto:support@4thdimension.com" style="color: #4F46E5;">support@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    elif role == 'contractor':
        role_data = t['contractor']
        subject = role_data['subject']
        
        # Build features HTML
        features_html = ""
        for feature in role_data['features']:
            features_html += f"""
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4F46E5;">
                <strong>{feature['title']}</strong>
                <p style="margin: 8px 0 0 0; color: #4B5563;">{feature['desc']}</p>
            </div>
            """
        
        # Build steps HTML
        steps_html = ""
        for idx, step in enumerate(role_data['steps'], 1):
            steps_html += f'<li style="margin: 12px 0;">{step}</li>'
        
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; font-size: 32px; margin-bottom: 10px;">{t['welcome']}</h1>
                        <p style="color: #6B7280; font-size: 16px;">{t['architecture_design']}</p>
                    </div>
                    
                    {language_toggle}
                    
                    <h2 style="color: #1F2937; font-size: 24px;">{t['dear']} {name},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">{role_data['intro']}</p>
                    
                    <div style="background: #F3F4F6; padding: 25px; border-radius: 10px; margin: 25px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">{role_data['partnership_benefits']}</h3>
                        {features_html}
                    </div>
                    
                    {credentials_html}
                    
                    <div style="background: #F3F4F6; padding: 25px; border-radius: 10px; margin: 25px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">{role_data['portal_guide']}</h3>
                        <ol style="padding-left: 20px; color: #4B5563;">
                            {steps_html}
                        </ol>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #92400E;"><strong>{role_data['important']}</strong> {role_data['important_text']}</p>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">{role_data['closing']}</p>
                    
                    <p style="font-size: 16px;"><strong>{role_data['looking_forward']}</strong></p>
                    
                    <p style="margin-top: 30px;">{role_data['best_regards']}<br>
                    <strong style="color: #4F46E5;">{role_data['team']}</strong><br>
                    <span style="color: #6B7280; font-size: 14px;">{t['architecture_design']}</span></p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - {t['architecture_design']}</strong></p>
                        <p style="margin: 5px 0;">{role_data['tagline'] if 'tagline' in role_data else t['client']['tagline']}</p>
                        <p style="margin: 15px 0 5px 0;">{role_data['support']} <a href="mailto:projects@4thdimension.com" style="color: #4F46E5;">projects@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    else:
        # For other roles, use English template
        return get_welcome_email_content(user, login_url)
    
    return subject, html_content

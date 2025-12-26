# 4th Dimension - Notification System Documentation

## Overview
This document lists all notifications sent by the system, their triggers, recipients, and message content.

---

## 1. USER REGISTRATION (New User Signs Up)

**Trigger:** User completes registration form and verifies OTP

**Recipients:**
- **Owner:** Gets notified about new registration needing approval
- **Registrant:** Gets confirmation that registration is pending

**Channels:**
- Owner: In-App + WhatsApp
- Registrant: Email

**Owner Message:**
```
New Registration: {name}
Role: {role}
Email: {email}

Review: {APP_URL}/pending-registrations
```

**Registrant Email Subject:** "Registration Pending Approval - 4th Dimension"

---

## 2. USER APPROVAL (Owner Approves Registration)

**Trigger:** Owner approves a pending registration

**Recipients:**
- Approved User

**Channels:**
- WhatsApp (using approved template)
- Email (professional HTML welcome)

**Email Subject (by role):**
- Client: "Welcome to 4th Dimension - Your Architectural Journey Begins! 🏛️"
- Contractor: "Welcome to 4th Dimension - {Type} Contractor Partnership! 🏗️"
- Consultant: "Welcome to 4th Dimension - Consultant! 🎓"
- Team Member: "Welcome to 4th Dimension - Team Member! 🎯"

---

## 3. REGISTRATION INVITATION (Owner Invites Someone)

**Trigger:** Owner sends invitation to new user

**Recipients:**
- Invitee

**Channels:**
- WhatsApp (template) → SMS (fallback)

**WhatsApp Template Variables:**
- {{1}}: Invitee name
- {{2}}: Inviter name
- {{3}}: Role (e.g., "Civil Contractor")
- {{4}}: Registration URL

**SMS Fallback:**
```
Hi {name}!

{inviter} from 4th Dimension Architects has invited you to join as a {role}.

📱 REGISTER HERE: {URL}

💬 FOR WHATSAPP UPDATES:
1. Save our number: +917016779016
2. Send "START" to us on WhatsApp

Welcome aboard!
- 4th Dimension Architects
```

---

## 4. PROJECT CREATION (New Project Created)

**Trigger:** Owner/Team Leader creates a new project

**Recipients:**
- Client (project owner)
- Team Leader (assigned)

**Channels:**
- WhatsApp (template)
- Email

**Client WhatsApp Template Variables:**
- {{1}}: Client name
- {{2}}: Project name
- {{3}}: Team leader name
- {{4}}: Team leader phone
- {{5}}: Portal URL

**Client Email Subject:** "Your Project is Ready - {Project Name}"

---

## 5. PROJECT TEAM ASSIGNMENT (Contractor/Consultant Added to Project)

**Trigger:** Existing contractor/consultant is assigned to a project

**Recipients:**
- Assigned person
- Client
- Owner + Team Leader (summary)

**Channels:**
- WhatsApp (freeform) → SMS (fallback)
- Email

**Contractor Message:**
```
🏗️ New Project Assignment

Hi {name}!

You have been assigned as {Type} Contractor for:

📁 Project: {project_name}
📍 Location: {address}
👔 Firm: 4th Dimension Architects

What's Next:
• Log in to view project details and drawings
• You'll receive notifications for relevant updates
• Contact us for any queries

Portal: {URL}
```

**Consultant Message:**
```
🔬 Consultant Engagement

Dear {name},

We are pleased to engage you as {Type} Consultant for:

📁 Project: {project_name}
📍 Location: {address}

Your Role:
• Provide {type} design and consultation
• Review and approve relevant drawings
• Coordinate with the project team
```

**SMS Fallback:**
```
Hi {name}! You've been assigned as {Type} {role} for project "{project}" at 4th Dimension Architects.

View project details: {URL}

- 4th Dimension Architects
```

---

## 6. DRAWING UPLOADED (For Approval)

**Trigger:** Team member uploads drawing for owner approval

**Recipients:**
- Owner

**Channels:**
- In-App + WhatsApp

**Message:**
```
📤 Drawing Uploaded for Approval

📁 Project: {project_name}
📐 Drawing: {drawing_name}
👤 Uploaded by: {uploader}
📅 Date: {date}

Please review and approve.
```

---

## 7. DRAWING APPROVED

**Trigger:** Owner approves a drawing

**Recipients:**
- Team Leader

**Channels:**
- In-App + WhatsApp

**Message:**
```
✅ Drawing Approved - Ready to Issue

📁 Project: {project_name}
📐 Drawing: {drawing_name}
🎯 Status: Approved

You can now issue this drawing to the client.
```

---

## 8. DRAWING REVISION (Internal)

**Trigger:** Owner/Team Leader requests revision on drawing

**Recipients:**
- Team Leader (if not the one who requested)

**Channels:**
- In-App + WhatsApp

**Message:**
```
🔄 Drawing Revision Required

📁 Project: {project_name}
📐 Drawing: {drawing_name}
👤 Revised by: {name}

Please review the revision comments and update.
```

---

## 9. DRAWING REVISION (External)

**Trigger:** Client/Contractor/Consultant requests revision

**Recipients:**
- Owner + Team Leader

**Channels:**
- In-App + WhatsApp

**Message:**
```
🔄 Drawing Revision from {role}

📁 Project: {project_name}
📐 Drawing: {drawing_name}
👤 Revised by: {name}

Please review and take necessary action.
```

---

## 10. DRAWING ISSUED

**Trigger:** Drawing is issued to recipients

**Recipients:**
- Selected recipients + Owner (mandatory)

**Channels:**
- WhatsApp (template)
- In-App

**WhatsApp Template Variables:**
- {{1}}: Recipient name
- {{2}}: Project name
- {{3}}: Drawing name
- {{4}}: Issue date
- {{5}}: Portal URL

---

## 11. DRAWING COMMENT

**Trigger:** Comment added on drawing

**Recipients:**
- Selected recipients + Owner (mandatory)

**Channels:**
- In-App + WhatsApp

**Client Message (Formal):**
```
Dear {name},

A comment has been added to a drawing in your project "{project}".

📐 Drawing: {drawing_name}
👤 Comment by: {commenter}
💬 Comment: "{comment_text}"

Please review using the link below.
```

**Team Message (Casual):**
```
💬 New Comment on Drawing

📁 {project_name}
📐 {drawing_name}
👤 {commenter}: "{comment_text}"
```

---

## 12. FEES PAID (By Client)

**Trigger:** Client marks payment as made

**Recipients:**
- Owner

**Channels:**
- In-App + WhatsApp

**Message:**
```
💰 Payment Notification

📁 Project: {project_name}
👤 Client: {client_name}
💵 Amount: ₹{amount}
💳 Mode: {payment_mode}
📅 Date: {date}

Status: Client has marked this payment as made
Action: Please verify and confirm receipt
```

---

## 13. FEES RECEIVED (By Owner)

**Trigger:** Owner records payment received

**Recipients:**
- Client + Owner

**Channels:**
- Email (for cheque/online) with invoice
- WhatsApp (for cash)

**Client Message:**
```
Dear {name},

Thank you for your payment for project "{project}".

💵 Amount Received: ₹{amount}
💳 Payment Mode: {mode}
📅 Date: {date}

Your payment has been successfully recorded.
```

---

## Email Sender
All emails are sent from: **"4th Dimension Architects" <contact@4thdimensionarchitect.com>**

---

## Re-Registration
- Deleted users CAN re-register with the same email
- Rejected users CAN re-register with the same email
- They will receive the full welcome email again upon approval

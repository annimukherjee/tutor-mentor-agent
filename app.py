# AI Tutor Mentoring System
# Project Structure:
# - data_generator.py - Creates sample student data
# - knowledge_base.py - Handles student knowledge tracking
# - email_processor.py - Scans and processes emails
# - app.py - Main Flask application
# - templates/ - HTML templates for web interface

# First, let's create the data generator to create sample student information

import pandas as pd
import numpy as np
import random
import requests
import os
import json
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
import imaplib
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from dotenv import load_dotenv

# Download NLTK resources
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")

# Load environment variables from .env file
load_dotenv()

# Configuration (with credentials loaded from .env)
CONFIG = {
    "data_dir": "data",
    "knowledge_dir": "knowledge_base",
    "courses": [
        "Computer Science",
        "Data Structures",
        "Algorithms",
        "Machine Learning",
        "Web Development",
        "Database Systems",
    ],
    "email_check_interval": 300,  # 5 minutes
    "professor_email": os.getenv("PROFESSOR_EMAIL", ""),
    "professor_password": os.getenv("PROFESSOR_PASSWORD", ""),
    "imap_server": os.getenv("IMAP_SERVER", "imap.gmail.com"),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "processed_emails_file": os.path.join("data", "processed_emails.json"),
}



# Validate essential configuration
if not CONFIG["professor_email"] or not CONFIG["professor_password"]:
    print("Warning: Professor email or password not found in .env file.")
    print("Email functionality will not work without these credentials.")

# Create necessary directories
os.makedirs(CONFIG["data_dir"], exist_ok=True)
os.makedirs(CONFIG["knowledge_dir"], exist_ok=True)


#################################
# Data Generator
#################################


def load_student_data():
    """Load student data from CSV file and generate random attendance data"""

    # Path to the student data CSV
    csv_path = os.path.join(CONFIG["data_dir"], "student_data.csv")

    if not os.path.exists(csv_path):
        print(f"Error: Student data file not found at {csv_path}")
        return []

    # Load the student data from CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded student data from {csv_path}")
    except Exception as e:
        print(f"Error loading student data: {e}")
        return []

    # Convert dataframe to list of dictionaries
    students = df.to_dict("records")

    # Generate random attendance for each student
    for student in students:
        # Generate random attendance for each course (between 60% and 100%)
        attendance = {}
        for course in CONFIG["courses"]:
            attendance[course] = round(random.uniform(60, 100), 1)

        # Add the attendance data to the student record
        student["attendance"] = attendance

    # Save to Excel with attendance data
    excel_path = os.path.join(CONFIG["data_dir"], "student_data_with_attendance.xlsx")
    pd.DataFrame(students).to_excel(excel_path, index=False)

    # Also save individual attendance sheets for each course
    for course in CONFIG["courses"]:
        course_data = []
        for student in students:
            course_data.append(
                {
                    "roll_no": student["roll_no"],
                    "name": f"{student['first_name']} {student['last_name']}",
                    "attendance_percentage": student["attendance"][course],
                    "total_classes": random.randint(40, 50),
                    "classes_attended": 0,  # Will be calculated below
                }
            )

        # Calculate classes attended based on attendance percentage
        for entry in course_data:
            entry["classes_attended"] = int(
                (entry["attendance_percentage"] / 100) * entry["total_classes"]
            )

        course_df = pd.DataFrame(course_data)
        course_file = os.path.join(
            CONFIG["data_dir"], f"{course.replace(' ', '_').lower()}_attendance.xlsx"
        )
        course_df.to_excel(course_file, index=False)

    # Initialize knowledge base for each student
    for student in students:
        create_knowledge_base(student)

    print(f"Processed {len(students)} students from CSV and saved to {excel_path}")
    return students


def create_knowledge_base(student):
    """Initialize an empty knowledge base for a student if it doesn't exist"""
    kb_file = os.path.join(CONFIG["knowledge_dir"], f"{student['roll_no']}.txt")

    if os.path.exists(kb_file):
        return

    # Create basic info section
    kb_content = f"""# Knowledge Base for {student['first_name']} {student['last_name']} ({student['roll_no']})
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Basic Information
- Name: {student['first_name']} {student['last_name']}
- Roll Number: {student['roll_no']}
- Email: {student['email']}
- Phone: {student['phone']}
- Parent 1 Phone: {student['parent1_phone']}
- Parent 2 Phone: {student['parent2_phone']}

## Attendance Summary
"""

    for course, attendance in student["attendance"].items():
        kb_content += f"- {course}: {attendance}%\n"

    kb_content += """
## Interaction History

## Special Circumstances

## Notes
"""

    with open(kb_file, "w") as f:
        f.write(kb_content)


#################################
# Knowledge Base Manager
#################################


def read_knowledge_base(roll_no):
    """Read a student's knowledge base file"""
    kb_file = os.path.join(CONFIG["knowledge_dir"], f"{roll_no}.txt")

    if not os.path.exists(kb_file):
        return None

    with open(kb_file, "r") as f:
        content = f.read()

    return content


def update_knowledge_base(roll_no, section, new_content, timestamp=None):
    """Update a specific section of a student's knowledge base"""
    kb_file = os.path.join(CONFIG["knowledge_dir"], f"{roll_no}.txt")

    if not os.path.exists(kb_file):
        return False

    with open(kb_file, "r") as f:
        content = f.read()

    # Find the section
    section_pattern = re.compile(f"## {section}\n(.*?)(?=\n## |$)", re.DOTALL)
    match = section_pattern.search(content)

    if not match:
        return False

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare new entry
    new_entry = f"\n[{timestamp}] {new_content}"

    # Replace the section with updated content
    updated_section = f"## {section}\n{match.group(1)}{new_entry}"
    updated_content = section_pattern.sub(updated_section, content)

    # Write back to file
    with open(kb_file, "w") as f:
        f.write(updated_content)

    return True


def add_interaction(roll_no, message, is_from_student=True):
    """Add an interaction to the student's knowledge base"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    direction = "FROM student" if is_from_student else "TO student"
    new_content = f"{direction}: {message}"

    return update_knowledge_base(roll_no, "Interaction History", new_content, timestamp)


def add_special_circumstance(roll_no, circumstance_type, details, follow_up_date=None):
    """Add a special circumstance to the student's knowledge base"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_content = f"TYPE: {circumstance_type}\nDETAILS: {details}"

    if follow_up_date:
        new_content += f"\nFOLLOW-UP DATE: {follow_up_date}"

    return update_knowledge_base(
        roll_no, "Special Circumstances", new_content, timestamp
    )


def get_all_students():
    """Get a list of all students from the Excel file with attendance data"""
    # First, try to load from the Excel file with attendance data
    excel_path = os.path.join(CONFIG["data_dir"], "student_data_with_attendance.xlsx")

    if not os.path.exists(excel_path):
        # If the attendance file doesn't exist, try to load from the original CSV
        # and regenerate attendance data
        csv_path = os.path.join(CONFIG["data_dir"], "student_data.csv")
        if os.path.exists(csv_path):
            return load_student_data()
        else:
            print("No student data found")
            return []

    try:
        df = pd.read_excel(excel_path)
        students = df.to_dict("records")

        # Convert attendance string to dictionary if needed
        for student in students:
            if "attendance" in student and isinstance(student["attendance"], str):
                try:
                    # Try to convert from string to dict if it's stored as string
                    student["attendance"] = eval(student["attendance"])
                except:
                    # If conversion fails, create a default attendance dict
                    student["attendance"] = {
                        course: 75.0 for course in CONFIG["courses"]
                    }

        return students
    except Exception as e:
        print(f"Error loading student data: {e}")
        return []


def get_student_by_roll_no(roll_no):
    """Get a student's information by roll number"""
    students = get_all_students()

    # Convert roll_no to int if it's a string, since your roll numbers appear to be integers
    if isinstance(roll_no, str):
        try:
            roll_no = int(roll_no)
        except ValueError:
            # If it can't be converted to int, keep it as is
            pass

    # Search for the student with matching roll_no
    for student in students:
        # Check if student's roll_no matches (handle both int and string cases)
        if str(student["roll_no"]) == str(roll_no):
            return student

    return None


def get_student_by_email(email):
    """Get a student's information by email"""
    students = get_all_students()

    email = email.lower()  # Normalize email for comparison

    for student in students:
        if (
            "email" in student
            and student["email"]
            and student["email"].lower() == email
        ):
            return student

    return None


#################################
# Email Processing
#################################


def extract_roll_no_from_email(sender_email):
    """Extract roll number from a student email address"""
    # Updated regex to match your email format (2205460@kiit.ac.in)
    match = re.match(r"(\d+)@kiit\.ac\.in", sender_email.lower())

    if match:
        # Return the roll number as an integer since that's how it's stored
        return int(match.group(1))

    # If that doesn't match, check our student database
    student = get_student_by_email(sender_email)
    if student:
        return student["roll_no"]

    return None


def check_emails():
    """Check professor's email for new messages from students with [MENTOR-COMMUNICATION] in subject"""
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(CONFIG["imap_server"])
        mail.login(CONFIG["professor_email"], CONFIG["professor_password"])
        mail.select("inbox")

        # Search for unread emails with [MENTOR-COMMUNICATION] in subject
        search_criteria = '(SUBJECT "[MENTOR-COMMUNICATION]")'
        status, data = mail.search(None, search_criteria)

        print(data)

        if status != "OK":
            print("No mentor communication messages found!")
            return []

        message_ids = data[0].split()

        if not message_ids:
            print("No messages with [MENTOR-COMMUNICATION] tag found!")
            return []

        processed_messages = []

        for msg_id in message_ids:
            status, data = mail.fetch(msg_id, "(RFC822)")

            if status != "OK":
                continue

            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Extract sender
            sender = email.utils.parseaddr(email_message["From"])[1]

            # Check if sender is a student
            roll_no = extract_roll_no_from_email(sender)

            if not roll_no:
                # Try to find student by email directly
                student = get_student_by_email(sender)
                if student:
                    roll_no = student["roll_no"]
                else:
                    # Skip this email if we can't identify the student
                    continue

            # Extract subject and body
            subject = email_message["Subject"]
            body = ""

            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            # Remove the standard footer if present
            body = remove_email_footer(body)

            # Process the message
            processed = process_student_message(roll_no, subject, body)
            processed_messages.append(processed)

            # Mark as read
            mail.store(msg_id, "+FLAGS", "\\Seen")

        mail.close()
        mail.logout()

        return processed_messages

    except Exception as e:
        print(f"Error checking emails: {e}")
        return []


def remove_email_footer(body):
    """Remove the standard KIIT email footer from email body"""
    # Use more aggressive matching to ensure the footer is caught
    
    # Try more precise matching first with regex
    import re
    
    # Pattern to match the start of the footer
    footer_pattern = re.compile(r'--\s*\n+\s*\*\s*<http://www\.kiit\.ac\.in>\*', re.DOTALL)
    match = footer_pattern.search(body)
    if match:
        # Return only the part before the footer
        return body[:match.start()].strip()
    
    # Try alternative pattern for "Go Green" text
    green_pattern = re.compile(r'Go\s+Green:\s+Kindly\s+don\'t\s+print\s+this\s+unless\s+so\s+required', re.DOTALL)
    match = green_pattern.search(body)
    if match:
        # Find the start of the line containing this pattern
        line_start = body[:match.start()].rfind('\n')
        if line_start >= 0:
            return body[:line_start].strip()
        else:
            # If no newline before the match, return empty string
            return ""
    
    # Try simpler string-based detection as fallback
    footer_markers = [
        "-- \n\n",
        "--\n\n",
        "Go Green: Kindly don't print this",
        "Established U/S 3 of UGC Act",
        "Visit us @ http://www.kiit.ac.in",
        "Follow us @",
        "The information contained in this electronic message",
        "VIRUS WARNING: Computer viruses"
    ]
    
    # Try to find the earliest occurrence of any marker
    earliest_pos = len(body)
    for marker in footer_markers:
        pos = body.find(marker)
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos
    
    # If we found a marker position
    if earliest_pos < len(body):
        # Find the start of the line
        line_start = body[:earliest_pos].rfind('\n')
        if line_start >= 0:
            return body[:line_start].strip()
        else:
            # If no newline before the match, use the position directly
            return body[:earliest_pos].strip()
    
    # If all else fails, try a very aggressive approach with double dashes
    dash_pos = body.find("--")
    if dash_pos > len(body) // 2:  # Only if it's in the latter half of the email
        return body[:dash_pos].strip()
        
    # If nothing worked, return the original body
    return body


def process_student_message(roll_no, subject, body):
    """Process a message from a student and update their knowledge base"""
    # Get student info
    student = get_student_by_roll_no(roll_no)

    if not student:
        return {"error": f"Student with roll number {roll_no} not found"}

    # Remove the footer before adding to interaction history
    cleaned_body = remove_email_footer(body)
    
    # Add to interaction history with the cleaned body
    add_interaction(roll_no, f"SUBJECT: {subject}\nBODY: {cleaned_body}", is_from_student=True)

    # Analyze message content (also using the cleaned body)
    response = analyze_message_content(roll_no, subject, cleaned_body)

    return {"student": student, "subject": subject, "body": cleaned_body, "response": response}



def analyze_message_content(roll_no, subject, body):
    """Analyze the content of a student message and determine appropriate response"""
    # Simple keyword-based analysis
    combined_text = (subject + " " + body).lower()
    tokens = word_tokenize(combined_text)

    # Check for leave request
    if any(word in combined_text for word in ["leave", "absent", "away", "vacation"]):
        # Try to extract duration
        leave_days = extract_leave_duration(combined_text)

        if leave_days:
            # Calculate expected return date
            today = datetime.now()
            return_date = today + timedelta(days=leave_days)

            # Add special circumstance
            add_special_circumstance(
                roll_no,
                "Leave Request",
                f"Student requested leave for {leave_days} days. Message: {body}",
                return_date.strftime("%Y-%m-%d"),
            )

            return {
                "type": "leave_request",
                "days": leave_days,
                "return_date": return_date.strftime("%Y-%m-%d"),
                "suggested_response": f"Your leave request for {leave_days} days has been noted. Please confirm your return by {return_date.strftime('%Y-%m-%d')}.",
            }

    # Check for medical issue
    if any(
        word in combined_text
        for word in [
            "hospital",
            "sick",
            "ill",
            "doctor",
            "medical",
            "health",
            "injury",
            "injured",
        ]
    ):
        # Try to extract duration if any
        recovery_days = extract_leave_duration(combined_text)

        if recovery_days:
            follow_up_date = (datetime.now() + timedelta(days=recovery_days)).strftime(
                "%Y-%m-%d"
            )
        else:
            follow_up_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

        add_special_circumstance(
            roll_no,
            "Medical Issue",
            f"Student reported a medical issue. Message: {body}",
            follow_up_date,
        )

        return {
            "type": "medical_issue",
            "follow_up_date": follow_up_date,
            "suggested_response": f"I'm sorry to hear about your health issue. Please take care and keep me updated on your recovery. I'll check in with you on {follow_up_date}.",
        }

    # Default response for other messages
    return {
        "type": "general_message",
        "suggested_response": "Thank you for your message. I've noted it down.",
    }


def extract_leave_duration(text):
    """Extract the number of days of leave from text"""
    # Look for patterns like "5 days", "for 3 days", etc.
    patterns = [
        r"(\d+)\s*days?",
        r"for\s*(\d+)",
        r"(\d+)\s*day leave",
        r"leave\s*for\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return None


def send_email(to_email, subject, body):
    """Send an email to a student"""
    try:
        msg = MIMEMultipart()
        msg["From"] = CONFIG["professor_email"]
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(CONFIG["smtp_server"], CONFIG["smtp_port"])
        server.starttls()
        server.login(CONFIG["professor_email"], CONFIG["professor_password"])
        text = msg.as_string()
        server.sendmail(CONFIG["professor_email"], to_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


#################################
# Follow-up System
#################################


def check_follow_ups():
    """Check for any follow-ups that need to be done today"""
    today = datetime.now().strftime("%Y-%m-%d")
    follow_ups = []

    # Get all students
    students = get_all_students()

    for student in students:
        roll_no = student["roll_no"]
        kb_content = read_knowledge_base(roll_no)

        if not kb_content:
            continue

        # Look for follow-up dates
        pattern = re.compile(r"FOLLOW-UP DATE: (\d{4}-\d{2}-\d{2})", re.MULTILINE)
        matches = pattern.findall(kb_content)

        for follow_up_date in matches:
            if follow_up_date == today:
                # Extract the circumstance
                circumstance_pattern = re.compile(
                    r"TYPE: (.*?)\nDETAILS: (.*?)\nFOLLOW-UP DATE: " + follow_up_date,
                    re.DOTALL,
                )
                circumstance_match = circumstance_pattern.search(kb_content)

                if circumstance_match:
                    circumstance_type = circumstance_match.group(1)
                    details = circumstance_match.group(2)

                    follow_ups.append(
                        {
                            "student": student,
                            "circumstance_type": circumstance_type,
                            "details": details,
                            "follow_up_date": follow_up_date,
                            "suggested_message": generate_follow_up_message(
                                circumstance_type, student
                            ),
                        }
                    )

    return follow_ups


def generate_follow_up_message(circumstance_type, student):
    """Generate a follow-up message based on the circumstance type"""
    name = student["first_name"]

    if circumstance_type == "Leave Request":
        return f"Hi {name}, I hope you're doing well. I wanted to check if you've returned from your leave and if everything is okay."

    elif circumstance_type == "Medical Issue":
        return f"Hi {name}, I'm checking in to see how you're feeling. I hope your recovery is going well. Please let me know if you need any additional support."

    else:
        return f"Hi {name}, I'm following up regarding our previous conversation. How are things going?"


#################################
# Flask Web Application
#################################

app = Flask(__name__, template_folder="templates")
app.secret_key = "ai_tutor_mentoring_system"  # For flash messages


@app.route("/")
def index():
    """Home page"""
    # Get number of students from data
    student_count = len(get_all_students())

    # Get number of follow-ups for today
    follow_ups = check_follow_ups()
    followup_count = len(follow_ups)

    return render_template(
        "index.html", student_count=student_count, followup_count=followup_count
    )


@app.route("/students")
def students_list():
    """Show list of all students"""
    students = get_all_students()
    return render_template("students.html", students=students)


@app.route("/student/<roll_no>")
def student_detail(roll_no):
    """Show details for a specific student"""
    student = get_student_by_roll_no(roll_no)

    if not student:
        flash(f"Student with roll number {roll_no} not found!")
        return redirect(url_for("students_list"))

    knowledge_base = read_knowledge_base(roll_no)

    return render_template(
        "student_detail.html", student=student, knowledge_base=knowledge_base
    )


# @app.route('/messages')
# def messages():
#     """Show messages from students that need responses and allow filtering by student."""
#     # Get the filter query from the URL (could be roll_no, first name, or last name)
#     filter_student = request.args.get('filter_student', "").strip().lower()
#     new_messages = check_emails()

#     if filter_student:
#         filtered = []
#         for msg in new_messages:
#             student = msg.get('student', {})
#             # Check if filter_student matches student roll_no or name (first_name or last_name)
#             if (filter_student == str(student.get('roll_no')).lower() or
#                 filter_student in student.get('first_name', "").lower() or
#                 filter_student in student.get('last_name', "").lower()):
#                 filtered.append(msg)
#         new_messages = filtered

#     return render_template('messages.html', messages=new_messages)


@app.route("/messages")
def messages():
    filter_student = request.args.get("filter_student", "").strip().lower()
    new_messages = check_emails()
    # Retrieve all students to populate the dropdown
    all_students = get_all_students()

    if filter_student:
        filtered = []
        for msg in new_messages:
            student = msg.get("student", {})
            if (
                filter_student == str(student.get("roll_no")).lower()
                or filter_student in student.get("first_name", "").lower()
                or filter_student in student.get("last_name", "").lower()
            ):
                filtered.append(msg)
        new_messages = filtered

    return render_template(
        "messages.html", messages=new_messages, all_students=all_students
    )


def get_upcoming_follow_ups():
    """Retrieve upcoming follow-ups (future dates) from all student knowledge bases."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    upcoming = []
    students = get_all_students()

    for student in students:
        roll_no = student["roll_no"]
        kb_content = read_knowledge_base(roll_no)
        if not kb_content:
            continue

        # Find all FOLLOW-UP DATE entries
        pattern = re.compile(r"FOLLOW-UP DATE: (\d{4}-\d{2}-\d{2})")
        dates = pattern.findall(kb_content)

        for follow_up_date in dates:
            if follow_up_date > today_str:
                # Extract the circumstance details (match TYPE and DETAILS)
                circumstance_pattern = re.compile(
                    r"TYPE: (.*?)\nDETAILS: (.*?)\nFOLLOW-UP DATE: "
                    + re.escape(follow_up_date),
                    re.DOTALL,
                )
                match = circumstance_pattern.search(kb_content)
                if match:
                    circumstance_type = match.group(1).strip()
                    details = match.group(2).strip()
                    upcoming.append(
                        {
                            "student": student,
                            "circumstance_type": circumstance_type,
                            "details": details,
                            "follow_up_date": follow_up_date,
                            "suggested_message": generate_follow_up_message(
                                circumstance_type, student
                            ),
                        }
                    )
    # Sort by follow-up date in ascending order
    upcoming.sort(key=lambda x: x["follow_up_date"])
    return upcoming


@app.route("/follow_ups")
def follow_ups():
    """Show follow-ups for today or display upcoming follow-ups if none for today."""
    follow_ups_today = check_follow_ups()

    if follow_ups_today:
        message = None
        followups_to_display = follow_ups_today
    else:
        followups_to_display = get_upcoming_follow_ups()
        message = (
            "No follow-ups are scheduled for today. Here are the upcoming follow-ups:"
        )

    return render_template(
        "follow_ups.html", follow_ups=followups_to_display, message=message
    )


@app.route("/send_message", methods=["POST"])
def send_message():
    """Send a message to a student"""
    student_email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")
    roll_no = request.form.get("roll_no")

    if not all([student_email, subject, message, roll_no]):
        flash("All fields are required!")
        return redirect(request.referrer or url_for("students_list"))

    # Send the email
    if send_email(student_email, subject, message):
        # Record in knowledge base
        add_interaction(
            roll_no, f"SUBJECT: {subject}\nBODY: {message}", is_from_student=False
        )
        flash("Message sent successfully!")
    else:
        flash("Failed to send message. Please try again.")

    return redirect(request.referrer or url_for("students_list"))


@app.route("/api/refresh_messages", methods=["POST"])
def api_refresh_messages():
    """API endpoint to refresh messages"""
    new_messages = check_emails()
    return jsonify({"success": True, "message_count": len(new_messages)})


@app.route("/api/update_knowledge_base", methods=["POST"])
def api_update_knowledge_base():
    """API endpoint to update a student's knowledge base"""
    roll_no = request.form.get("roll_no")
    section = request.form.get("section")
    content = request.form.get("content")

    if not all([roll_no, section, content]):
        return jsonify({"success": False, "error": "Missing required fields"})

    if update_knowledge_base(roll_no, section, content):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to update knowledge base"})


# Run the app if executed directly
if __name__ == "__main__":
    # Check if student data CSV exists
    csv_path = os.path.join(CONFIG["data_dir"], "student_data.csv")
    if not os.path.exists(csv_path):
        print(f"Error: Student data file not found at {csv_path}")
        print("Please place student_data.csv in the data directory")
        exit(1)

    # Load student data from CSV
    load_student_data()

    # Start the Flask app
    app.run(debug=True, port=5000)

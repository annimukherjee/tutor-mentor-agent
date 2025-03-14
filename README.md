# AI Tutor Mentoring System

A smart assistant that helps professors manage student mentoring by automating communication tracking, context maintenance, and follow-ups.

## Why This Exists

* **Problem**: Professors mentoring large groups of students (80+) struggle to keep track of individual circumstances and conversations
* **Challenge**: Mental workload of remembering each student's context leads to oversight and missed follow-ups
* **Solution**: AI-powered system that maintains contextual knowledge for each student and suggests timely follow-ups

## Key Features

* **Intelligent Email Processing**: Recognizes emails with "[MENTOR-COMMUNICATION]" tag in subject line
* **Context-Aware Knowledge Base**: Builds and maintains a profile for each student
* **Automated Situation Detection**: Identifies leave requests, medical issues, etc.
* **Smart Follow-up System**: Reminds the professor to check in with students at appropriate times
* **Professor-in-the-Loop Design**: AI suggests responses for the professor to review and send

## How It Works

* Students email their mentor/professor with the "[MENTOR-COMMUNICATION]" tag in the subject
* The system scans the professor's inbox for these communications
* Natural language processing identifies the type of request (leave, medical issue, etc.)
* Information is stored in the student's knowledge base for future context
* The system schedules appropriate follow-ups based on the detected situation
* The professor reviews and sends AI-suggested responses through a simple web interface

## Technology Stack

* **Backend**: Python with Flask
* **Data Processing**: Pandas, NumPy, NLTK
* **Data Storage**: Text-based knowledge bases, Excel for student data
* **Email Integration**: IMAP/SMTP for email processing
* **UI**: Bootstrap-based responsive web interface

## Getting Started

1. Place your student data CSV in the `data` directory
2. Configure the professor's email settings in the app
3. Run `python app.py` to start the local server
4. Access the dashboard at http://localhost:5000

## Screenshot

![AI Tutor Mentoring System Dashboard](dashboard-screenshot.png)



## Setting Up Email Credentials

To run the AI Tutor Mentoring System with your email credentials:

1. Create a virtual environment:


2. Install the python-dotenv package:
   ```
   pip install -r requirements.txt
   ```

3. Create a file named `.env` in the project root directory.

4. Add your email credentials to the `.env` file:
   ```
   PROFESSOR_EMAIL=your.email@gmail.com
   PROFESSOR_PASSWORD=your_email_password
   ```

5. Optional: Customize email server settings if needed:
   ```
   IMAP_SERVER=imap.gmail.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

### Note for Gmail Users

If you're using Gmail, you'll need to:

1. Enable 2-Step Verification on your Google account
2. Generate an App Password specifically for this application
3. Use the App Password instead of your regular Google account password

This is because Google blocks sign-in attempts from apps that don't use modern security standards.

### Security Best Practices

- Never commit your `.env` file to version control
- Include `.env` in your `.gitignore` file
- Use different App Passwords for different applications
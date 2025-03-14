# This is a simple test function to verify the email filtering logic
# You can add this to app.py or run it separately to test the email filtering

def test_email_filter():
    """
    Test function to verify the email filtering logic for [MENTOR-COMMUNICATION]
    This simulates processing different types of emails
    """
    
    # Example emails with different subjects
    test_emails = [
        {
            "from": "student1@example.com",
            "subject": "[MENTOR-COMMUNICATION] Leave request for next week",
            "body": "Dear Professor, I need to take leave for 5 days due to a family emergency."
        },
        {
            "from": "student2@example.com",
            "subject": "Question about the assignment",
            "body": "Hello, I have a question about the latest assignment."
        },
        {
            "from": "student3@example.com",
            "subject": "[MENTOR-COMMUNICATION] Medical leave notification",
            "body": "I'm currently in the hospital and will be absent for a few days."
        },
        {
            "from": "student4@example.com", 
            "subject": "RE: [MENTOR-COMMUNICATION] Previous discussion",
            "body": "Following up on our previous conversation."
        }
    ]
    
    # Process each email using our filter logic
    for email in test_emails:
        should_process = "[MENTOR-COMMUNICATION]" in email["subject"]
        print(f"Email from: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Should process: {'YES' if should_process else 'NO'}")
        print("---")

# Uncomment to run the test
test_email_filter()
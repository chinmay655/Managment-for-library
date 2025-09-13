import smtplib
from email.mime.text import MIMEText
from typing import List

class NotificationService:
    """Handles sending email notifications."""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 smtp_user: str, smtp_password: str, sender_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender_email = sender_email
    
    def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Send a single email."""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string())
            
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {e}")
            return False
    
    def send_bulk_emails(self, recipient_emails: List[str], subject: str, body: str) -> int:
        """Send email to multiple recipients."""
        sent_count = 0
        for email in recipient_emails:
            if self.send_email(email, subject, body):
                sent_count += 1
        return sent_count
    
    def send_overdue_reminders(self, overdue_books: List[dict]) -> int:
        """Send overdue reminders to members."""
        sent_count = 0
        for item in overdue_books:
            member = item['member']
            book = item['book']
            days_overdue = item['days_overdue']
            
            subject = f"Overdue Book Reminder: {book.title}"
            body = f"""Dear {member.name},

This is a reminder that the book '{book.title}' is {days_overdue} days overdue. 
Please return it as soon as possible.

Thank you,
Community Library"""
            
            if self.send_email(member.email, subject, body):
                sent_count += 1
        
        return sent_count

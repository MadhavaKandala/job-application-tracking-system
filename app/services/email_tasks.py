import os
from celery import Celery
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def send_email_task(to_email: str, subject: str, content: str):
    if settings.SENDGRID_API_KEY == "SG.mock":
        print(f"[MOCK EMAIL] To: {to_email} | Subject: {subject} | Body: {content}")
        return {"status": "mock_sent"}
    
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return {"status": "sent", "code": response.status_code}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task
def send_application_submitted_email(to_email: str, job_title: str):
    subject = f"Application Received: {job_title}"
    content = f"<p>Thank you for applying to <strong>{job_title}</strong>. We have received your application.</p>"
    send_email_task.delay(to_email, subject, content)

@celery_app.task
def send_new_application_email(recruiter_email: str, job_title: str):
    subject = f"New Candidate for {job_title}"
    content = f"<p>A new candidate has applied for <strong>{job_title}</strong>.</p>"
    send_email_task.delay(recruiter_email, subject, content)

@celery_app.task
def send_stage_changed_email(to_email: str, job_title: str, new_stage: str):
    subject = f"Update on your application for {job_title}"
    content = f"<p>Your application status has been updated to: <strong>{new_stage}</strong></p>"
    send_email_task.delay(to_email, subject, content)

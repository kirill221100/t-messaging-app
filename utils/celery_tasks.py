from celery import Celery
from pydantic import EmailStr
from security.email import email_changing, email_verification, login_email
from config import config
import smtplib
from email.message import EmailMessage

celery = Celery(__name__, broker=f"amqp://{config.RABBITMQ_USER}:{config.RABBITMQ_PASS}@rabbitmq:5672/",
                backend=f"redis://{config.REDIS_USER}:{config.REDIS_PASSWORD}@{config.REDIS_URL}",
                result_expires=config.CELERY_RESULT_EXP)


def send_email(email: EmailMessage):
    with smtplib.SMTP_SSL(config.MAIL_SERVER, config.MAIL_PORT) as server:
        server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
        server.send_message(email)


@celery.task
def send_email_verification(email: EmailStr, code: str):
    email = email_verification(email, code)
    send_email(email)


@celery.task
def send_email_changing(new_email: EmailStr, code: str):
    email = email_changing(new_email, code)
    send_email(email)


@celery.task
def send_login_email(email: EmailStr, code: str):
    email = login_email(email, code)
    send_email(email)

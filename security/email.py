from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from config import config
from pydantic import EmailStr


email_config = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM="t@mail.com",
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="T",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

mail = FastMail(email_config)


async def send_email_verification(email: EmailStr, code: str, back_tasks: BackgroundTasks):
    html = f"""{code}"""
    message = MessageSchema(
        subject="[T] Подтверждение почты",
        recipients=[email],
        body=html,
        subtype=MessageType.html)
    if config.DEBUG:
        await mail.send_message(message)
        return True
    back_tasks.add_task(mail.send_message, message)
    return True


async def send_login_email(email: EmailStr, code: str, back_tasks: BackgroundTasks):
    html = f"""{code}"""
    message = MessageSchema(
        subject="[T] Введите код на странице входа",
        recipients=[email],
        body=html,
        subtype=MessageType.html)
    if config.DEBUG:
        await mail.send_message(message)
        return True
    back_tasks.add_task(mail.send_message, message)
    return True


async def send_email_changing(new_email: EmailStr, code: str, back_tasks: BackgroundTasks):
    html = f"""{code}"""
    message = MessageSchema(
        subject="[T] Подтверждение изменения почты",
        recipients=[new_email],
        body=html,
        subtype=MessageType.html)
    if config.DEBUG:
        await mail.send_message(message)
        return True
    back_tasks.add_task(mail.send_message, message)
    return {'msg': 'Email change was sent'}

from pydantic import EmailStr
from email.message import EmailMessage


def email_verification(email: EmailStr, code: str):
    html = f"""{code}"""
    message = EmailMessage()
    message['Subject'] = "[T] Подтверждение почты"
    message['From'] = "t@mail.com"
    message['To'] = email
    message.set_content(html)
    return message


def login_email(email: EmailStr, code: str):
    html = f"""{code}"""
    message = EmailMessage()
    message['Subject'] = "[T] Введите код на странице входа"
    message['From'] = "t@mail.com"
    message['To'] = email
    message.set_content(html)
    return message


def email_changing(new_email: EmailStr, code: str):
    html = f"""{code}"""
    message = EmailMessage()
    message['Subject'] = "[T] Подтверждение изменения почты"
    message['From'] = "t@mail.com"
    message['To'] = new_email
    message.set_content(html)
    return message

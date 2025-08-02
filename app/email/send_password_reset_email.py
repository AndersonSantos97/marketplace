import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List
from sqlmodel import select
from fastapi import HTTPException
import os

# Configuración de email (agregar a tu archivo de configuración)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

def send_password_reset_email(user_email: str, user_name: str, reset_link: str):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = user_email
    msg["Subject"] = "Restablecimiento de contraseña"

    body = f"""
    <p>Hola {user_name},</p>
    <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Este enlace expirará en 1 hora.</p>
    """
    msg.attach(MIMEText(body, "html"))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_FROM, user_email, msg.as_string())
    server.quit()


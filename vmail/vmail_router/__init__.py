"""
Implements the vmail_router module for vmail.
"""
import hashlib
import logging
import math
import random
import typing

import fastapi_mail

from ..config import get_settings

__version__ = "0.3.0"

L = logging.getLogger("vmail_router")

settings = get_settings()

mail_conf = fastapi_mail.ConnectionConfig(
    MAIL_USERNAME=settings.smtp_user,
    MAIL_PASSWORD=settings.smtp_password,
    MAIL_FROM=settings.smtp_from,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_FROM_NAME=settings.smtp_name,
    MAIL_STARTTLS=settings.smtp_starttls,
    MAIL_SSL_TLS=settings.smtp_ssl,
    USE_CREDENTIALS=settings.smtp_credentials,
    VALIDATE_CERTS=settings.smtp_checkcerts,
    TEMPLATE_FOLDER=settings.template_path,
)


def create_otp() -> str:
    """
    Create a random one time passcode.

    Returns:
        Random string of length settings.otp_digitsm defaults to 6
    """
    digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    otp_str = ""
    try:
        ndigits = settings.otp_digits
    except AttributeError:
        ndigits = 6
    for i in range(0, ndigits):
        idx = math.floor(random.random() * 10)
        otp_str += digits[idx]
    return otp_str


def hash_something(text: str) -> str:
    """
    Create a unique hash string for the provided input. This should not be used
    to encrypt passwords, but rather to obfuscate unique strings like email addresses.

    Args:
        text: Unique string

    Returns:
        Unique string obfustaced
    """
    h = hashlib.new("sha256")
    h.update(settings.verify_seed.encode("utf-8"))
    h.update(text.encode("utf-8"))
    return h.hexdigest()


async def send_verification_email(
    email: str,
    otp: str,
    verify_url: str,
    name: typing.Optional[str] = None,
    app_name: typing.Optional[str] = None,
) -> bool:
    L.debug("send_verification_email")
    if name is None:
        name = email
    if app_name is None:
        app_name = ""
    message = fastapi_mail.MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[
            email,
        ],
        template_body={
            "name": name,
            "email": email,
            "url": verify_url,
            "otp": otp,
            "application_name": app_name,
        },
        subtype=fastapi_mail.MessageType.html,
    )
    fm = fastapi_mail.FastMail(mail_conf)
    L.debug(f"Sending to {email}")
    try:
        await fm.send_message(message, template_name="verify_email.html")
        L.debug(f"Message sent to {email}")
        return True
    except Exception as e:
        L.error(e)
    return False

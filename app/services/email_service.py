# app/services/email_service.py
import os
import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")
RESEND_FROM_NAME = os.getenv("RESEND_FROM_NAME", "Stack From Scratch")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_otp_email(to_email: str, user_name: str, otp: str):
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY is not set")

    if not RESEND_FROM_EMAIL:
        raise ValueError("RESEND_FROM_EMAIL is not set")

    params: resend.Emails.SendParams = {
        "from": f"{RESEND_FROM_NAME} <{RESEND_FROM_EMAIL}>",
        "to": [to_email],
        "subject": "Your OTP for Email Verification",
        "html": f"""
            <div style="font-family: Arial, sans-serif">
                <h2>Email Verification</h2>
                <p>Hi {user_name},</p>
                <p>Your OTP is:</p>
                <h1>{otp}</h1>
                <p>This OTP is valid for 10 minutes.</p>
            </div>
        """,
        "text": f"Hi {user_name}, your OTP is {otp}. It is valid for 10 minutes.",
    }

    try:
        response = resend.Emails.send(params)
        print("Resend response:", response)
        return response
    except Exception as exc:
        print("Resend error:", repr(exc))
        raise
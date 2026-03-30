# backend/app/services/notification_service.py
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


async def send_telegram(message: str) -> bool:
    """Send message via Telegram bot."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.info("Telegram message sent")
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Telegram error: {text}")
                    return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_email(subject: str, html_body: str, to_email: str = None) -> bool:
    """Send email via SMTP."""
    if not settings.smtp_email or not settings.smtp_password:
        logger.warning("Email not configured")
        return False

    to_email = to_email or settings.smtp_email

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
            logger.info(f"Email sent to {to_email}")
            return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def format_job_notification(jobs: list) -> str:
    """Format jobs for Telegram notification."""
    lines = ["\U0001f514 *New Job Matches Found!*\n"]
    for i, job in enumerate(jobs[:10], 1):
        score = job.get("final_score") or job.get("keyword_score", 0)
        tier = "\U0001f7e2" if score >= 75 else "\U0001f535" if score >= 50 else "\U0001f7e1"
        lines.append(
            f"{tier} *{job['title']}*\n"
            f"   {job.get('company', 'N/A')} | Score: {score}\n"
            f"   [View]({job.get('url', '')})\n"
        )
    return "\n".join(lines)

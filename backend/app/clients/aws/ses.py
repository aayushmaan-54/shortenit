import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.logger import logger

ses_client = boto3.client(
    "ses",
    region_name=settings.aws_default_region,
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_access_key,
)


def send_email(
    to_email: list[str],
    subject: str,
    html_body: str | None = None,
    text_body: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    """
    Send an email using AWS SES;
    sync on purpose (boto3 blocks): run via `BackgroundTasks` (threadpool) or `asyncio.to_thread`;
    failures are logged, not raised, as it usually runs after the response is sent
    """
    if not html_body and not text_body:
        raise ValueError("Email needs an html_body or text_body")

    destination = {"ToAddresses": to_email}
    if cc:
        destination["CcAddresses"] = cc
    if bcc:
        destination["BccAddresses"] = bcc

    body = {}
    if html_body:
        body["Html"] = {"Data": html_body, "Charset": "UTF-8"}
    if text_body:
        body["Text"] = {"Data": text_body, "Charset": "UTF-8"}

    try:
        return ses_client.send_email(
            Source=settings.aws_ses_source_email,
            Destination=destination,
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            },
        )
    except (BotoCoreError, ClientError):
        logger.exception("Failed to send email to %s (subject: %s)", to_email, subject)
        return None

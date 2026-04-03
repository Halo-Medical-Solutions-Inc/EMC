import html
import re
import uuid

import httpx

from app.config import settings


def _preview_text(content: str, max_len: int) -> str:
    text = re.sub(r"<[^>]+>", " ", content)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text


async def notify_platform_support_message(
    author_name: str,
    content: str,
    conversation_id: uuid.UUID,
    is_reply: bool,
) -> None:
    token = settings.SLACK_BOT_TOKEN.strip()
    channel = settings.SLACK_SUPPORT_CHANNEL_ID.strip()
    if not token or not channel:
        return

    preview = _preview_text(content, 280)
    base = settings.FRONTEND_URL.rstrip("/")
    link = f"{base}/messages?conversation={conversation_id}"
    kind = "Reply in a Platform Support thread" if is_reply else "New message in Platform Support"
    text = (
        f"{kind}\n"
        f"From: {author_name}\n"
        f"{preview}\n"
        f"Open: {link}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"channel": channel, "text": text}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers,
            )
    except httpx.RequestError as exc:
        print(f"Slack notify request error: {exc}")
        return

    try:
        data = response.json()
    except ValueError as exc:
        print(f"Slack notify invalid JSON: {exc}")
        return

    if response.status_code != 200:
        print(f"Slack notify HTTP {response.status_code}: {data}")
        return

    if not data.get("ok"):
        print(f"Slack chat.postMessage failed: {data.get('error')}")

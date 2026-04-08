import html
import re
import uuid
from typing import List

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

INTERNAL_CALL_COMMENT_NOTIFY_EMAIL: str = "mandika@halohealth.app"


def _preview_text(content: str, max_len: int) -> str:
    text = content
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text


def _first_name(full_name: str) -> str:
    parts = (full_name or "").strip().split(None, 1)
    return parts[0] if parts else "Someone"


def _safe_slack_plain(value: str) -> str:
    return re.sub(r"[*_`<>&|]", "", value).strip() or "—"


def _quoted_preview(preview: str) -> str:
    inner = preview.replace('"', "'")
    return f'"{inner}"'


def _messaging_slack_text(
    author_name: str,
    content: str,
    conversation_id: uuid.UUID,
) -> str:
    preview = _preview_text(content, 280)
    base = settings.FRONTEND_URL.rstrip("/")
    link = f"{base}/messages?conversation={conversation_id}"
    first = _safe_slack_plain(_first_name(author_name))
    practice = _safe_slack_plain(settings.FROM_NAME)
    quoted = _quoted_preview(preview)
    return (
        f"{practice} ({first})\n\n"
        f"{quoted}\n\n"
        f"→ <{link}|View in Halo>\n"
        f"<!channel>"
    )


async def _post_support_channel_text(text: str) -> None:
    token = settings.SLACK_BOT_TOKEN.strip()
    channel = settings.SLACK_SUPPORT_CHANNEL_ID.strip()
    if not token or not channel:
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "channel": channel,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }

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


async def notify_platform_support_message(
    author_name: str,
    content: str,
    conversation_id: uuid.UUID,
) -> None:
    text = _messaging_slack_text(author_name, content, conversation_id)
    await _post_support_channel_text(text)


def _call_comment_slack_text(
    author_name: str,
    content: str,
    call_id: uuid.UUID,
    slack_user_id: str,
) -> str:
    preview = _preview_text(content, 280)
    base = settings.FRONTEND_URL.rstrip("/")
    link = f"{base}/dashboard?call={call_id}"
    first = _safe_slack_plain(_first_name(author_name))
    practice = _safe_slack_plain(settings.FROM_NAME)
    quoted = _quoted_preview(preview)
    ping = ""
    sid = (slack_user_id or "").strip()
    if sid:
        ping = f"\n<@{sid}>"
    return (
        f"{practice} — Call comment ({first})\n\n"
        f"{quoted}\n\n"
        f"→ <{link}|View call in Halo>"
        f"{ping}"
    )


async def maybe_notify_internal_call_comment_slack(
    db: AsyncSession,
    call_id: uuid.UUID,
    author_id: uuid.UUID,
    content: str,
    at_mentioned_user_ids: List[uuid.UUID],
) -> None:
    email = INTERNAL_CALL_COMMENT_NOTIFY_EMAIL.strip().lower()
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    target = result.scalar_one_or_none()
    if target is None:
        return

    if target.id not in at_mentioned_user_ids:
        return

    author = await db.get(User, author_id)
    author_name = author.full_name if author else "Someone"
    text = _call_comment_slack_text(
        author_name,
        content,
        call_id,
        settings.SLACK_INTERNAL_CALL_MENTION_USER_ID,
    )
    await _post_support_channel_text(text)

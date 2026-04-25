import asyncio
import os
import smtplib
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional, Sequence, Tuple

import pytz
import yagmail
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import AsyncSessionLocal
from app.schemas.analytics import AnalyticsResponse, DoctorBreakdownItem
from app.services import practice_service
from app.services.analytics_service import get_analytics

TEST_ANALYTICS_REPORT_RECIPIENT = "mandika@halohealth.app"
ANALYTICS_REPORT_RECIPIENTS = ["lgiffen@emcfresno.com", "RFrediani@emcfresno.com"]
ANALYTICS_REPORT_CC_RECIPIENTS = ["mandika@halohealth.app"]
DEFAULT_TIMEZONE = "America/Los_Angeles"
PRACTICE_DISPLAY_NAME = "Eye Medical Center of Fresno"
MONTHLY_REPORT_HOUR = 7
MONTHLY_REPORT_MINUTE = 0


@dataclass(frozen=True)
class AnalyticsReportResult:
    recipients: List[str]
    cc_recipients: List[str]
    subject: str
    filename: str
    start_datetime: str
    end_datetime: str
    timezone: str
    total_calls: int


class AnalyticsReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_test_month_to_date_report(self) -> AnalyticsReportResult:
        timezone = await self._get_practice_timezone()
        start_dt, end_dt = self._get_current_month_range(timezone)
        return await self._send_report(
            recipients=[TEST_ANALYTICS_REPORT_RECIPIENT],
            cc_recipients=[],
            start_dt=start_dt,
            end_dt=end_dt,
            is_previous_month_report=False,
        )

    async def send_previous_month_report(self) -> AnalyticsReportResult:
        timezone = await self._get_practice_timezone()
        start_dt, end_dt = self._get_previous_month_range(timezone)
        return await self._send_report(
            recipients=ANALYTICS_REPORT_RECIPIENTS,
            cc_recipients=ANALYTICS_REPORT_CC_RECIPIENTS,
            start_dt=start_dt,
            end_dt=end_dt,
            is_previous_month_report=True,
        )

    async def _send_report(
        self,
        recipients: List[str],
        cc_recipients: List[str],
        start_dt: datetime,
        end_dt: datetime,
        is_previous_month_report: bool,
    ) -> AnalyticsReportResult:
        analytics = await get_analytics(
            self.db,
            start_dt.astimezone(pytz.UTC),
            end_dt.astimezone(pytz.UTC),
        )
        subject = self._build_subject(start_dt, end_dt)
        filename = self._build_filename(start_dt)
        pdf_bytes = self._build_pdf(analytics, start_dt, end_dt)
        self._send_email(
            recipients,
            cc_recipients,
            subject,
            pdf_bytes,
            filename,
            analytics,
            start_dt,
            end_dt,
            is_previous_month_report,
        )
        return AnalyticsReportResult(
            recipients=recipients,
            cc_recipients=cc_recipients,
            subject=subject,
            filename=filename,
            start_datetime=start_dt.isoformat(),
            end_datetime=end_dt.isoformat(),
            timezone=timezone,
            total_calls=analytics.cards.total_calls,
        )

    async def _get_practice_timezone(self) -> str:
        practice = await practice_service.get_practice(self.db)
        timezone = practice.practice_region if practice else DEFAULT_TIMEZONE
        try:
            pytz.timezone(timezone or DEFAULT_TIMEZONE)
            return timezone or DEFAULT_TIMEZONE
        except pytz.UnknownTimeZoneError:
            return DEFAULT_TIMEZONE

    def _get_current_month_range(self, timezone: str) -> Tuple[datetime, datetime]:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        start_dt = tz.localize(datetime(now.year, now.month, 1, 0, 0, 0, 0))
        return start_dt, now

    def _get_previous_month_range(self, timezone: str) -> Tuple[datetime, datetime]:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        current_month_start = tz.localize(datetime(now.year, now.month, 1, 0, 0, 0, 0))
        previous_month_end = current_month_start - timedelta(microseconds=1)
        previous_month_start = tz.localize(
            datetime(previous_month_end.year, previous_month_end.month, 1, 0, 0, 0, 0)
        )
        return previous_month_start, previous_month_end

    def _build_subject(self, start_dt: datetime, end_dt: datetime) -> str:
        return (
            "Halo Back Office Receptionist Report – "
            f"{start_dt.strftime('%b %-d')} to {end_dt.strftime('%b %-d, %Y')}"
        )

    def _build_filename(self, start_dt: datetime) -> str:
        return f"analytics-report-{start_dt.strftime('%Y-%m')}.pdf"

    def _build_pdf(
        self,
        analytics: AnalyticsResponse,
        start_dt: datetime,
        end_dt: datetime,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            title="Halo Back Office Receptionist Report",
        )
        styles = self._get_styles()
        period = self._format_report_period_phrase(start_dt, end_dt)
        elements: List[Flowable] = [
            Paragraph("Halo Back Office Receptionist Report", styles["Title"]),
            Paragraph(
                f"{PRACTICE_DISPLAY_NAME} · {period}",
                styles["Muted"],
            ),
            Spacer(1, 0.18 * inch),
            self._build_metric_table(analytics),
            Spacer(1, 0.2 * inch),
            Paragraph("Call Flow by Intent", styles["Heading2"]),
            self._build_flow_visual(
                self._intent_flow_items(analytics),
                analytics.sankey.by_intent.total,
            ),
            Spacer(1, 0.16 * inch),
            Paragraph("Transferred Destinations", styles["Heading2"]),
            self._build_breakdown_table(
                analytics.sankey.by_intent.transferred_extensions,
                "Destination",
            ),
            Spacer(1, 0.16 * inch),
            Paragraph("Doctor Breakdown", styles["Heading2"]),
            self._build_doctor_table(analytics.doctor_breakdown),
        ]
        doc.build(elements)
        return buffer.getvalue()

    def _get_styles(self) -> Dict[str, ParagraphStyle]:
        styles = getSampleStyleSheet()
        styles["Title"].fontName = "Helvetica-Bold"
        styles["Title"].fontSize = 18
        styles["Title"].leading = 22
        styles["Title"].textColor = colors.HexColor("#111827")
        styles["Heading2"].fontName = "Helvetica-Bold"
        styles["Heading2"].fontSize = 12
        styles["Heading2"].leading = 15
        styles["Heading2"].textColor = colors.HexColor("#111827")
        styles.add(
            ParagraphStyle(
                name="Muted",
                parent=styles["Normal"],
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#6b7280"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="Right",
                parent=styles["Normal"],
                alignment=TA_RIGHT,
                fontSize=8,
                leading=10,
            )
        )
        return styles

    def _build_metric_table(self, analytics: AnalyticsResponse) -> Table:
        cards = analytics.cards
        data = [
            [
                "Total Calls",
                "Avg Duration",
                "Review Completion",
                "Avg Review Time",
            ],
            [
                str(cards.total_calls),
                self._format_duration(cards.avg_call_duration_seconds),
                self._format_percentage(cards.review_completion_rate),
                self._format_review_time(cards.avg_review_time_minutes),
            ],
        ]
        table = Table(data, colWidths=[1.85 * inch] * 4)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#374151")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, 1), 15),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#111827")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return table

    def _intent_flow_items(
        self,
        analytics: AnalyticsResponse,
    ) -> List[Tuple[str, int, Color]]:
        sankey = analytics.sankey.by_intent
        items: List[Tuple[str, int, Color]] = []
        if sankey.transferred > 0:
            items.append(
                ("Transferred", sankey.transferred, colors.HexColor("#0891b2"))
            )
        palette = [
            "#1d4ed8",
            "#7e22ce",
            "#be185d",
            "#b45309",
            "#0e7490",
            "#4338ca",
            "#9333ea",
            "#dc2626",
            "#0f766e",
            "#c2410c",
            "#15803d",
            "#4f46e5",
        ]
        sorted_intents = sorted(
            sankey.non_transferred_intents.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        for index, (label, count) in enumerate(sorted_intents):
            if count > 0:
                items.append(
                    (label, count, colors.HexColor(palette[index % len(palette)]))
                )
        return items

    def _build_flow_visual(
        self,
        items: Sequence[Tuple[str, int, Color]],
        total: int,
    ) -> Drawing:
        width = 520
        row_height = 24
        height = max(60, len(items) * row_height + 14)
        drawing = Drawing(width, height)
        if total <= 0 or not items:
            drawing.add(String(0, height - 20, "No data for this period", fontSize=9))
            return drawing

        max_value = max(count for _, count, _ in items)
        bar_left = 140
        bar_width = 270
        y = height - 22
        for label, count, color in items:
            width_ratio = count / max_value if max_value else 0
            current_width = max(2, bar_width * width_ratio)
            percent = count / total
            drawing.add(String(0, y + 2, self._truncate(label, 30), fontSize=8))
            drawing.add(
                Rect(bar_left, y, current_width, 10, fillColor=color, strokeColor=color)
            )
            drawing.add(
                String(
                    bar_left + bar_width + 12,
                    y + 2,
                    f"{count} ({self._format_percentage(percent)})",
                    fontSize=8,
                )
            )
            y -= row_height
        return drawing

    def _build_breakdown_table(
        self,
        values: Dict[str, int],
        label_heading: str,
    ) -> Table:
        rows = [[label_heading, "Calls"]]
        for label, count in sorted(
            values.items(), key=lambda item: item[1], reverse=True
        ):
            rows.append([label, str(count)])
        if len(rows) == 1:
            rows.append(["No transferred calls", "0"])
        table = Table(rows, colWidths=[5.8 * inch, 1.4 * inch])
        table.setStyle(self._standard_table_style())
        return table

    def _build_doctor_table(self, doctors: List[DoctorBreakdownItem]) -> Table:
        rows = [
            ["Doctor", "Calls", "Reviewed", "Needs Review", "Review %", "Avg Review"]
        ]
        for doctor in doctors:
            rows.append(
                [
                    doctor.doctor_name,
                    str(doctor.total_calls),
                    str(doctor.reviewed),
                    str(doctor.needs_review),
                    self._format_percentage(doctor.review_completion_rate),
                    self._format_optional_review_time(doctor.avg_review_time_minutes),
                ]
            )
        if len(rows) == 1:
            rows.append(["No doctors", "0", "0", "0", "0%", "-"])
        table = Table(
            rows,
            colWidths=[
                2.35 * inch,
                0.75 * inch,
                0.9 * inch,
                1.0 * inch,
                0.8 * inch,
                1.0 * inch,
            ],
            repeatRows=1,
        )
        table.setStyle(self._standard_table_style())
        return table

    def _standard_table_style(self) -> TableStyle:
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#111827")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )

    def _send_email(
        self,
        recipients: List[str],
        cc_recipients: List[str],
        subject: str,
        pdf_bytes: bytes,
        filename: str,
        analytics: AnalyticsResponse,
        start_dt: datetime,
        end_dt: datetime,
        is_previous_month_report: bool,
    ) -> None:
        contents = self._build_email_body(
            analytics,
            start_dt,
            end_dt,
            is_previous_month_report,
        )
        temp_dir = ""
        temp_path = ""
        try:
            temp_dir = tempfile.mkdtemp(prefix="analytics-report-")
            temp_path = os.path.join(temp_dir, filename)
            with open(temp_path, "wb") as temp_file:
                temp_file.write(pdf_bytes)
            yag = yagmail.SMTP(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            send_kwargs = {
                "to": recipients,
                "subject": subject,
                "contents": contents,
                "attachments": [temp_path],
            }
            if cc_recipients:
                send_kwargs["cc"] = cc_recipients
            yag.send(**send_kwargs)
        except (OSError, smtplib.SMTPException, ValueError) as exc:
            raise RuntimeError("Failed to send analytics report email") from exc
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError as exc:
                    print(f"Failed to delete analytics report temp file: {exc}")
            if temp_dir:
                try:
                    os.rmdir(temp_dir)
                except OSError as exc:
                    print(f"Failed to delete analytics report temp directory: {exc}")

    def _format_report_period_phrase(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> str:
        if start_dt.date() == end_dt.date():
            return start_dt.strftime("%B %-d, %Y")
        if start_dt.year == end_dt.year and start_dt.month == end_dt.month:
            return f"{start_dt.strftime('%B %-d')} through {end_dt.strftime('%-d, %Y')}"
        return (
            f"{start_dt.strftime('%B %-d, %Y')} through {end_dt.strftime('%B %-d, %Y')}"
        )

    def _build_email_body(
        self,
        analytics: AnalyticsResponse,
        start_dt: datetime,
        end_dt: datetime,
        is_previous_month_report: bool,
    ) -> List[str]:
        period = self._format_report_period_phrase(start_dt, end_dt)
        if is_previous_month_report:
            opening = (
                "Please find last month's Halo Back Office Receptionist analytics "
                f"report for {PRACTICE_DISPLAY_NAME} attached to this email, "
                f"covering {period} ({analytics.cards.total_calls} completed calls "
                "in scope)."
            )
        else:
            opening = (
                "Please find the Halo Back Office Receptionist report for "
                f"{PRACTICE_DISPLAY_NAME} attached, covering {period} "
                f"({analytics.cards.total_calls} completed calls in scope)."
            )
        text_body = f"""Hi Lisa and Robert,

We hope you are well. {opening}

This PDF mirrors the high-level view from your practice analytics, distilled for a quick read. If you would like a walkthrough, a different cut of the data, or have any questions, we will be glad to help.

Warmly,
The Halo Team
"""
        html_body = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px 20px;font-family:Georgia,serif;font-size:15px;line-height:1.55;color:#1f2937;max-width:560px;">
<p style="margin:0 0 16px 0;">Hi Lisa and Robert,</p>
<p style="margin:0 0 16px 0;">We hope you are well. {opening}</p>
<p style="margin:0 0 16px 0;">It reflects the same metrics you use in the analytics workspace, presented in a single PDF for easy review. If you would like a walkthrough, a different view of the numbers, or have any questions, we are here to help.</p>
<p style="margin:24px 0 0 0;">Warmly,<br/>The Halo Team</p>
</body>
</html>"""
        return [text_body, html_body]

    def _format_duration(self, seconds: float) -> str:
        if seconds == 0:
            return "0s"
        if seconds < 60:
            return f"{round(seconds)}s"
        minutes = int(seconds // 60)
        remaining_seconds = round(seconds % 60)
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"

    def _format_review_time(self, minutes: float) -> str:
        if minutes == 0:
            return "0 min"
        if minutes < 60:
            return f"{round(minutes)} min"
        hours = int(minutes // 60)
        remaining_minutes = round(minutes % 60)
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"

    def _format_optional_review_time(self, minutes: Optional[float]) -> str:
        if minutes is None:
            return "-"
        return self._format_review_time(minutes)

    def _format_percentage(self, value: float) -> str:
        return f"{round(value * 100, 1)}%"

    def _truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return f"{value[: max_length - 3]}..."


def get_next_monthly_report_run(now: Optional[datetime] = None) -> datetime:
    tz = pytz.timezone(DEFAULT_TIMEZONE)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    scheduled = tz.localize(
        datetime(
            local_now.year,
            local_now.month,
            1,
            MONTHLY_REPORT_HOUR,
            MONTHLY_REPORT_MINUTE,
            0,
            0,
        )
    )
    if local_now < scheduled:
        return scheduled
    if local_now.month == 12:
        return tz.localize(
            datetime(
                local_now.year + 1,
                1,
                1,
                MONTHLY_REPORT_HOUR,
                MONTHLY_REPORT_MINUTE,
                0,
                0,
            )
        )
    return tz.localize(
        datetime(
            local_now.year,
            local_now.month + 1,
            1,
            MONTHLY_REPORT_HOUR,
            MONTHLY_REPORT_MINUTE,
            0,
            0,
        )
    )


async def send_scheduled_previous_month_analytics_report() -> AnalyticsReportResult:
    async with AsyncSessionLocal() as db:
        return await AnalyticsReportService(db).send_previous_month_report()


async def run_monthly_analytics_report_loop() -> None:
    while True:
        next_run = get_next_monthly_report_run()
        wait_seconds = max(
            1.0, (next_run - datetime.now(next_run.tzinfo)).total_seconds()
        )
        print(
            "[ANALYTICS REPORT] Next monthly report scheduled for "
            f"{next_run.isoformat()}"
        )
        try:
            await asyncio.sleep(wait_seconds)
            result = await send_scheduled_previous_month_analytics_report()
            print(
                "[ANALYTICS REPORT] Sent monthly report to "
                f"{', '.join(result.recipients)}"
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[ANALYTICS REPORT] Failed to send monthly report: {exc}")

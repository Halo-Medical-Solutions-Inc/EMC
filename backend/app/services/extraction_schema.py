from typing import Any, Dict, List, Optional

DEFAULT_PROVIDER_NAMES: List[str] = [
    "Dr. Bertolucci",
    "Dr. Prescott",
    "Dr. Thinda",
    "Dr. Teasley",
    "Dr. Mehta",
    "Dr. Ghajar",
    "Other",
    "Not Provided",
]

PROVIDER_STAFF_DIRECTORY: List[Dict[str, Any]] = []

DEPARTMENT_STAFF_DIRECTORY: List[Dict[str, Any]] = []

_TEAMS_OTHER_LABEL = "Other"

_PROVIDER_TO_CALL_TEAMS_MAP = (
    "Map provider_name to call_teams using the doctor's personal team: "
    "Dr. Bertolucci → George Bertolucci; Dr. Prescott → Daniel Prescott; "
    "Dr. Thinda → Sumeer Thinda; Dr. Teasley → Laura Teasley; Dr. Mehta → Neesurg Mehta; "
    "Dr. Ghajar → Mehdi Ghajar (corneal refractive surgery, LASIK, cross-linking)."
)

_TEAMS_FIELD_SUFFIX = (
    f"{_PROVIDER_TO_CALL_TEAMS_MAP} "
    "Each retina specialist has their own team bucket (there is no shared Retina department team). "
    f"Use '{_TEAMS_OTHER_LABEL}' when the call does not belong to any listed provider team "
    "(billing-only, general info, unknown provider, spam, or providers outside these six)."
)


def _call_teams_field_description(team_names_str: str) -> str:
    return (
        "All teams this call is associated with. "
        "A call can belong to multiple teams. "
        "Select all that apply based on the call content, provider, and context. "
        "Infer the best match from available teams even when transcript has errors. "
        f"Available teams: {team_names_str}. "
        + _TEAMS_FIELD_SUFFIX
    )


def build_staff_extension_map(
    provider_directory: List[Dict[str, Any]],
    department_directory: List[Dict[str, Any]],
) -> str:
    lines: List[str] = [
        "Staff extension directory — if the caller mentions a staff member "
        "by name or requests a specific extension number, use this lookup "
        "to resolve the correct provider:",
    ]
    for entry in provider_directory:
        provider = entry["provider"]
        parts = [f"Ext {entry['provider_ext']}: {provider}"]
        for s in entry["staff"]:
            parts.append(f"{s['name']} ({s['role']}, ext {s['ext']})")
        lines.append(f"  {' / '.join(parts)} -> {provider}")
    lines.append(
        "Department staff (no assigned provider — use best judgment from call context):"
    )
    for dept in department_directory:
        lines.append(f"  Ext {dept['ext']}: {dept['contact']} ({dept['department']})")
    if provider_directory or department_directory:
        lines.append(
            "If a caller mentions a staff member by name or extension, "
            "match to the most relevant provider based on call context."
        )
    return "\n".join(lines)


DEFAULT_PRIORITY_LOW = (
    "Routine appointment scheduling, prescription refills, billing questions, "
    "medical records requests, general inquiries, LASIK information, outgoing referral status checks."
)
DEFAULT_PRIORITY_MEDIUM = (
    "Non-urgent symptom reports (e.g. mild discomfort, blurry vision, redness, dryness), "
    "medication questions, incoming referral status, appointment changes, test results."
)
DEFAULT_PRIORITY_HIGH = (
    "Transfer-triggering symptoms (floaters/flashes, curtain or cobwebs in vision, "
    "signs of infection, suture concerns, extreme or unusual pain), ER/urgent care/discharge follow-ups, "
    "calls from outside practices or hospitals, severely escalated callers, "
    "or anything requiring same-day or immediate attention."
)


def _build_priority_description(custom: Optional[Dict[str, str]] = None) -> str:
    low = (custom or {}).get("low") or DEFAULT_PRIORITY_LOW
    medium = (custom or {}).get("medium") or DEFAULT_PRIORITY_MEDIUM
    high = (custom or {}).get("high") or DEFAULT_PRIORITY_HIGH
    return f"Urgency level of the call. Low: {low} Medium: {medium} High: {high}"


def build_extraction_schema(
    provider_names: List[str],
    team_names: Optional[List[str]] = None,
    staff_extension_map: Optional[str] = None,
    priority_descriptions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    provider_enum = (
        provider_names
        if "Not Provided" in provider_names
        else provider_names + ["Not Provided"]
    )
    provider_names_str = ", ".join(provider_names)

    provider_description = (
        "Provider the caller is asking for. "
        "Match to the closest option in the enum even when the transcript has "
        "typos or misheard names (e.g. 'Gajar' or 'Doctor Gahar' → Dr. Ghajar)."
    )
    if staff_extension_map:
        provider_description += f" {staff_extension_map}"

    fields: List[Dict[str, Any]] = [
        {
            "name": "caller_name",
            "type": "string",
            "description": "Name of the person calling",
        },
        {
            "name": "caller_affiliation",
            "type": "string",
            "description": "Relationship of caller to the patient",
            "enum": [
                "Patient",
                "Family Member",
                "Caregiver",
                "Pharmacy",
                "Other Provider",
                "Hospital",
                "Insurance",
                "Other",
                "Not Provided",
            ],
        },
        {
            "name": "patient_dob",
            "type": "string",
            "description": "Date of birth of the patient",
        },
        {
            "name": "patient_name",
            "type": "string",
            "description": "Name of the patient the call is about",
        },
        {
            "name": "provider_name",
            "type": "string",
            "description": provider_description,
            "enum": provider_enum,
        },
        {
            "name": "primary_intent",
            "type": "string",
            "description": "Main reason for the call",
            "enum": [
                "Appointment (New/Reschedule/Cancel)",
                "Prescription Refill",
                "Test Results",
                "Referral Request",
                "Medical Records",
                "Billing/Insurance Question",
                "Speak to Staff",
                "Report Symptoms",
                "Prior Authorization",
                "Spam/Wrong Number",
                "Other",
                "Not Provided",
            ],
        },
        {
            "name": "priority",
            "type": "string",
            "description": _build_priority_description(priority_descriptions),
            "enum": [
                "Low",
                "Medium",
                "High",
                "Not Provided",
            ],
        },
        {
            "name": "summary",
            "type": "string",
            "description": (
                "Direct, concise summary of the call. "
                "The practice name is Eye Medical Center of Fresno — always use this exact name, "
                "never a transcription variant like 'iMedical' or 'I Medical.' "
                "Use the correct provider name from the schema (not transcript typos). "
                f"Available providers: {provider_names_str}."
            ),
        },
        {
            "name": "auto_review",
            "type": "boolean",
            "description": (
                "Whether this call can be automatically marked as reviewed without human review. "
                "Set to true ONLY for spam, wrong numbers, robocalls, or abandoned calls with no "
                "meaningful content. "
                "Set to true if the call was transferred to a live person AND the patient needed "
                "nothing further from this practice after the transfer (no callback, no message "
                "for staff, no prescription or paperwork issue left open). "
                "Set to false if ANY of the following apply — this list is not exhaustive: "
                "scheduling or appointment changes; callbacks; prescription or medication issues "
                "(refill, redirect, pharmacy cannot fill, dosage, timing); post-injection or "
                "post-procedure symptoms or pain; urgent or same-day requests; messages for a "
                "doctor or team; test results; referrals; authorizations; medical records; "
                "billing; insurance; high or urgent priority; confusion, complaint, or escalation; "
                "or any clinical or operational follow-up. "
                "When in doubt, set to false."
            ),
        },
    ]

    if team_names:
        team_names_str = ", ".join(team_names)
        teams_description = _call_teams_field_description(team_names_str)
        if staff_extension_map:
            teams_description += (
                " When the caller mentions a staff name or extension number, "
                "use the staff extension directory (from the provider_name field) "
                "to identify the associated provider(s) and assign the call to "
                "their team(s)."
            )
        fields.append(
            {
                "name": "call_teams",
                "type": "array",
                "items": {"type": "string", "enum": team_names},
                "description": teams_description,
            }
        )

    return {"fields": fields}


DEFAULT_EXTRACTION_SCHEMA: Dict[str, Any] = build_extraction_schema(
    DEFAULT_PROVIDER_NAMES
)

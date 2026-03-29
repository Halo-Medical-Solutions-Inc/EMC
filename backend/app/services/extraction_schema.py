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
    lines.append(
        "Shared staff/extensions: "
        "Daisy (ext 223) is secretary for both Dr. Waider, Winfried "
        "and Dr. Nasr, George — select the most relevant provider based on call context. "
        "Ext 260 is shared by Cathy (Dr. Sklash, Ron's secretary) and "
        "Maryann (Authorizations) — use call context to determine intent. "
        "Cathy also appears as Medical Records contact at ext 264."
    )
    return "\n".join(lines)


def build_extraction_schema(
    provider_names: List[str],
    team_names: Optional[List[str]] = None,
    staff_extension_map: Optional[str] = None,
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
        "typos or misheard names (e.g. 'Slash' or 'Doctor Slash' → Ron Sklash)."
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
            "description": (
                "Urgency level of the call. "
                "Low: routine scheduling, well-child visits, immunizations, "
                "school physicals, prescription refills, billing questions, "
                "medical records requests, general inquiries. "
                "Medium: test results, referrals, non-urgent medical questions, "
                "prenatal consultations. "
                "High: sick child with concerning symptoms, high fever in infant, "
                "difficulty breathing, severe allergic reaction, "
                "urgent callback requests, "
                "anything requiring same-day or immediate attention."
            ),
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
                "Use the correct provider name from the schema (not transcript typos). "
                f"Available providers: {provider_names_str}."
            ),
        },
        {
            "name": "auto_review",
            "type": "boolean",
            "description": (
                "Whether this call can be automatically marked as reviewed without human review. "
                "Set to true ONLY for spam, wrong numbers, robocalls, abandoned calls with no "
                "meaningful content, or calls where no human follow-up action is needed. "
                "Also set to true if the call was transferred to a live person, since staff "
                "already handled it during the transfer. "
                "Set to false for ANY call that requires staff action such as scheduling, "
                "callbacks, prescription refills, test results, referrals, authorizations, "
                "medical records requests, or any legitimate patient call that was NOT transferred. "
                "When in doubt, set to false."
            ),
        },
    ]

    if team_names:
        team_names_str = ", ".join(team_names)
        teams_description = (
            "All teams this call is associated with. "
            "A call can belong to multiple teams. "
            "Select all that apply based on the call content, provider, and context. "
            "Infer the best match from available teams even when transcript has errors. "
            f"Available teams: {team_names_str}. "
            "Provider-to-team mapping: "
            "Dr. Bertolucci, Dr. Prescott, Dr. Thinda, Dr. Teasley, and Dr. Mehta are all Retina team providers. "
            "Dr. Ghajar belongs to the Dr. Ghajar team (includes LASIK, cross-linking, and corneal refractive surgery). "
            "Use 'Other' only when the call does not involve any of the above providers "
            "(e.g. billing-only, general info, unknown provider, spam, or providers outside these six)."
        )
        if staff_extension_map:
            teams_description += (
                " When the caller mentions a staff name or extension number, "
                "use the staff extension directory (from the provider_name field) "
                "to identify the associated provider(s) and assign the call to "
                "their team(s). For shared staff (e.g. Daisy serves both "
                "Dr. Waider and Dr. Nasr), assign to all applicable teams."
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

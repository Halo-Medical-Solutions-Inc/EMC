import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.call import Call
from app.services import call_service

DOCTOR_TEAMS = [
    "George Nasr",
    "Henry Van Gieson",
    "Mark Young Lee",
    "Natasha Cuk",
    "Ron Sklash",
    "Winfried Waider",
]


async def reassign_other_appointments() -> None:
    async with AsyncSessionLocal() as db:
        print(f"Doctor teams for round-robin: {DOCTOR_TEAMS}")

        query = select(Call).where(
            Call.deleted_at.is_(None),
            Call.extraction_data_encrypted.isnot(None),
        )
        result = await db.execute(query)
        calls = list(result.scalars().all())

        print(f"Scanning {len(calls)} calls with extraction data...")

        candidates = []
        for call in calls:
            extraction_data = call_service.decrypt_extraction_data(call)
            if not extraction_data:
                continue

            call_teams = extraction_data.get("call_teams", [])
            primary_intent = extraction_data.get("primary_intent", "")

            if "Other" in call_teams and "Appointment" in primary_intent:
                candidates.append((call, extraction_data))

        print(f"Found {len(candidates)} Other + Appointment calls to reassign")

        if not candidates:
            return

        candidates.sort(key=lambda x: x[0].created_at)

        reassigned = 0
        for call, extraction_data in candidates:
            selected_team = DOCTOR_TEAMS[reassigned % len(DOCTOR_TEAMS)]

            extraction_data["call_teams"] = [
                selected_team if t == "Other" else t
                for t in extraction_data["call_teams"]
            ]

            await call_service.store_extraction_data(db, call, extraction_data)

            vapi_data = call_service.decrypt_vapi_data(call)
            display_data = call_service.build_display_data(
                vapi_data=vapi_data, extraction_data=extraction_data
            )
            await call_service.store_display_data(db, call, display_data)

            reassigned += 1
            print(
                f"  [{reassigned}/{len(candidates)}] "
                f"Call {call.id} -> {selected_team}"
            )

        print(f"Done. Reassigned {reassigned} calls.")


if __name__ == "__main__":
    asyncio.run(reassign_other_appointments())

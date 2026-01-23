
import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from common.database.postgres_database import SessionLocal
from common.database.postgres_models import MinuteVersion, GuardrailResult

async def check_guardrails():
    print("Checking for Guardrail Results...")
    with SessionLocal() as session:
        # Get the 5 most recent minute versions
        query = (
            select(MinuteVersion)
            .order_by(MinuteVersion.created_datetime.desc())
            .limit(5)
            .options(selectinload(MinuteVersion.guardrail_results))
        )
        result = session.exec(query)
        minute_versions = result.all()

        if not minute_versions:
            print("No minute versions found.")
            return

        for mv in minute_versions:
            print(f"MinuteVersion ID: {mv.id}, Status: {mv.status}, Created: {mv.created_datetime}")
            if mv.guardrail_results:
                print(f"  Found {len(mv.guardrail_results)} guardrail results:")
                for gr in mv.guardrail_results:
                    print(f"    - {gr.guardrail_type}: {gr.result} (Score: {gr.score})")
            else:
                print("  No guardrail results found.")

if __name__ == "__main__":
    asyncio.run(check_guardrails())

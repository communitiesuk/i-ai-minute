import asyncio
from uuid import UUID
from common.database.postgres_database import SessionLocal
from common.database.postgres_models import MinuteVersion, GuardrailResult, Hallucination
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def check():
    async with SessionLocal() as session:
        # Check latest minute versions
        stmt = select(MinuteVersion).order_by(MinuteVersion.created_datetime.desc()).limit(5).options(
            selectinload(MinuteVersion.guardrail_results),
            selectinload(MinuteVersion.hallucinations)
        )
        result = await session.execute(stmt)
        versions = result.scalars().all()
        
        print(f"Found {len(versions)} recent minute versions.")
        for v in versions:
            print(f"Version {v.id}: Status={v.status}, Source={v.content_source}")
            print(f"  Guardrails: {len(v.guardrail_results)}")
            for gr in v.guardrail_results:
                print(f"    - {gr.guardrail_type}: {gr.result} (Score: {gr.score})")
            print(f"  Hallucinations: {len(v.hallucinations)}")

if __name__ == "__main__":
    asyncio.run(check())

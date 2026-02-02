import asyncio
from common.database.postgres_database import SessionLocal
from common.database.postgres_models import GuardrailResult, Hallucination, MinuteVersion
from sqlalchemy import select

async def check_db():
    with SessionLocal() as session:
        # Check most recent minute versions
        stmt = select(MinuteVersion).order_by(MinuteVersion.created_datetime.desc()).limit(5)
        versions = session.execute(stmt).scalars().all()
        
        print(f"Checking {len(versions)} most recent minute versions:")
        for v in versions:
            print(f"Version ID: {v.id}")
            print(f"  Content Source: {v.content_source}")
            print(f"  Status: {v.status}")
            
            # Count guardrails
            gr_stmt = select(GuardrailResult).where(GuardrailResult.minute_version_id == v.id)
            gr_count = len(session.execute(gr_stmt).all())
            print(f"  Guardrail Results: {gr_count}")
            
            # Count hallucinations
            h_stmt = select(Hallucination).where(Hallucination.minute_version_id == v.id)
            h_count = len(session.execute(h_stmt).all())
            print(f"  Hallucinations: {h_count}")

if __name__ == "__main__":
    asyncio.run(check_db())

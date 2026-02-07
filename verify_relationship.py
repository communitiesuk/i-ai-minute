import asyncio
from uuid import UUID
from common.database.postgres_database import SessionLocal
from common.database.postgres_models import MinuteVersion
from sqlalchemy.orm import selectinload
from sqlmodel import select

async def verify_relationship():
    minute_version_id = UUID("9577d595-5944-47ec-ab27-fa1eb8f50a61")
    
    with SessionLocal() as session:
        print(f"Checking MinuteVersion {minute_version_id}")
        
        # Try to load with relationship
        stmt = select(MinuteVersion).where(MinuteVersion.id == minute_version_id).options(
            selectinload(MinuteVersion.guardrail_results)
        )
        result = session.exec(stmt).first()
        
        if not result:
            print("MinuteVersion not found!")
            return

        print(f"MinuteVersion found. ID: {result.id}")
        print(f"Guardrail Results count: {len(result.guardrail_results)}")
        for gr in result.guardrail_results:
            print(f" - {gr.guardrail_type}: {gr.result}")

if __name__ == "__main__":
    asyncio.run(verify_relationship())

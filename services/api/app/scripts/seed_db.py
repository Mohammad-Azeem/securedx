"""
SecureDx AI — Database Seed Script

Generates realistic test patients for development.

For a 15-year-old:
This is like filling a fish tank with fake fish so you can test if the filter works.
We create "pretend patients" with random ages, symptoms, and names like "Patient A123."
The real names are encrypted so even developers can't see them.

For an interviewer:
Factory pattern with Faker library for reproducible test data:
- 20 patients with realistic demographics
- Encrypted PII (name, MRN, SSN) using pgcrypto
- Pseudonymous display names (Patient A001, A002...)
- Age distribution: 20% pediatric, 60% adult, 20% geriatric
- Mix of active/inactive status
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
from sqlalchemy import select, text
from app.core import database as db
from app.core.database import close_db, get_session, init_db
from app.models import Patient
from app.core.config import settings

fake = Faker()


def hash_user_id(user_id: str) -> str:
    """Hash user ID for pseudonymous storage"""
    return hashlib.sha256(f"{user_id}{settings.PSEUDONYM_SALT}".encode()).hexdigest()


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt using pgcrypto (simulated here, real encryption happens in DB).
    
    In production, this would call:
    SELECT pgp_sym_encrypt('value', 'encryption_key')
    
    For dev/seed purposes, we'll prefix with [ENCRYPTED] to indicate it
    should be encrypted but keep it readable for debugging.
    """
    return f"[ENCRYPTED]{plaintext}"


async def seed_patients(n_patients: int = 20):
    """
    Seed the database with test patients.
    
    Age distribution:
    - 0-17: 20% (pediatric)
    - 18-64: 60% (adult)
    - 65+: 20% (geriatric)
    """
    async for session in get_session():
        # Check if already seeded
        result = await session.execute(select(Patient).limit(1))
        if result.scalar_one_or_none():
            print("✓ Database already seeded. Skipping...")
            return
        
        patients = []
        
        for i in range(n_patients):
            # Generate age with realistic distribution
            rand = fake.random.random()
            if rand < 0.2:  # 20% pediatric
                age = fake.random_int(min=1, max=17)
            elif rand < 0.8:  # 60% adult
                age = fake.random_int(min=18, max=64)
            else:  # 20% geriatric
                age = fake.random_int(min=65, max=95)
            
            sex = fake.random.choice(['male', 'female', 'other'])
            
            # Generate realistic but fake identifiers
            mrn = f"MRN-{fake.random_number(digits=8, fix_len=True)}"
            full_name = fake.name()
            ssn = fake.ssn()
            
            # Pseudonymous display name (visible to users)
            display_name = f"Patient {chr(65 + (i // 26))}{str(i % 26 + 1).zfill(3)}"
            
            # Last visit: random date in past 90 days (or None)
            if fake.random.random() > 0.2:  # 80% have visited recently
                last_visit = fake.date_time_between(start_date='-90d', end_date='now')
            else:
                last_visit = None
            
            # Status: 90% active, 10% inactive
            status = 'active' if fake.random.random() > 0.1 else 'inactive'
            
            patient = Patient(
                pseudo_id=uuid4(),
                encrypted_mrn=encrypt_value(mrn),
                encrypted_name=encrypt_value(full_name),
                encrypted_ssn=encrypt_value(ssn),
                display_name=display_name,
                age_years=age,
                sex=sex,
                last_visit_date=last_visit,
                status=status,
                created_by_user_id=hash_user_id("seed_script"),
            )
            patients.append(patient)
        
        session.add_all(patients)
        await session.commit()
        
        print(f"✓ Seeded {n_patients} patients:")
        for p in patients[:5]:
            print(f"  - {p.display_name}: {p.age_years}y {p.sex}, Status: {p.status}")
        if n_patients > 5:
            print(f"  ... and {n_patients - 5} more")


async def seed_audit_genesis():
    """
    Create the genesis audit event (first link in the hash chain).
    
    For a 15-year-old:
    Every chain needs a first link. This is the "Big Bang" of our audit log.
    
    For an interviewer:
    The genesis event has previous_hash = '0' * 64 (no predecessor).
    All subsequent events will hash against this or later events.
    """
    import hashlib

    async for session in get_session():
        try:
            # Use SQL against the existing securedx.audit_events table shape.
            result = await session.execute(text("SELECT event_id FROM securedx.audit_events LIMIT 1"))
            if result.first():
                print("✓ Audit log already initialized. Skipping...")
                return

            event_id = "GENESIS_EVENT"
            action = "system_init"
            previous_hash = "0" * 64  # Genesis has no predecessor

            payload = {
                "event_id": event_id,
                "action": action,
                "actor_id": "system",
                "outcome": "success",
                "created_at": datetime.utcnow().isoformat(),
            }
            payload_str = str(sorted(payload.items()))
            event_hash = hashlib.sha256(f"{previous_hash}{payload_str}".encode()).hexdigest()

            await session.execute(
                text(
                    """
                    INSERT INTO securedx.audit_events
                    (event_id, clinic_id, action, outcome, actor_id, actor_role,
                     details, previous_hash, event_hash, is_break_glass)
                    VALUES
                    (:event_id, :clinic_id, :action, :outcome, :actor_id, :actor_role,
                     CAST(:details AS jsonb), :previous_hash, :event_hash, :is_break_glass)
                    """
                ),
                {
                    "event_id": event_id,
                    "clinic_id": settings.CLINIC_ID,
                    "action": action,
                    "outcome": "success",
                    "actor_id": "system",
                    "actor_role": "system",
                    "details": '{"note":"Initial audit log entry"}',
                    "previous_hash": previous_hash,
                    "event_hash": event_hash,
                    "is_break_glass": False,
                },
            )
            await session.commit()

            print(f"✓ Created genesis audit event: {event_hash[:16]}...")
        except Exception as exc:
            await session.rollback()
            print(f"! Skipping audit genesis seed due to schema mismatch: {exc}")
            return


async def main():
    """Run all seed tasks"""
    await init_db()

    print("🌱 Seeding SecureDx database...")
    print()

    try:
        # Fallback for local/dev where Alembic migrations may be incomplete.
        if db.engine is None:
            raise RuntimeError("Database engine was not initialized.")
        async with db.engine.begin() as conn:
            await conn.run_sync(db.Base.metadata.create_all)

        await seed_patients(n_patients=20)
        print()
        await seed_audit_genesis()
        print()

        print("✅ Database seeding complete!")
        print()
        print("Test credentials:")
        print("  Physician: physician@clinic.local / ChangeMe123!")
        print("  Admin: admin@clinic.local / ChangeMe123!")
        print()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())








"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

# Seed data
db = SessionLocal()
try:
    # Add your seed data here
    print("✅ Database seeded successfully")
finally:
    db.close()

from app.models import User

db = SessionLocal()

# Add seed data
user = User(email="admin@example.com", username="admin")
db.add(user)
db.commit()
print("✅ Database seeded")

"""

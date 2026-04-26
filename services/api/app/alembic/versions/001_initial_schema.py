"""
Initial schema migration

Creates:
- patients table (with pseudonymous IDs)
- feedback_events table (physician feedback loop)
- audit_events table (tamper-evident log)
- break_glass_sessions table (emergency access)

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgcrypto extension for encryption
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Patients table
    op.create_table(
        'patients',
        sa.Column('pseudo_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('encrypted_mrn', sa.Text(), nullable=True),
        sa.Column('encrypted_name', sa.Text(), nullable=True),
        sa.Column('encrypted_ssn', sa.Text(), nullable=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('age_years', sa.Integer(), nullable=True),
        sa.Column('sex', sa.String(20), nullable=True),
        sa.Column('last_visit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('created_by_user_id', sa.String(100), nullable=True),
    )
    op.create_index('ix_patients_status', 'patients', ['status'])
    op.create_index('ix_patients_display_name', 'patients', ['display_name'])
    
    # Feedback events table
    op.create_table(
        'feedback_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_pseudo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inference_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('physician_id_hash', sa.String(64), nullable=False),
        sa.Column('decision', sa.String(20), nullable=False),
        sa.Column('modified_diagnosis_code', sa.String(50), nullable=True),
        sa.Column('modified_diagnosis_name', sa.String(200), nullable=True),
        sa.Column('modified_confidence', sa.Float(), nullable=True),
        sa.Column('physician_notes', sa.Text(), nullable=True),
        sa.Column('original_suggestions', postgresql.JSON(), nullable=False),
        sa.Column('feature_vector', postgresql.JSON(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('queued_for_fl', sa.Boolean(), server_default='true'),
        sa.Column('fl_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pseudo_id'], ['patients.pseudo_id'], ondelete='CASCADE'),
    )
    op.create_index('ix_feedback_physician', 'feedback_events', ['physician_id_hash'])
    op.create_index('ix_feedback_decision', 'feedback_events', ['decision'])
    op.create_index('ix_feedback_queued', 'feedback_events', ['queued_for_fl'])
    
    # Audit events table (append-only)
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('previous_hash', sa.String(64), nullable=False),
        sa.Column('event_id', sa.String(100), nullable=False, unique=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('actor_id_hash', sa.String(64), nullable=False),
        sa.Column('actor_role', sa.String(50), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('outcome_reason', sa.Text(), nullable=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address_hash', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_break_glass', sa.Boolean(), server_default='false'),
        sa.Column('break_glass_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_metadata', postgresql.JSON(), nullable=True),
        #sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_audit_action', 'audit_events', ['action'])
    op.create_index('ix_audit_actor', 'audit_events', ['actor_id_hash'])
    op.create_index('ix_audit_resource', 'audit_events', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_break_glass', 'audit_events', ['is_break_glass'])
    
    # Break-glass sessions table
    op.create_table(
        'break_glass_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activated_by_user_id_hash', sa.String(64), nullable=False),
        sa.Column('activated_by_name', sa.String(200), nullable=False),
        sa.Column('activated_by_role', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(200), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('patient_pseudo_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_description', sa.String(500), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actually_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('admin_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_notified_via', sa.String(100), nullable=True),
        sa.Column('review_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_user_id_hash', sa.String(64), nullable=True),
        sa.Column('review_outcome', sa.String(20), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('actions_performed', sa.Integer(), server_default='0'),
        sa.Column('patients_accessed', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_breakglass_status', 'break_glass_sessions', ['status'])
    op.create_index('ix_breakglass_review', 'break_glass_sessions', ['reviewed_at'])


def downgrade() -> None:
    op.drop_table('break_glass_sessions')
    op.drop_table('audit_events')
    op.drop_table('feedback_events')
    op.drop_table('patients')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

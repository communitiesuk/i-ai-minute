"""add guardrail result table

Revision ID: cbb794e0ad72
Revises: 9d080ca9fe6c
Create Date: 2024-02-06 12:34:56.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cbb794e0ad72'
down_revision: Union[str, None] = '9d080ca9fe6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Define the Enum object
    # CRITICAL: We set create_type=False so create_table doesn't crash trying to recreate it
    guardrail_type = postgresql.ENUM(
        'HALLUCINATION', 'TOXICITY', 'COMPLETENESS',
        name='guardrailtype',
        create_type=False 
    )

    # 2. Create the type manually and safely (checks if it exists first)
    guardrail_type.create(op.get_bind(), checkfirst=True)

    # 3. Create the table using the Enum
    op.create_table('guardrail_result',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_datetime', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_datetime', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('minute_version_id', sa.UUID(), nullable=True),
        # Because we set create_type=False above, this line will just use the existing type
        sa.Column('guardrail_type', guardrail_type, nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.String(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['minute_version_id'], ['minute_version.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('guardrail_result')
    postgresql.ENUM(name='guardrailtype').drop(op.get_bind(), checkfirst=True)
"""add guardrail result table - SAFE VERSION"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector 

revision: str = 'cbb794e0ad72'
down_revision: Union[str, None] = '9d080ca9fe6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'guardrail_result' not in tables:
        
        guardrail_type = postgresql.ENUM(
            'HALLUCINATION', 'TOXICITY', 'COMPLETENESS',
            name='guardrailtype',
            create_type=False
        )
        guardrail_type.create(conn, checkfirst=True)

        op.create_table('guardrail_result',
            sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('created_datetime', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_datetime', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('minute_version_id', sa.UUID(), nullable=True),
            sa.Column('guardrail_type', guardrail_type, nullable=False),
            sa.Column('passed', sa.Boolean(), nullable=False),
            sa.Column('score', sa.Float(), nullable=True),
            sa.Column('reasoning', sa.String(), nullable=True),
            sa.Column('error', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['minute_version_id'], ['minute_version.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        print("Table 'guardrail_result' already exists. Skipping creation.")
        
        columns = [c['name'] for c in inspector.get_columns('guardrail_result')]
        if 'passed' not in columns:
             op.add_column('guardrail_result', sa.Column('passed', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_table('guardrail_result')
    postgresql.ENUM(name='guardrailtype').drop(op.get_bind(), checkfirst=True)
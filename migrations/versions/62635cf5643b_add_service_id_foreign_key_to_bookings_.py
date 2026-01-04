"""Add service_id foreign key to bookings table

Revision ID: 62635cf5643b
Revises: 
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '62635cf5643b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Connect to the database
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if service_id column already exists
    columns = [col['name'] for col in inspector.get_columns('bookings')]
    
    if 'service_id' not in columns:
        # Add service_id column (nullable first, we'll update it later)
        op.add_column('bookings', sa.Column('service_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint with a name
    # For SQLite, we need to recreate the table
    if conn.engine.name == 'sqlite':
        # SQLite doesn't support adding foreign keys with ALTER TABLE
        # We'll create the constraint when creating a new table
        with op.batch_alter_table('bookings', recreate='always') as batch_op:
            batch_op.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
            # Add foreign key with explicit name
            batch_op.create_foreign_key(
                'fk_bookings_service_id_services',
                'services', ['service_id'], ['id']
            )
    else:
        # For other databases (PostgreSQL, MySQL)
        op.create_foreign_key(
            'fk_bookings_service_id_services',
            'bookings', 'services',
            ['service_id'], ['id']
        )
    
    # Optionally, remove the old service_type column if you want
    # First check if it exists
    if 'service_type' in columns:
        # You might want to keep it during transition, or remove it:
        # op.drop_column('bookings', 'service_type')
        pass


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('bookings')]
    
    if conn.engine.name == 'sqlite':
        with op.batch_alter_table('bookings', recreate='always') as batch_op:
            # Remove foreign key constraint
            batch_op.drop_constraint('fk_bookings_service_id_services', type_='foreignkey')
            # Remove the column
            if 'service_id' in columns:
                batch_op.drop_column('service_id')
            # Add back service_type if it was removed
            if 'service_type' not in columns:
                batch_op.add_column(sa.Column('service_type', sa.String(255), nullable=True))
    else:
        # For other databases
        op.drop_constraint('fk_bookings_service_id_services', 'bookings', type_='foreignkey')
        if 'service_id' in columns:
            op.drop_column('bookings', 'service_id')
        # Add back service_type if it was removed
        if 'service_type' not in columns:
            op.add_column('bookings', sa.Column('service_type', sa.String(255), nullable=True))
"""initial_schema_reliefos_tables

Revision ID: 2c746e0b3655
Revises: 
Create Date: 2026-10-09 20:37:15.233945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c746e0b3655'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core RELIEFOS Lite tables."""
    # 1. zones
    op.create_table(
        'zones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('affected_population', sa.Integer(), nullable=True, default=0),
        sa.Column('inundation_area_ha', sa.Float(), nullable=True, default=0.0),
        sa.Column('water_depth_m', sa.Float(), nullable=True, default=0.0),
        sa.Column('status', sa.String(length=50), nullable=True, default='MONITORING'),
        sa.Column('road_status', sa.String(length=50), nullable=True, default='OPEN'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_zones_id'), 'zones', ['id'], unique=False)
    op.create_index(op.f('ix_zones_code'), 'zones', ['code'], unique=True)

    # 2. depots
    op.create_table(
        'depots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('capacity_kg', sa.Float(), nullable=True, default=20000.0),
        sa.Column('available_stock_kg', sa.Float(), nullable=True, default=5500.0),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_depots_id'), 'depots', ['id'], unique=False)
    op.create_index(op.f('ix_depots_code'), 'depots', ['code'], unique=True)

    # 3. vehicles
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('plate', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('capacity_kg', sa.Float(), nullable=True, default=2500.0),
        sa.Column('status', sa.String(length=50), nullable=True, default='READY'),
        sa.Column('fuel_pct', sa.Integer(), nullable=True, default=100),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_code'), 'vehicles', ['code'], unique=True)

    # 4. inventory_items
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('total_quantity', sa.Float(), nullable=True, default=0.0),
        sa.Column('available_quantity', sa.Float(), nullable=True, default=0.0),
        sa.Column('reserved_quantity', sa.Float(), nullable=True, default=0.0),
        sa.Column('unit', sa.String(length=50), nullable=True, default='kg'),
        sa.Column('status', sa.String(length=50), nullable=True, default='In Stock'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_verified_by', sa.String(length=100), nullable=True, default='ASDMA Central Logistics Desk'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_items_sku'), 'inventory_items', ['sku'], unique=True)

    # 5. demands
    op.create_table(
        'demands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('req_id', sa.String(length=50), nullable=False),
        sa.Column('zone_code', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('requested_qty', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True, default='kg'),
        sa.Column('priority', sa.String(length=50), nullable=True, default='HIGH'),
        sa.Column('status', sa.String(length=50), nullable=True, default='PENDING'),
        sa.Column('lifecycle_status', sa.String(length=50), nullable=True, default='REQUESTED'),
        sa.Column('verification_status', sa.String(length=50), nullable=True, default='UNVERIFIED'),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('request_source', sa.String(length=100), nullable=True, default='Field Shelter Coordinator'),
        sa.Column('notes', sa.String(length=255), nullable=True, default=''),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demands_id'), 'demands', ['id'], unique=False)
    op.create_index(op.f('ix_demands_req_id'), 'demands', ['req_id'], unique=True)

    # 6. shelters
    op.create_table(
        'shelters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('zone_code', sa.String(length=50), nullable=False),
        sa.Column('location_desc', sa.String(length=255), nullable=True, default=''),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True, default=500),
        sa.Column('occupancy', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(length=50), nullable=True, default='ACTIVE'),
        sa.Column('verification_status', sa.String(length=50), nullable=True, default='VERIFIED'),
        sa.Column('verification_source', sa.String(length=255), nullable=True, default='DDMA Kamrup Metro Evacuation Registry 2024'),
        sa.Column('verified_date', sa.String(length=50), nullable=True, default='2024-06-15'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shelters_id'), 'shelters', ['id'], unique=False)
    op.create_index(op.f('ix_shelters_code'), 'shelters', ['code'], unique=True)

    # 7. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('operator_name', sa.String(length=100), nullable=True, default='Insp. S. Sharma (EOC Planner)'),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True, default=''),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)

    # 8. road_closures
    op.create_table(
        'road_closures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('corridor_name', sa.String(length=255), nullable=False),
        sa.Column('location_desc', sa.String(length=255), nullable=True, default=''),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('water_depth_m', sa.Float(), nullable=True, default=0.0),
        sa.Column('clearance_threshold_m', sa.Float(), nullable=True, default=0.35),
        sa.Column('status', sa.String(length=50), nullable=True, default='IMPASSABLE_FLOOD'),
        sa.Column('detour_corridor', sa.String(length=255), nullable=True, default=''),
        sa.Column('reported_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by', sa.String(length=100), nullable=True, default='PWD Roads / Traffic Police Guwahati'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_road_closures_id'), 'road_closures', ['id'], unique=False)

    # 9. dispatch_orders
    op.create_table(
        'dispatch_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispatch_id', sa.String(length=50), nullable=False),
        sa.Column('plan_id', sa.String(length=50), nullable=False),
        sa.Column('zone_code', sa.String(length=50), nullable=False),
        sa.Column('zone_name', sa.String(length=255), nullable=False),
        sa.Column('vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('vehicle_name', sa.String(length=255), nullable=True, default=''),
        sa.Column('resource_type', sa.String(length=100), nullable=True, default='Food Rations & Potable Water'),
        sa.Column('food_quantity_kg', sa.Float(), nullable=True, default=0.0),
        sa.Column('water_quantity_l', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_weight_kg', sa.Float(), nullable=True, default=0.0),
        sa.Column('destination_desc', sa.String(length=255), nullable=True, default=''),
        sa.Column('route_summary', sa.String(length=255), nullable=True, default=''),
        sa.Column('transit_distance_km', sa.Float(), nullable=True, default=0.0),
        sa.Column('detour_required', sa.Boolean(), nullable=True, default=False),
        sa.Column('detour_reason', sa.String(length=255), nullable=True, default=''),
        sa.Column('status', sa.String(length=50), nullable=True, default='PENDING'),
        sa.Column('is_dry_run', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_simulation', sa.Boolean(), nullable=True, default=False),
        sa.Column('safety_validation_passed', sa.Boolean(), nullable=True, default=True),
        sa.Column('safety_warnings', sa.Text(), nullable=True, default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_decision', sa.String(length=50), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('form_8b_reference', sa.String(length=100), nullable=True, default='ASDMA-F8B-2026-LOG-DISPATCH'),
        sa.Column('external_connector_attempted', sa.Boolean(), nullable=True, default=False),
        sa.Column('external_connector_status', sa.String(length=50), nullable=True, default='DISABLED_BY_POLICY'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dispatch_orders_id'), 'dispatch_orders', ['id'], unique=False)
    op.create_index(op.f('ix_dispatch_orders_dispatch_id'), 'dispatch_orders', ['dispatch_id'], unique=True)
    op.create_index(op.f('ix_dispatch_orders_plan_id'), 'dispatch_orders', ['plan_id'], unique=False)
    op.create_index(op.f('ix_dispatch_orders_status'), 'dispatch_orders', ['status'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table('dispatch_orders')
    op.drop_table('road_closures')
    op.drop_table('audit_logs')
    op.drop_table('shelters')
    op.drop_table('demands')
    op.drop_table('inventory_items')
    op.drop_table('vehicles')
    op.drop_table('depots')
    op.drop_table('zones')

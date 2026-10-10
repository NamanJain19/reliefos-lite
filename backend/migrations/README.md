# RELIEFOS Lite Database Migrations

This folder houses Alembic database schema migrations for PostgreSQL (production) and SQLite (development).

## Production Deployment (PostgreSQL)
When deploying against a fresh or existing PostgreSQL database:
```bash
# Apply all pending migrations to bring the database schema to the latest version
alembic upgrade head
```

## Creating New Migrations
To generate a new migration revision based on changes in `app/models/domain.py`:
```bash
alembic revision --autogenerate -m "description_of_changes"
alembic upgrade head
```

## Existing Databases
If pointing to an existing database whose tables already exist:
```bash
# Stamp the database without altering existing tables
alembic stamp head
```

## Checking Current Revision
```bash
alembic current
alembic heads
```


# RELIEFOS Lite — Production Operational Deployment & Runbook Guide

**System Name:** RELIEFOS Lite (Disaster Relief Planning & Resource Optimization System)  
**Target Environment:** Assam State Disaster Management Authority (ASDMA) / District Emergency Operations Centers (DEOC)  
**Classification:** Operational Decision-Support & Humanitarian Logistics Management  
**Version:** 2.0-Production  

---

## 1. System Architecture & Component Overview

```
                      +---------------------------------------+
                      |   Client Web Browsers / Field Tablets |
                      +---------------------------------------+
                                          |
                                          v (HTTP/HTTPS :80/:443)
                      +---------------------------------------+
                      |    Nginx Reverse Proxy & Static SPA   |
                      |   (Docker: reliefos-frontend :80)     |
                      +---------------------------------------+
                               /                     \
                   Static Assets                 API Proxy (/api/*)
                 (React + Leaflet GIS)                |
                                                      v
                                      +-----------------------------------+
                                      |     FastAPI Operational Engine     |
                                      |    (Docker: reliefos-backend :8013)|
                                      +-----------------------------------+
                                        /         |             \
                   +-------------------+   +-------------+   +-------------------+
                   | External Telemetry|   | OR-Tools &  |   | Persistent Ledger |
                   | - Open-Meteo      |   | ML Services |   | - SQLite / PG16   |
                   | - CWC Gauges      |   | - CP-SAT    |   | - Stock Movements |
                   | - OSRM Routing    |   | - RF Risk   |   | - Field Incidents |
                   | - ASDMA Circles   |   | - Sphere    |   | - SitReps         |
                   +-------------------+   +-------------+   +-------------------+
```

### Core Architecture Principles
1. **Statutory Integrity & Human-in-the-Loop:** All physical dispatch orders, inventory deductions, and ASDMA Situation Reports require explicit officer digital signatures under Form 8B protocol. No AI model or optimizer is permitted to dispatch relief supplies autonomously.
2. **Deterministic Data Contracts:** External hydrometeorological feeds (Open-Meteo, CWC, OSRM) are isolated behind resilient adapters with strict bounded timeouts (4–6s) and deterministic fallback telemetry.
3. **Multi-Location Boundary Isolation:** Complete geographic and transactional partitioning across monitored Assam districts (`kamrup_metro`, `barpeta`, `nalbari`, `cachar`).

---

## 2. Infrastructure Requirements

### Minimum Hardware Sizing (DEOC Operations)
- **CPU:** 4 vCPU (x86_64 or ARM64)
- **Memory:** 8 GB RAM
- **Storage:** 50 GB NVMe / SSD (minimum 20 GB free for logs and point-in-time snapshots)
- **Network:** 10 Mbps low-latency broadband or VSAT backup for hydro-met telemetry syncing

### Software Prerequisites
- **Operating System:** Ubuntu 22.04 LTS / Debian 12 / RHEL 9 (or Windows Server 2022)
- **Container Engine:** Docker Engine 24.0+ and Docker Compose v2.20+
- **Alternative Bare-Metal:** Python 3.12+, Node.js 20.x, Nginx 1.24+

---

## 3. Containerized Deployment (Recommended)

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/reliefos/reliefos-lite.git /opt/reliefos
cd /opt/reliefos

# Create and lock down the production environment file
cp backend/.env.example backend/.env
chmod 600 backend/.env
```

### Step 2: Configure Environment Variables (`backend/.env`)
Edit `backend/.env` with production keys:
```ini
APP_ENV=production
PORT=8013
HOST=0.0.0.0

# Security Credentials (CRITICAL: Change before operational launch)
JWT_SECRET_KEY=generate_high_entropy_64_char_secret_key_here
ACCESS_TOKEN_EXPIRE_HOURS=12
CORS_ORIGINS=https://reliefos.asdma.gov.in,http://localhost

# Database Connection
DATABASE_URL=sqlite:////app/data/reliefos_lite.db

# Hydro-Met & Routing Network Boundaries
OPEN_METEO_TIMEOUT_SECONDS=6.0
CWC_TIMEOUT_SECONDS=5.0
OSRM_TIMEOUT_SECONDS=4.0

# AI Provider Integration
AI_COPILOT_PROVIDER=gemini
GEMINI_API_KEY=your_official_gemini_api_key_here
```

### Step 3: Launch Containers via Docker Compose
```bash
# Standard Production Deployment (SQLite Persistent Volume)
docker compose up -d --build

# Verify container health status
docker compose ps
```

*Expected output:*
```
NAME                IMAGE               COMMAND                  SERVICE             STATUS                    PORTS
reliefos-backend    reliefos-backend    "uvicorn app.main:ap…"   backend             Up (healthy)              0.0.0.0:8013->8013/tcp
reliefos-frontend   reliefos-frontend   "nginx -g 'daemon of…"   frontend            Up (healthy)              0.0.0.0:80->80/tcp
```

### Step 4: Optional PostgreSQL Enterprise Profile
To launch with a dedicated PostgreSQL 16 database instead of SQLite:
```bash
docker compose --profile with-postgres up -d --build
```

---

## 4. Role-Based Access Control (RBAC) & Default Credentials

The system operates with 3 strict statutory roles:

| Username | Default Password | Role | Operational Authorization |
| :--- | :--- | :--- | :--- |
| `commander` | `asdma@2026` | `COMMANDER` | Final Form 8B plan approval, vehicle dispatch execution, ASDMA Daily SitRep sign-off |
| `operator` | `relief@2026` | `OPERATOR` | Field incident logging, physical stock cycle-count adjustments, consignments receipt |
| `analyst` | `view@2026` | `ANALYST` | Read-only inspection of hydro-met telemetry, flood risk simulations, and audit trails |

> **IMPORTANT:** Immediately change default passwords upon initial deployment using the `PUT /api/auth/profile` endpoint or User Profile Settings modal.

---

## 5. Database Durability, Backup & Recovery Runbook

### Automatic Online Backups
RELIEFOS Lite utilizes SQLite's Online Backup API, guaranteeing zero lockup and 100% ACID consistency even during concurrent dispatches.

Run manual snapshot:
```bash
python backend/scripts/backup_db.py
```
*Output: Compressed snapshot in `backend/backups/reliefos_snapshot_YYYYMMDD_HHMMSS.db.gz` with companion `.sha256` checksum.*

### Automated Daily Cron Job (Linux)
Add to `/etc/cron.d/reliefos-backup`:
```cron
# Daily atomic snapshot at 02:00 IST
0 2 * * * root cd /opt/reliefos && /usr/bin/docker compose exec -T backend python /app/scripts/backup_db.py >> /var/log/reliefos_backup.log 2>&1
```

### Disaster Recovery / Restore Procedure
To restore the operational ledger from an authenticated backup:
```bash
# Verify checksum, PRAGMA health, and atomically swap
python backend/scripts/restore_db.py backend/backups/reliefos_snapshot_20261013_164924.db.gz
```

---

## 6. Health Monitoring & Endpoints

| Endpoint | Method | Purpose | Normal Response |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Core backend container health check | `{"status": "ok", "mode": "OPERATIONAL_LIVE"}` |
| `/api/health/integrations` | `GET` | External telemetry adapter availability status | Detailed latency and status for Open-Meteo, CWC, OSRM, AI Copilot |
| `/api/operational/inventory/alerts` | `GET` | Inventory threshold monitoring | Active SKU deficits and near-expiry consignment alerts |
| `/api/operational/incidents` | `GET` | Active ground incident status | List of open breaches, road blockages, and overflow events |
| `/api/operational/sitreps` | `GET` | ASDMA Daily Flood Bulletins | Historical and daily compiled situation reports |

---

## 7. Emergency Failover & Offline Mode

If the DEOC loses internet connectivity during extreme monsoon events:
1. **Weather & River Gauges:** The system gracefully retains last-known verified readings, clearly marking them with timestamps and `STALE` freshness warnings.
2. **OSRM Routing:** The routing adapter automatically falls back to deterministic road network graph distances without blocking dispatch calculations.
3. **AI Copilot:** The Logistics Advisor switches to rule-based deterministic heuristics and displays transparent uncertainty disclosures.
4. **Local Database:** All incident logging, stock adjustments, and officer dispatch approvals continue functioning locally without network dependencies.

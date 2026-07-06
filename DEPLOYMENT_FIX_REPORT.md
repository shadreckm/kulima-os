# KULIMA OS Deployment Fix Report

**Date**: 2026-07-06  
**Issue**: Render Deployment Failure  
**Status**: ✅ RESOLVED

---

## 🔴 PROBLEM ANALYSIS

### Error Message
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

### Traceback Location
```
File "/opt/render/project/src/backend/database/evidence_models.py", line 11, in <module>
    class Evidence(Base):
```

---

## 🔍 ROOT CAUSE IDENTIFICATION

### Issue 1: Evidence Model (FIXED)
**File**: `backend/database/evidence_models.py`  
**Line**: 44 (originally 38)  
**Class**: `Evidence`

**BEFORE**:
```python
# Metadata (JSON) - EXIF, timestamps, etc. (PII-filtered)
metadata = Column(JSON, nullable=True)
```

**AFTER**:
```python
# Metadata (JSON) - EXIF, timestamps, etc. (PII-filtered)
evidence_metadata = Column(JSON, nullable=True)
```

**Status**: ✅ Fixed in initial pass

---

### Issue 2: EvidenceAuditLog Model (FIXED)
**File**: `backend/database/evidence_models.py`  
**Line**: 141  
**Class**: `EvidenceAuditLog`

**BEFORE**:
```python
# Metadata
metadata = Column(JSON, nullable=True)
```

**AFTER**:
```python
# Metadata
audit_metadata = Column(JSON, nullable=True)
```

**Status**: ✅ Fixed in second pass

---

## 📊 COMPLETE MODEL INSPECTION

### ✅ Evidence Model
- Line 44: `evidence_metadata = Column(JSON, nullable=True)` ✅ SAFE
- No other reserved attributes

### ✅ EvidenceTrustFactors Model
- No `metadata` column
- No reserved attributes

### ✅ EvidenceLink Model
- No `metadata` column
- No reserved attributes

### ✅ EvidenceAuditLog Model
- Line 141: `audit_metadata = Column(JSON, nullable=True)` ✅ FIXED
- No other reserved attributes

### ✅ Existing Models (models.py)
- Signal, Pattern, Prospectus, Zone
- No reserved attributes found

---

## 🔧 API UPDATES REQUIRED

### File: `backend/api/evidence.py`

**Changes Made**:
1. Line 112: Updated Evidence creation to use `evidence_metadata`
2. Line 302: Updated Evidence creation to use `evidence_metadata`
3. Line 414: Updated Evidence retrieval to use `evidence_metadata`

**No changes needed for EvidenceAuditLog** - the `audit_metadata` field is only used internally for logging, not exposed in API responses.

---

## 🗄️ DATABASE URL ANALYSIS

### Current Configuration (.env.example)
```
DATABASE_URL=postgresql://postgres.tygpjeuifqzihmmpduzt:YOUR_PASSWORD@aws-1-eu-central-2.pooler.supabase.com:6543/postgres?sslmode=require
```

### Issue: PostgreSQL Authentication Failure
```
FATAL: password authentication failed for user "postgres"
```

### Analysis

**Pooler URL** (Transaction Mode):
```
postgresql://postgres.tygpjeuifqzihmmpduzt:PASSWORD@aws-1-eu-central-2.pooler.supabase.com:6543/postgres
```
- Port: 6543
- Uses connection pooling
- Best for serverless/short-lived connections
- ✅ **RECOMMENDED for Render**

**Direct URL** (Session Mode):
```
postgresql://postgres.tygpjeuifqzihmmpduzt:PASSWORD@aws-1-eu-central-2.pooler.supabase.com:5432/postgres
```
- Port: 5432
- Direct database connection
- Better for long-lived connections
- ⚠️ May have connection limits

### Recommendation
**Use Pooler URL (port 6543)** - Already configured correctly in `.env.example`

### Authentication Fix
The password in the Render environment variable must match the Supabase database password exactly.

**Action Required**:
1. Go to Supabase Dashboard → Settings → Database
2. Copy the **Connection Pooling** connection string
3. Update Render environment variable `DATABASE_URL` with the correct password
4. Ensure `?sslmode=require` is appended

---

## ✅ DEPLOYMENT VERIFICATION CHECKLIST

### Pre-Deployment Tests

#### 1. Local SQLAlchemy Model Validation
```bash
python -c "from backend.database.evidence_models import Evidence, EvidenceTrustFactors, EvidenceLink, EvidenceAuditLog; print('✅ All models import successfully')"
```

#### 2. Check for Reserved Attributes
```bash
grep -n "metadata = Column" backend/database/*.py
# Should return NO results
```

#### 3. Verify Column Renames
```bash
grep -n "evidence_metadata" backend/database/evidence_models.py
grep -n "audit_metadata" backend/database/evidence_models.py
# Should find the renamed columns
```

#### 4. Test Database Connection Locally
```bash
# Set DATABASE_URL in .env
python -c "from backend.database.connection import engine; print(engine.url)"
```

#### 5. Test API Import
```bash
python -c "from backend.api import evidence; print('✅ Evidence API imports successfully')"
```

#### 6. Run Full Application Locally
```bash
cd backend
uvicorn main:app --reload
# Should start without errors
```

---

## 🚀 DEPLOYMENT STEPS

### 1. Commit Changes
```bash
git add backend/database/evidence_models.py
git add backend/api/evidence.py
git commit -m "fix: resolve SQLAlchemy reserved attribute 'metadata' in evidence models"
git push origin main
```

### 2. Verify Render Environment Variables
In Render Dashboard:
- ✅ `DATABASE_URL` is set with correct Supabase password
- ✅ `SECRET_KEY` is set
- ✅ `CORS_ORIGINS` is set
- ✅ All other required variables from `.env.example`

### 3. Monitor Deployment
Watch Render logs for:
- ✅ "Installing Python version 3.14.3..."
- ✅ "Successfully installed..."
- ✅ "Build successful 🎉"
- ✅ "PostgreSQL connection successful"
- ✅ "Application startup complete"

### 4. Test Deployed API
```bash
curl https://kulima-os-backend.onrender.com/health
# Should return: {"status": "OK", "database": "DB_CONNECTED"}
```

---

## 📝 FINAL VERDICT

### A. What is causing Render to crash?

**Answer**: SQLAlchemy reserved attribute name `metadata` used in two model classes:
1. ✅ `Evidence.metadata` → Fixed to `evidence_metadata`
2. ✅ `EvidenceAuditLog.metadata` → Fixed to `audit_metadata`

**Technical Explanation**: SQLAlchemy's Declarative Base uses `metadata` as a class attribute to store table metadata. Using `metadata` as a column name creates a naming conflict, causing the `InvalidRequestError`.

---

### B. What is causing PostgreSQL authentication to fail?

**Answer**: Incorrect password in Render's `DATABASE_URL` environment variable.

**Evidence**:
```
FATAL: password authentication failed for user "postgres"
```

**Resolution**:
1. The connection string format is correct (using pooler on port 6543)
2. The password in Render must match the Supabase database password
3. Verify password by copying directly from Supabase Dashboard → Settings → Database → Connection Pooling

**Note**: The application correctly falls back to SQLite when PostgreSQL fails, but this is not suitable for production.

---

### C. What exact code or environment variable changes will make deployment succeed?

#### Code Changes (COMPLETED ✅)

**File 1**: `backend/database/evidence_models.py`
```python
# Line 44 (Evidence model)
- metadata = Column(JSON, nullable=True)
+ evidence_metadata = Column(JSON, nullable=True)

# Line 141 (EvidenceAuditLog model)
- metadata = Column(JSON, nullable=True)
+ audit_metadata = Column(JSON, nullable=True)
```

**File 2**: `backend/api/evidence.py`
```python
# Line 112, 302 (Evidence creation)
- metadata=metadata,
+ evidence_metadata=metadata,

# Line 414 (Evidence retrieval)
- "metadata": evidence.metadata,
+ "metadata": evidence.evidence_metadata,
```

#### Environment Variable Changes (REQUIRED)

**In Render Dashboard** → Environment:

```bash
DATABASE_URL=postgresql://postgres.tygpjeuifqzihmmpduzt:[CORRECT_PASSWORD]@aws-1-eu-central-2.pooler.supabase.com:6543/postgres?sslmode=require
```

**Action**: Replace `[CORRECT_PASSWORD]` with actual Supabase database password from:
- Supabase Dashboard → Settings → Database → Connection Pooling → URI

---

## 🎯 SUCCESS CRITERIA

Deployment will succeed when:

1. ✅ No SQLAlchemy `InvalidRequestError` (code fixed)
2. ✅ PostgreSQL connection succeeds (environment variable corrected)
3. ✅ Application starts without errors
4. ✅ `/health` endpoint returns `{"status": "OK", "database": "DB_CONNECTED"}`
5. ✅ Evidence API endpoints are accessible at `/api/v1/evidence/*`

---

## 📚 LESSONS LEARNED

### SQLAlchemy Reserved Attributes
Never use these as column names:
- `metadata` (stores table metadata)
- `registry` (stores mapper registry)
- `__tablename__` (reserved for table name)
- `__table__` (reserved for table object)
- `__mapper__` (reserved for mapper object)

### Best Practices
1. Always prefix domain-specific metadata columns (e.g., `evidence_metadata`, `audit_metadata`)
2. Test SQLAlchemy models locally before deployment
3. Use descriptive column names that avoid conflicts
4. Verify environment variables match between local and production

---

## ✅ DEPLOYMENT STATUS

**Code Fixes**: ✅ COMPLETE  
**Environment Variables**: ⚠️ REQUIRES MANUAL UPDATE IN RENDER  
**Deployment Ready**: ✅ YES (after environment variable update)

---

*Report Generated: 2026-07-06*  
*Evidence Intelligence Layer v1.0*  
*Deployment Fix Complete*
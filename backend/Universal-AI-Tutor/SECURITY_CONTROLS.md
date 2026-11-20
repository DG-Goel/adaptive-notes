# Security Controls - Universal AI Tutor API

**Implemented**: November 11, 2026  
**Status**: Local Development Security - Phase 1

---

## Overview

This document describes the security controls implemented for the Universal AI Tutor API. These controls are designed for **local development** and include baseline protections against common security issues.

**⚠️ WARNING: This system is NOT production-ready without additional security hardening.**

---

## Implemented Security Controls

### 1. Localhost Binding by Default

**Control**: API binds to `127.0.0.1` (localhost) by default, not `0.0.0.0` (all interfaces).

**Configuration**:
```bash
# .env
API_HOST=127.0.0.1  # Default (localhost only)
# API_HOST=0.0.0.0  # All interfaces (DO NOT use without firewall)
```

**Rationale**: Prevents accidental exposure to network or internet during local development.

**Files Modified**:
- `src/api/main.py`: Changed default from `0.0.0.0` to `127.0.0.1`
- `src/config.py`: Updated `api_host` default value

### 2. File Path Validation and Whitelisting

**Control**: All ingested files must be within a configured allowed directory.

**Configuration**:
```bash
# .env
ALLOWED_NOTES_DIR=./notes  # Default
# ALLOWED_NOTES_DIR=/home/user/my_notes  # Custom path
```

**Protections**:
- ✅ **Path traversal prevention**: `../` attempts blocked
- ✅ **Symlink escape prevention**: Canonical path checking
- ✅ **Directory restriction**: Files outside allowed directory rejected
- ✅ **Existence verification**: Nonexistent files rejected
- ✅ **Type verification**: Only regular files (not directories)

**Implementation**: `src/api/security.py::validate_file_path()`

**Example Blocked Attempts**:
```python
"/etc/passwd"                          # Outside allowed directory
"../../secrets.txt"                    # Path traversal
"/notes/../../../etc/shadow"           # Traversal with allowed prefix
"/tmp/symlink_to_secrets"              # Symlink escape
```

### 3. File Type Restrictions

**Control**: Only specific file types allowed for ingestion.

**Allowed Extensions**:
```python
{
    '.txt', '.md', '.markdown',        # Text documents
    '.py', '.js', '.java', '.cpp',     # Code files
    '.json', '.yaml', '.yml', '.xml',  # Data formats
    '.rst', '.tex', '.html', '.css',   # Other documentation
}
```

**Blocked Extensions** (examples):
- `.exe`, `.dll`, `.so` - Executables
- `.sh`, `.bat`, `.ps1` - Scripts  
- `.zip`, `.tar`, `.gz` - Archives
- `.pdf`, `.docx` - Binary documents (not yet supported)

**Implementation**: `src/api/security.py::validate_file_path()`

### 4. File Size Limits

**Control**: Maximum file size enforced (default: 50MB).

**Configuration**:
```bash
# .env
MAX_FILE_SIZE_MB=50  # Default
```

**Rationale**: Prevents:
- Resource exhaustion attacks
- Accidental processing of large binary files
- Memory overflow from oversized files

**Implementation**: `src/api/security.py::validate_file_path()`

### 5. Input Validation

**Control**: Questions and inputs validated before processing.

**Question Validation**:
- ✅ Minimum length: 3 characters
- ✅ Maximum length: 2000 characters (configurable)
- ✅ SQL injection patterns detected
- ✅ Command injection patterns detected
- ✅ XSS patterns detected
- ✅ Normal punctuation allowed

**Detected Malicious Patterns**:
```python
# SQL Injection
"'; DROP TABLE users; --"

# Command Injection
"$(rm -rf /)"
"`malicious command`"
"${env:SECRETS}"

# Cross-Site Scripting (XSS)
"<script>alert('xss')</script>"
"javascript:alert(1)"
"onerror='malicious()'"
```

**Implementation**: `src/api/security.py::validate_question()`

### 6. Credential Redaction in Logs

**Control**: Sensitive data automatically redacted in logs.

**Redacted Patterns**:
- API keys (long alphanumeric strings)
- Passwords (password= fields)
- Tokens (token= fields)
- Secrets (secret= fields)
- Groq API keys
- Qdrant API keys

**Example**:
```python
# Original
"Using groq_api_key=sk_abc123xyz456def789"

# Redacted
"Using groq_api_key=[REDACTED]"
```

**Implementation**: `src/api/security.py::redact_sensitive_data()`

### 7. Security Warnings on Startup

**Control**: API prints security warnings on startup for misconfigurations.

**Checks**:
- ✅ API bound to all interfaces (0.0.0.0)
- ✅ Debug mode enabled in production
- ✅ Missing API keys
- ✅ Default notes directory in use
- ✅ CORS configured to allow all origins

**Example Output**:
```
======================================================================
SECURITY WARNINGS
======================================================================

⚠️  API is bound to 0.0.0.0 (all interfaces). 
For local development, use 127.0.0.1 instead. 
Set API_HOST=127.0.0.1 in .env

ℹ️  Using default notes directory: C:\Projects\notes. 
To restrict access, set ALLOWED_NOTES_DIR in .env

======================================================================
⚠️  DO NOT DEPLOY TO PRODUCTION WITHOUT ADDRESSING THESE ISSUES
======================================================================
```

**Implementation**: `src/api/security.py::print_security_warnings()`

### 8. Batch Upload Limits

**Control**: Maximum number of files per request (100 files).

**Rationale**: Prevents:
- Resource exhaustion from bulk uploads
- Denial of service attacks
- Accidental mass processing

**Implementation**: `src/api/security.py::validate_file_paths()`

---

## Security Test Suite

**Location**: `tests/unit/test_security.py`  
**Tests**: 31 tests (31 passed, 1 skipped)

### Test Coverage

#### Path Validation (9 tests)
- ✅ Valid file paths accepted
- ✅ Path traversal attempts blocked (`../`)
- ✅ Absolute paths outside directory blocked
- ✅ Nonexistent files rejected
- ✅ Directory paths rejected
- ✅ Invalid extensions blocked
- ✅ Allowed extensions accepted
- ✅ Empty paths rejected
- ⊘ Symlink escapes blocked (skipped on Windows)

#### Batch Validation (4 tests)
- ✅ All valid paths processed
- ✅ Mixed valid/invalid paths handled
- ✅ Empty list rejected
- ✅ Too many files rejected

#### Question Validation (9 tests)
- ✅ Valid questions accepted
- ✅ Empty questions rejected
- ✅ Whitespace-only rejected
- ✅ Too short questions rejected
- ✅ Too long questions rejected
- ✅ SQL injection detected
- ✅ Command injection detected
- ✅ XSS patterns detected
- ✅ Normal punctuation allowed

#### Credential Redaction (6 tests)
- ✅ API keys redacted
- ✅ Long alphanumeric strings redacted
- ✅ Password fields redacted
- ✅ Token fields redacted
- ✅ Normal text preserved
- ✅ Empty/None handled

#### Configuration (3 tests)
- ✅ Default directory created
- ✅ Custom directory from environment
- ✅ Missing directory auto-created

---

## Known Limitations

### Critical (Block Production Deployment)

1. **No Authentication/Authorization**
   - No API keys
   - No user management
   - No role-based access control
   - **Action Required**: Implement before production

2. **No Rate Limiting**
   - Vulnerable to abuse and DoS
   - No request throttling
   - **Action Required**: Add rate limiting middleware

3. **No HTTPS/TLS**
   - Traffic not encrypted
   - Credentials sent in plaintext
   - **Action Required**: Configure TLS certificates

4. **No Request Logging/Audit Trail**
   - Cannot track who accessed what
   - No security event monitoring
   - **Action Required**: Implement audit logging

5. **Basic Input Validation Only**
   - Pattern matching may miss sophisticated attacks
   - No ML-based anomaly detection
   - **Action Required**: Enhanced validation

### High Priority

6. **CORS Allows All Origins**
   - Current: `allow_origins=["*"]`
   - **Action Required**: Restrict to specific domains

7. **No Session Management**
   - No session tokens
   - No timeout handling
   - **Action Required**: Implement proper sessions

8. **No API Key Rotation**
   - Keys don't expire
   - No rotation mechanism
   - **Action Required**: Key lifecycle management

9. **No Secrets Vault Integration**
   - Environment variables only
   - Keys visible in process listing
   - **Action Required**: Use HashiCorp Vault or AWS Secrets Manager

10. **No Request Size Limits**
    - Large requests can exhaust memory
    - **Action Required**: Add middleware for request size limiting

### Medium Priority

11. **No IP Whitelisting**
12. **No Web Application Firewall (WAF)**
13. **No Intrusion Detection System (IDS)**
14. **No Security Headers** (CSP, X-Frame-Options, etc.)
15. **No Content Security Policy**

---

## Recommended Production Security Additions

### Authentication & Authorization
```python
# Example: API Key Authentication
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/api/v1/ask")
async def ask_question(
    request: AskRequest,
    api_key: str = Depends(api_key_header)
):
    # Validate API key
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ...
```

### Rate Limiting
```python
# Example: Using SlowAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/ask")
@limiter.limit("10/minute")
async def ask_question(request: AskRequest):
    # ...
```

### HTTPS Configuration
```bash
# Example: Uvicorn with TLS
uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

### Security Headers
```python
# Example: Security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])
app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## Environment Configuration

### Secure Development Configuration (.env)

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API Security
API_HOST=127.0.0.1        # Localhost only
API_PORT=8000
ALLOWED_NOTES_DIR=./notes # Restrict to specific directory

# File Security
MAX_FILE_SIZE_MB=50
MAX_QUESTION_LENGTH=2000

# Database (if using managed Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=           # Leave empty for local dev

# LLM (Groq)
GROQ_API_KEY=your-key-here # Required for real LLM
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TIMEOUT_SECONDS=30
```

### Production Configuration Differences

```bash
# Application
APP_ENV=production
DEBUG=false              # CRITICAL: Disable debug mode
LOG_LEVEL=WARNING

# API Security
API_HOST=0.0.0.0        # With firewall/load balancer
API_PORT=443            # HTTPS
ALLOWED_NOTES_DIR=/var/lib/tutor/notes

# Add:
API_KEY_HEADER=X-API-Key
RATE_LIMIT_PER_MINUTE=60
SESSION_TIMEOUT_SECONDS=3600
```

---

## Security Checklist for Production

### Before Deployment
- [ ] Authentication implemented (API keys or OAuth)
- [ ] Rate limiting configured
- [ ] HTTPS/TLS certificates installed
- [ ] CORS restricted to specific domains
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Logging configured (centralized, structured)
- [ ] Secrets in vault (not .env files)
- [ ] Allowed notes directory restricted
- [ ] File size/type limits appropriate
- [ ] Security headers added
- [ ] Error messages don't leak information
- [ ] API documentation access restricted

### After Deployment
- [ ] Penetration testing performed
- [ ] Security audit completed
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented
- [ ] Regular security updates scheduled
- [ ] Backup and recovery tested

---

## Threat Model

### In Scope (Protected)
- ✅ Path traversal attacks
- ✅ Malicious file uploads (via type/size restrictions)
- ✅ SQL/Command/XSS injection in queries
- ✅ Credential exposure in logs
- ✅ Accidental network exposure (localhost default)

### Out of Scope (NOT Protected)
- ❌ DDoS attacks (no rate limiting)
- ❌ Unauthorized access (no authentication)
- ❌ Man-in-the-middle (no TLS)
- ❌ Session hijacking (no sessions)
- ❌ Privilege escalation (no authorization)
- ❌ Advanced persistent threats
- ❌ Zero-day exploits in dependencies

---

## Security Contacts

For security issues or questions:
1. Review this document
2. Check test suite: `tests/unit/test_security.py`
3. Review implementation: `src/api/security.py`
4. Consult PHASE1_ACCEPTANCE_REPORT.md

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-11-11 | Initial security controls for Phase 1 MVP |

---

**Status**: ✅ Local Development Security Controls Implemented  
**Production Ready**: ❌ NO - Additional hardening required (see Known Limitations)

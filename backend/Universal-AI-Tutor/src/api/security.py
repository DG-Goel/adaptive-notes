"""
Security controls for the Universal AI Tutor API.

Implements:
- Path validation and sanitization
- File type and size restrictions
- Input validation
- Credential redaction in logs
- Security warnings
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# Security constants
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_FILE_EXTENSIONS = {
    '.txt', '.md', '.markdown',
    '.py', '.js', '.java', '.cpp', '.c', '.h',
    '.json', '.yaml', '.yml', '.xml',
    '.rst', '.tex', '.html', '.css',
}

# Sensitive patterns to redact in logs
SENSITIVE_PATTERNS = [
    'api_key', 'apikey', 'password', 'secret', 'token', 'credential',
    'groq_api_key', 'qdrant_api_key'
]


def get_allowed_notes_directory() -> Path:
    """
    Get the allowed notes directory from environment or use default.
    
    Returns:
        Path: Canonical path to allowed notes directory
        
    Raises:
        ValueError: If directory doesn't exist or isn't accessible
    """
    # Check for environment variable
    allowed_dir_str = os.getenv("ALLOWED_NOTES_DIR", None)
    
    if allowed_dir_str:
        allowed_dir = Path(allowed_dir_str).resolve()
    else:
        # Default to ./notes in workspace root
        allowed_dir = Path("./notes").resolve()
    
    # Ensure directory exists
    if not allowed_dir.exists():
        logger.warning(
            f"Allowed notes directory does not exist: {allowed_dir}",
            extra={"directory": str(allowed_dir)}
        )
        # Create it if it doesn't exist
        allowed_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created allowed notes directory: {allowed_dir}")
    
    if not allowed_dir.is_dir():
        raise ValueError(f"Allowed notes path is not a directory: {allowed_dir}")
    
    return allowed_dir


def validate_file_path(file_path: str, allowed_directory: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Validate that a file path is safe and within allowed directory.
    
    Checks:
    - Path traversal attempts (../)
    - Symlink escapes
    - Path is within allowed directory
    - File exists and is readable
    - File extension is allowed
    - File size is within limits
    
    Args:
        file_path: Path to validate
        allowed_directory: Optional allowed directory (default: from config)
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error description") if invalid
    """
    if not file_path:
        return False, "File path is empty"
    
    # Get allowed directory
    if allowed_directory is None:
        try:
            allowed_directory = get_allowed_notes_directory()
        except ValueError as e:
            return False, f"Configuration error: {str(e)}"
    
    # Resolve to canonical path (handles .., symlinks, etc.)
    try:
        canonical_path = Path(file_path).resolve()
    except Exception as e:
        return False, f"Invalid path format: {str(e)}"
    
    # Check if path is within allowed directory
    try:
        # is_relative_to() is Python 3.9+, use alternative for compatibility
        canonical_path.relative_to(allowed_directory)
    except ValueError:
        return False, f"Path is outside allowed directory: {allowed_directory}"
    
    # Check file exists
    if not canonical_path.exists():
        return False, f"File does not exist: {canonical_path}"
    
    # Check it's a file (not directory)
    if not canonical_path.is_file():
        return False, f"Path is not a regular file: {canonical_path}"
    
    # Check file extension
    file_ext = canonical_path.suffix.lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        return False, f"File type not allowed: {file_ext}. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
    
    # Check file size
    try:
        file_size = canonical_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"
    except Exception as e:
        return False, f"Cannot access file: {str(e)}"
    
    # All checks passed
    return True, ""


def validate_file_paths(file_paths: List[str], allowed_directory: Optional[Path] = None) -> Tuple[List[str], List[str]]:
    """
    Validate multiple file paths.
    
    Args:
        file_paths: List of paths to validate
        allowed_directory: Optional allowed directory
        
    Returns:
        Tuple of (valid_paths, errors)
        - valid_paths: List of canonical paths that passed validation
        - errors: List of error messages for invalid paths
    """
    if not file_paths:
        return [], ["No file paths provided"]
    
    if len(file_paths) > 100:
        return [], [f"Too many files: {len(file_paths)} (max: 100)"]
    
    valid_paths = []
    errors = []
    
    for file_path in file_paths:
        is_valid, error_msg = validate_file_path(file_path, allowed_directory)
        if is_valid:
            # Store canonical path
            valid_paths.append(str(Path(file_path).resolve()))
        else:
            errors.append(f"{file_path}: {error_msg}")
    
    return valid_paths, errors


def validate_question(question: str) -> Tuple[bool, str]:
    """
    Validate question input.
    
    Checks:
    - Not empty
    - Reasonable length
    - No suspicious patterns
    
    Args:
        question: Question text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not question:
        return False, "Question cannot be empty"
    
    question = question.strip()
    
    if len(question) < 3:
        return False, "Question too short (min: 3 characters)"
    
    if len(question) > 2000:
        return False, f"Question too long: {len(question)} characters (max: 2000)"
    
    # Check for suspicious patterns (basic SQL injection, command injection)
    suspicious_patterns = [
        "'; DROP TABLE", "'; DELETE FROM", "$(", "`", "${",
        "<script", "javascript:", "onerror=", "onload="
    ]
    
    question_lower = question.lower()
    for pattern in suspicious_patterns:
        if pattern.lower() in question_lower:
            logger.warning(
                f"Suspicious pattern detected in question",
                extra={"pattern": pattern, "question_length": len(question)}
            )
            return False, "Invalid characters in question"
    
    return True, ""


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from text (for logging).
    
    Args:
        text: Text that may contain sensitive data
        
    Returns:
        Text with sensitive data redacted
    """
    if not text:
        return text
    
    redacted = text
    
    # Redact anything that looks like an API key or token
    # Pattern: long alphanumeric strings (> 20 chars)
    import re
    
    # Match common API key patterns
    api_key_pattern = r'([a-zA-Z0-9_-]{32,})'
    redacted = re.sub(api_key_pattern, '[REDACTED]', redacted)
    
    # Match key=value patterns with sensitive keys
    for pattern in SENSITIVE_PATTERNS:
        sensitive_pattern = rf'{pattern}["\']?\s*[:=]\s*["\']?([^\s,\'"}}]+)'
        redacted = re.sub(sensitive_pattern, rf'{pattern}=[REDACTED]', redacted, flags=re.IGNORECASE)
    
    return redacted


def log_security_event(event_type: str, details: dict):
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event
        details: Event details (will be redacted)
    """
    # Redact sensitive data from details
    safe_details = {
        k: redact_sensitive_data(str(v)) if isinstance(v, str) else v
        for k, v in details.items()
    }
    
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            **safe_details
        }
    )


def check_security_warnings() -> List[str]:
    """
    Check for security misconfigurations and return warnings.
    
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check if running with default settings
    if settings.api_host == "0.0.0.0":
        warnings.append(
            "⚠️  API is bound to 0.0.0.0 (all interfaces). "
            "For local development, use 127.0.0.1 instead. "
            "Set API_HOST=127.0.0.1 in .env"
        )
    
    # Check if debug mode is enabled
    if settings.debug and settings.app_env == "production":
        warnings.append(
            "⚠️  Debug mode enabled in production environment. "
            "Set DEBUG=false in .env"
        )
    
    # Check for default API keys
    if not settings.groq_api_key or settings.groq_api_key == "your-api-key-here":
        warnings.append(
            "⚠️  No Groq API key configured. "
            "Set GROQ_API_KEY in .env for real LLM integration"
        )
    
    # Check CORS settings
    # Note: This is checked in main.py where CORS middleware is configured
    
    # Check if notes directory is configured
    try:
        allowed_dir = get_allowed_notes_directory()
        if str(allowed_dir) == str(Path("./notes").resolve()):
            warnings.append(
                f"ℹ️  Using default notes directory: {allowed_dir}. "
                f"To restrict access, set ALLOWED_NOTES_DIR in .env"
            )
    except Exception as e:
        warnings.append(f"⚠️  Error checking notes directory: {str(e)}")
    
    return warnings


def print_security_warnings():
    """Print security warnings to console on startup."""
    warnings = check_security_warnings()
    
    if warnings:
        print("\n" + "="*70)
        print("SECURITY WARNINGS")
        print("="*70)
        for warning in warnings:
            logger.warning("%s", warning)
        print("\n" + "="*70)
        print("⚠️  DO NOT DEPLOY TO PRODUCTION WITHOUT ADDRESSING THESE ISSUES")
        print("="*70 + "\n")
    else:
        logger.info("Security configuration validated")


# Export main functions
__all__ = [
    'validate_file_path',
    'validate_file_paths',
    'validate_question',
    'redact_sensitive_data',
    'log_security_event',
    'check_security_warnings',
    'print_security_warnings',
    'get_allowed_notes_directory',
    'MAX_FILE_SIZE_MB',
    'ALLOWED_FILE_EXTENSIONS',
]

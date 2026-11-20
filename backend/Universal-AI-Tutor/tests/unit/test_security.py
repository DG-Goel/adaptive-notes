"""
Unit tests for API security controls.

Tests:
- Path validation and traversal prevention
- File type and size restrictions
- Input validation
- Credential redaction
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.api.security import (
    validate_file_path,
    validate_file_paths,
    validate_question,
    redact_sensitive_data,
    get_allowed_notes_directory,
)


class TestPathValidation:
    """Test file path validation and security."""
    
    @pytest.fixture
    def temp_notes_dir(self):
        """Create temporary notes directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notes_dir = Path(tmpdir) / "notes"
            notes_dir.mkdir()
            
            # Create a valid test file
            test_file = notes_dir / "test.txt"
            test_file.write_text("Test content")
            
            # Create a file outside notes dir
            outside_file = Path(tmpdir) / "outside.txt"
            outside_file.write_text("Outside content")
            
            yield {
                "notes_dir": notes_dir,
                "test_file": test_file,
                "outside_file": outside_file,
                "tmpdir": Path(tmpdir)
            }
    
    def test_valid_file_path(self, temp_notes_dir):
        """Test that valid file path passes validation."""
        is_valid, error = validate_file_path(
            str(temp_notes_dir["test_file"]),
            temp_notes_dir["notes_dir"]
        )
        
        assert is_valid
        assert error == ""
    
    def test_path_traversal_blocked(self, temp_notes_dir):
        """Test that path traversal attempts are blocked."""
        # Try to access file outside allowed directory using ../
        traversal_path = str(temp_notes_dir["notes_dir"] / ".." / "outside.txt")
        
        is_valid, error = validate_file_path(
            traversal_path,
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "outside allowed directory" in error.lower()
    
    def test_absolute_path_outside_directory_blocked(self, temp_notes_dir):
        """Test that absolute paths outside allowed directory are blocked."""
        is_valid, error = validate_file_path(
            str(temp_notes_dir["outside_file"]),
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "outside allowed directory" in error.lower()
    
    def test_nonexistent_file_blocked(self, temp_notes_dir):
        """Test that nonexistent files are rejected."""
        fake_path = temp_notes_dir["notes_dir"] / "nonexistent.txt"
        
        is_valid, error = validate_file_path(
            str(fake_path),
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "does not exist" in error.lower()
    
    def test_directory_path_blocked(self, temp_notes_dir):
        """Test that directory paths are rejected."""
        is_valid, error = validate_file_path(
            str(temp_notes_dir["notes_dir"]),
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "not a regular file" in error.lower()
    
    def test_invalid_extension_blocked(self, temp_notes_dir):
        """Test that invalid file extensions are blocked."""
        # Create file with invalid extension
        exe_file = temp_notes_dir["notes_dir"] / "malicious.exe"
        exe_file.write_text("fake executable")
        
        is_valid, error = validate_file_path(
            str(exe_file),
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "not allowed" in error.lower()
        assert ".exe" in error.lower()
    
    def test_allowed_extensions(self, temp_notes_dir):
        """Test that all allowed extensions pass validation."""
        allowed_extensions = ['.txt', '.md', '.py', '.json']
        notes_dir = temp_notes_dir["notes_dir"]
        
        for ext in allowed_extensions:
            test_file = notes_dir / f"test{ext}"
            test_file.write_text("content")
            
            is_valid, error = validate_file_path(
                str(test_file),
                notes_dir
            )
            
            assert is_valid, f"Extension {ext} should be allowed"
            assert error == ""
    
    def test_empty_path_rejected(self, temp_notes_dir):
        """Test that empty path is rejected."""
        is_valid, error = validate_file_path(
            "",
            temp_notes_dir["notes_dir"]
        )
        
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_symlink_escape_blocked(self, temp_notes_dir):
        """Test that symlink escapes are blocked."""
        notes_dir = temp_notes_dir["notes_dir"]
        outside_file = temp_notes_dir["outside_file"]
        
        # Create symlink to file outside allowed directory
        symlink_path = notes_dir / "symlink.txt"
        try:
            symlink_path.symlink_to(outside_file)
            
            # Validate - should detect that resolved path is outside
            is_valid, error = validate_file_path(
                str(symlink_path),
                notes_dir
            )
            
            assert not is_valid
            assert "outside allowed directory" in error.lower()
        except OSError:
            # Symlinks may not be supported on all systems
            pytest.skip("Symlinks not supported on this system")


class TestBatchPathValidation:
    """Test batch file path validation."""
    
    @pytest.fixture
    def temp_notes_dir(self):
        """Create temporary notes directory with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notes_dir = Path(tmpdir) / "notes"
            notes_dir.mkdir()
            
            # Create valid files
            (notes_dir / "file1.txt").write_text("content1")
            (notes_dir / "file2.md").write_text("content2")
            
            # Create invalid file
            (notes_dir / "file3.exe").write_text("invalid")
            
            # Create file outside
            outside = Path(tmpdir) / "outside.txt"
            outside.write_text("outside")
            
            yield {
                "notes_dir": notes_dir,
                "valid1": notes_dir / "file1.txt",
                "valid2": notes_dir / "file2.md",
                "invalid_ext": notes_dir / "file3.exe",
                "outside": outside
            }
    
    def test_all_valid_paths(self, temp_notes_dir):
        """Test batch validation with all valid paths."""
        paths = [
            str(temp_notes_dir["valid1"]),
            str(temp_notes_dir["valid2"])
        ]
        
        valid, errors = validate_file_paths(paths, temp_notes_dir["notes_dir"])
        
        assert len(valid) == 2
        assert len(errors) == 0
    
    def test_mixed_valid_invalid_paths(self, temp_notes_dir):
        """Test batch validation with mix of valid and invalid paths."""
        paths = [
            str(temp_notes_dir["valid1"]),
            str(temp_notes_dir["invalid_ext"]),
            str(temp_notes_dir["valid2"]),
            str(temp_notes_dir["outside"])
        ]
        
        valid, errors = validate_file_paths(paths, temp_notes_dir["notes_dir"])
        
        assert len(valid) == 2  # Only the two valid files
        assert len(errors) == 2  # Two invalid files
        assert any("not allowed" in e.lower() for e in errors)
        assert any("outside" in e.lower() for e in errors)
    
    def test_empty_list(self, temp_notes_dir):
        """Test batch validation with empty list."""
        valid, errors = validate_file_paths([], temp_notes_dir["notes_dir"])
        
        assert len(valid) == 0
        assert len(errors) == 1
        assert "no file paths" in errors[0].lower()
    
    def test_too_many_files(self, temp_notes_dir):
        """Test that too many files are rejected."""
        # Create 101 file paths (over limit of 100)
        paths = [f"file{i}.txt" for i in range(101)]
        
        valid, errors = validate_file_paths(paths, temp_notes_dir["notes_dir"])
        
        assert len(valid) == 0
        assert len(errors) == 1
        assert "too many" in errors[0].lower()


class TestQuestionValidation:
    """Test question input validation."""
    
    def test_valid_question(self):
        """Test that valid question passes."""
        is_valid, error = validate_question("What is machine learning?")
        
        assert is_valid
        assert error == ""
    
    def test_empty_question_rejected(self):
        """Test that empty question is rejected."""
        is_valid, error = validate_question("")
        
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_whitespace_only_rejected(self):
        """Test that whitespace-only question is rejected."""
        is_valid, error = validate_question("   ")
        
        assert not is_valid
        assert ("empty" in error.lower() or "too short" in error.lower())
    
    def test_too_short_question_rejected(self):
        """Test that very short question is rejected."""
        is_valid, error = validate_question("ab")
        
        assert not is_valid
        assert "too short" in error.lower()
    
    def test_too_long_question_rejected(self):
        """Test that excessively long question is rejected."""
        long_question = "a" * 2001
        
        is_valid, error = validate_question(long_question)
        
        assert not is_valid
        assert "too long" in error.lower()
    
    def test_sql_injection_detected(self):
        """Test that SQL injection patterns are detected."""
        malicious = "What is ML?'; DROP TABLE users; --"
        
        is_valid, error = validate_question(malicious)
        
        assert not is_valid
        assert "invalid" in error.lower()
    
    def test_command_injection_detected(self):
        """Test that command injection patterns are detected."""
        malicious = "What is $(rm -rf /) machine learning?"
        
        is_valid, error = validate_question(malicious)
        
        assert not is_valid
        assert "invalid" in error.lower()
    
    def test_xss_detected(self):
        """Test that XSS patterns are detected."""
        malicious = "What is <script>alert('xss')</script> ML?"
        
        is_valid, error = validate_question(malicious)
        
        assert not is_valid
        assert "invalid" in error.lower()
    
    def test_normal_special_characters_allowed(self):
        """Test that normal punctuation is allowed."""
        question = "What's the difference between ML & AI? (I'm curious!)"
        
        is_valid, error = validate_question(question)
        
        assert is_valid
        assert error == ""


class TestCredentialRedaction:
    """Test credential redaction in logs."""
    
    def test_api_key_redacted(self):
        """Test that API keys are redacted."""
        text = "Using groq_api_key=sk_abcdefghijklmnopqrstuvwxyz123456"
        redacted = redact_sensitive_data(text)
        
        assert "sk_abcdefghijklmnopqrstuvwxyz123456" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_long_alphanumeric_strings_redacted(self):
        """Test that long alphanumeric strings (likely keys) are redacted."""
        text = "API response: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = redact_sensitive_data(text)
        
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_password_field_redacted(self):
        """Test that password fields are redacted."""
        text = 'password="mysecretpassword123"'
        redacted = redact_sensitive_data(text)
        
        assert "mysecretpassword123" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_token_field_redacted(self):
        """Test that token fields are redacted."""
        text = "Authorization: Bearer token=abc123xyz456def"
        redacted = redact_sensitive_data(text)
        
        assert "abc123xyz456def" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_normal_text_preserved(self):
        """Test that normal text is not redacted."""
        text = "The machine learning model scored 0.95 accuracy"
        redacted = redact_sensitive_data(text)
        
        assert redacted == text  # Should be unchanged
    
    def test_empty_string_handled(self):
        """Test that empty string is handled gracefully."""
        redacted = redact_sensitive_data("")
        
        assert redacted == ""
    
    def test_none_handled(self):
        """Test that None is handled gracefully."""
        redacted = redact_sensitive_data(None)
        
        assert redacted is None


class TestAllowedNotesDirectory:
    """Test allowed notes directory configuration."""
    
    def test_default_directory_created(self, monkeypatch, tmp_path):
        """Test that default directory is created if it doesn't exist."""
        # Change working directory to temp
        monkeypatch.chdir(tmp_path)
        
        # Ensure ALLOWED_NOTES_DIR is not set
        monkeypatch.delenv("ALLOWED_NOTES_DIR", raising=False)
        
        # Get directory (should create ./notes)
        notes_dir = get_allowed_notes_directory()
        
        assert notes_dir.exists()
        assert notes_dir.is_dir()
        assert notes_dir.name == "notes"
    
    def test_custom_directory_from_env(self, monkeypatch, tmp_path):
        """Test that custom directory from environment is used."""
        custom_dir = tmp_path / "custom_notes"
        custom_dir.mkdir()
        
        monkeypatch.setenv("ALLOWED_NOTES_DIR", str(custom_dir))
        
        notes_dir = get_allowed_notes_directory()
        
        assert notes_dir == custom_dir.resolve()
    
    def test_directory_created_if_missing(self, monkeypatch, tmp_path):
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_notes"
        
        monkeypatch.setenv("ALLOWED_NOTES_DIR", str(new_dir))
        
        notes_dir = get_allowed_notes_directory()
        
        assert notes_dir.exists()
        assert notes_dir.is_dir()

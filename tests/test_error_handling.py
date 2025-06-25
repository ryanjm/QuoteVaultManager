import tempfile
import os
from quote_vault_manager.quote_parser import validate_block_ids
from quote_vault_manager.config import load_config, ConfigError

def test_duplicate_block_id_detection():
    """Test that duplicate block IDs are detected and reported."""
    markdown_content = """---
sync_quotes: true
---

> First quote
^Quote001

> Second quote
^Quote001

> Third quote
^Quote002
"""
    errors = validate_block_ids(markdown_content)
    
    assert len(errors) == 1
    assert "Duplicate block ID '^Quote001'" in errors[0]
    assert "line" in errors[0]
    
    print("Duplicate block ID detection test passed.")

def test_invalid_block_id_format():
    """Test that invalid block ID formats are detected."""
    markdown_content = """---
sync_quotes: true
---

> First quote
^Quote1

> Second quote
^QuoteABC

> Third quote
^Quote001
"""
    errors = validate_block_ids(markdown_content)
    
    assert len(errors) == 2
    assert "Invalid block ID format" in errors[0]
    assert "Invalid block ID format" in errors[1]
    
    print("Invalid block ID format detection test passed.")

def test_valid_block_ids():
    """Test that valid block IDs don't generate errors."""
    markdown_content = """---
sync_quotes: true
---

> First quote
^Quote001

> Second quote
^Quote002

> Third quote
^Quote003
"""
    errors = validate_block_ids(markdown_content)
    
    assert len(errors) == 0
    
    print("Valid block IDs test passed.")

def test_config_missing_keys():
    """Test that missing config keys are detected."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
source_vault_path: "/path/to/source"
# Missing other required keys
""")
        config_file = f.name
    
    try:
        try:
            load_config(config_file)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "Missing required config keys" in str(e)
            print("Config missing keys test passed.")
    finally:
        os.unlink(config_file)

def test_config_unexpected_keys():
    """Test that unexpected config keys generate warnings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
source_vault_path: "/path/to/source"
destination_vault_path: "/path/to/dest"
std_log_path: "logs/std.log"
err_log_path: "logs/err.log"
unexpected_key: "some value"
another_unexpected: "another value"
""")
        config_file = f.name
    
    try:
        # This should work but generate warnings
        config = load_config(config_file)
        assert config is not None
        print("Config unexpected keys test passed.")
    finally:
        os.unlink(config_file)

if __name__ == "__main__":
    test_duplicate_block_id_detection()
    test_invalid_block_id_format()
    test_valid_block_ids()
    test_config_missing_keys()
    test_config_unexpected_keys()
    print("All error handling tests passed!") 
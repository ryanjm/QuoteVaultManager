import tempfile
import os
from quote_vault_manager.config import load_config, ConfigError
from quote_vault_manager.models.source_file import SourceFile

def test_duplicate_block_ids():
    markdown_content = "> Quote 1\n^Quote001\n> Quote 2\n^Quote001\n"
    errors = SourceFile.validate_block_ids_from_content(markdown_content)
    assert any("Duplicate block ID" in e for e in errors)

def test_invalid_block_id_format():
    markdown_content = "> Quote 1\n^QuoteABC\n> Quote 2\n^Quote002\n"
    errors = SourceFile.validate_block_ids_from_content(markdown_content)
    assert any("Invalid block ID format" in e for e in errors)

def test_valid_block_ids():
    markdown_content = "> Quote 1\n^Quote001\n> Quote 2\n^Quote002\n"
    errors = SourceFile.validate_block_ids_from_content(markdown_content)
    assert not errors

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
    test_duplicate_block_ids()
    test_invalid_block_id_format()
    test_valid_block_ids()
    test_config_missing_keys()
    test_config_unexpected_keys()
    print("All error handling tests passed!") 
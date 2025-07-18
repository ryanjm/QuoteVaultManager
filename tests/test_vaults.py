import os
import tempfile
import pytest
from quote_vault_manager.models.source_vault import SourceVault
from quote_vault_manager.models.destination_vault import DestinationVault
from quote_vault_manager.models.source_file import SourceFile
from quote_vault_manager.models.destination_file import DestinationFile


def test_source_vault_load_and_save(tmp_path):
    # Create two source files with sync_quotes flag
    file1 = tmp_path / "a.md"
    file2 = tmp_path / "b.md"
    file1.write_text("---\nsync_quotes: true\n---\n\n> Quote 1\n^Quote001\n")
    file2.write_text("---\nsync_quotes: true\n---\n\n> Quote 2\n^Quote002\n")
    vault = SourceVault(str(tmp_path))
    assert len(vault.files) == 2
    # Test batch save (should not change content)
    vault.save_all()
    assert file1.read_text() == "---\nsync_quotes: true\n---\n\n> Quote 1\n^Quote001\n"
    assert file2.read_text() == "---\nsync_quotes: true\n---\n\n> Quote 2\n^Quote002\n"

def test_destination_vault_load_and_save(tmp_path):
    # Create two destination files
    file1 = tmp_path / "a - Quote001 - Test.md"
    file2 = tmp_path / "b - Quote002 - Test.md"
    file1.write_text("---\n---\n\n> Quote 1\n")
    file2.write_text("---\n---\n\n> Quote 2\n")
    vault = DestinationVault(str(tmp_path))
    assert len(vault.files) == 2
    # Test batch save (should not change content)
    vault.save_all()
    assert file1.read_text() == "---\n---\n\n> Quote 1\n"
    assert file2.read_text() == "---\n---\n\n> Quote 2\n" 
import os
import tempfile
import pytest
from quote_vault_manager.models.quote import Quote
from quote_vault_manager.models.source_file import SourceFile
from quote_vault_manager.models.destination_file import DestinationFile


def test_quote_equality_and_diff():
    q1 = Quote("A quote", "^Quote001")
    q2 = Quote("A quote", "^Quote001")
    q3 = Quote("Another quote", "^Quote002")
    assert q1 == q2
    assert q1 != q3
    assert not q1.differs_from(q2)
    assert q1.differs_from(q3)

def test_source_file_from_file_and_save(tmp_path):
    file_path = tmp_path / "source.md"
    content = "> A quote\n^Quote001\n> Another quote\n^Quote002\n"
    file_path.write_text(content)
    source = SourceFile.from_file(str(file_path))
    assert len(source.quotes) == 2
    assert source.quotes[0].text == "A quote"
    assert source.quotes[0].block_id == "^Quote001"
    # Test save
    source.save()
    assert file_path.read_text() == content

def test_destination_file_from_file_and_save(tmp_path):
    file_path = tmp_path / "dest.md"
    content = "---\nblock_id: ^Quote001\n---\n\n> A quote\n^Quote001\n"
    file_path.write_text(content)
    dest = DestinationFile.from_file(str(file_path))
    assert dest.frontmatter["block_id"] == "^Quote001"
    assert dest.quote.text == "A quote"
    # Test save
    dest.save(str(file_path))
    assert file_path.read_text() == content 
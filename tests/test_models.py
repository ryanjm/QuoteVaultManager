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
    # Test direct quote editing (edit first quote)
    q1 = source.quotes[0]
    q1.text = "Edited quote"
    q1.needs_edit = True
    source.save()
    with open(file_path, 'r') as f:
        updated_content = f.read()
    assert "> Edited quote" in updated_content
    assert "^Quote001" in updated_content
    # Test unwrap_quote (unwrap second quote)
    q2 = source.quotes[1]
    source.unwrap_quote(q2)
    source.save()
    with open(file_path, 'r') as f:
        unwrapped_content = f.read()
    assert '"Another quote"' in unwrapped_content
    assert "^Quote002" not in unwrapped_content

def test_source_file_preserves_non_quote_content(tmp_path):
    file_path = tmp_path / "source.md"
    content = """# Header\n\nSome intro text.\n\n> A quote\n^Quote001\n\nSome middle text.\n\n> Another quote\n^Quote002\n\nFooter text."""
    file_path.write_text(content)
    source = SourceFile.from_file(str(file_path))
    # Edit first quote directly
    q1 = source.quotes[0]
    q1.text = "Changed quote"
    q1.needs_edit = True
    # Unwrap second quote
    q2 = source.quotes[1]
    source.unwrap_quote(q2)
    source.save()
    with open(file_path, 'r') as f:
        result = f.read()
    assert '# Header' in result
    assert 'Some intro text.' in result
    assert '> Changed quote' in result
    assert 'Some middle text.' in result
    assert '"Another quote"' in result
    assert 'Footer text.' in result
    assert '^Quote002' not in result

def test_destination_file_from_file_and_save(tmp_path):
    file_path = tmp_path / "Book - Quote001 - Test.md"
    content = "---\n---\n\n> A quote\n"
    file_path.write_text(content)
    dest = DestinationFile.from_file(str(file_path))
    assert dest.quote.text == "A quote"
    assert dest.quote.block_id == "^Quote001"
    # Test save
    dest.save(str(file_path))
    assert file_path.read_text() == content 
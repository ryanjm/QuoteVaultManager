from quote_vault_manager.models.source_file import SourceFile

def test_extract_blockquotes():
    sample = (
        "> First quote line 1\n"
        "> First quote line 2\n"
        "\n"
        "> Second quote\n"
        "\n"
        "Not a quote\n"
        "> Third quote\n"
        "> Still third quote\n"
    )
    expected = [
        "First quote line 1\nFirst quote line 2",
        "Second quote",
        "Third quote\nStill third quote"
    ]
    # Use extract_blockquotes_with_ids and extract just the quote text
    result = [quote_text for quote_text, _ in SourceFile.extract_blockquotes_with_ids(sample)]
    print("Extracted:", result)
    assert result == expected, f"Expected {expected}, got {result}"
    print("Test passed.")

def test_extract_blockquotes_with_ids():
    sample = (
        "> First quote line 1\n"
        "> First quote line 2\n"
        "^Quote001\n"
        "\n"
        "> Second quote\n"
        "^Quote002\n"
        "\n"
        "> Third quote\n"
        "> Still third quote\n"
        "^Quote003\n"
    )
    expected = [
        ("First quote line 1\nFirst quote line 2", "^Quote001"),
        ("Second quote", "^Quote002"),
        ("Third quote\nStill third quote", "^Quote003")
    ]
    result = SourceFile.extract_blockquotes_with_ids(sample)
    print("Extracted with IDs:", result)
    assert result == expected, f"Expected {expected}, got {result}"
    print("Test with IDs passed.")

def test_get_next_block_id():
    # Test with no existing IDs
    sample1 = "> Some quote\n> Another line\n"
    result1 = SourceFile.get_next_block_id(sample1)
    assert result1 == "^Quote001", f"Expected ^Quote001, got {result1}"
    
    # Test with existing IDs
    sample2 = (
        "> First quote\n"
        "^Quote001\n"
        "> Second quote\n"
        "^Quote003\n"
        "> Third quote\n"
        "^Quote005\n"
    )
    result2 = SourceFile.get_next_block_id(sample2)
    assert result2 == "^Quote006", f"Expected ^Quote006, got {result2}"
    
    # Test transition from Quote999 to Quote1000
    sample3 = (
        "> Some quote\n"
        "^Quote999\n"
    )
    result3 = SourceFile.get_next_block_id(sample3)
    assert result3 == "^Quote1000", f"Expected ^Quote1000, got {result3}"
    
    print("Next block ID tests passed.")

if __name__ == "__main__":
    test_extract_blockquotes()
    test_extract_blockquotes_with_ids()
    test_get_next_block_id() 
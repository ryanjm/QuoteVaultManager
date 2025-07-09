"""
Source file synchronization logic for processing individual source files.
"""

import os
from typing import Dict, Any, Optional
from .quote_parser import extract_blockquotes_with_ids, validate_block_ids
from .quote_writer import (
    write_quote_file, update_quote_file_if_changed, delete_quote_file,
    find_quote_files_for_source, ensure_block_id_in_source, create_quote_filename
)
from .file_utils import get_book_title_from_path, get_vault_name_from_path

def sync_source_file(
    source_file: str, 
    destination_path: str, 
    dry_run: bool = False, 
    source_vault_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Syncs a single source file to the quote vault.
    Returns a dictionary with sync results.
    """
    results = _init_results(source_file)
    vault_name = get_vault_name_from_path(source_vault_path) if source_vault_path else "Notes"

    content: Optional[str] = _read_and_validate_source_file(source_file, results)
    if not content:
        return results
    quotes_with_ids = extract_blockquotes_with_ids(content)
    block_id_map, next_block_num = _collect_block_ids(quotes_with_ids)

    # Assign missing block IDs and update source file if needed
    quotes_with_ids, block_ids_added = _assign_missing_block_ids(source_file, quotes_with_ids, block_id_map, next_block_num, dry_run, results)
    if block_ids_added and not dry_run:
        # Re-read content and quotes if any block IDs were added (only in non-dry-run mode)
        content = _read_and_validate_source_file(source_file, results)
        quotes_with_ids = extract_blockquotes_with_ids(content)
        block_id_map, _ = _collect_block_ids(quotes_with_ids)

    _sync_quote_files(
        source_file, destination_path, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path, results
    )
    _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results)
    return results

def _extract_block_id_from_filename(filename: str) -> str:
    """Extract block ID from filename if possible."""
    if ' - Quote' in filename:
        parts = filename.split(' - Quote')
        if len(parts) >= 2:
            block_id_part = parts[1].split(' - ')[0]
            return f"^Quote{block_id_part}"
    return ""

def _build_source_file_path(source_path: Optional[str], source_vault_path: Optional[str]) -> Optional[str]:
    """Build full path to source file."""
    if not isinstance(source_path, str) or not source_path:
        return None
    if source_vault_path and isinstance(source_vault_path, str):
        return os.path.join(source_vault_path, source_path)
    return source_path

def _update_quote_file_frontmatter(file_path: str, frontmatter_dict: dict) -> None:
    """Update the frontmatter in a quote file."""
    from .quote_writer import frontmatter_dict_to_str
    new_frontmatter = frontmatter_dict_to_str(frontmatter_dict)
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    parts = file_content.split('---', 2)
    if len(parts) >= 3:
        new_content = f"---\n{new_frontmatter}\n---\n{parts[2]}"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

def is_edited_quote_file(file_path: str) -> bool:
    """Return True if file is a markdown file with edited: true in frontmatter."""
    if not file_path.endswith('.md'):
        return False
    from .quote_writer import read_quote_file_content, frontmatter_str_to_dict
    frontmatter, _ = read_quote_file_content(file_path)
    if not frontmatter:
        return False
    fm = frontmatter_str_to_dict(frontmatter)
    return fm.get('edited') is True

def get_edited_quote_info(file_path: str, filename: str) -> tuple:
    """Extract source_path, block_id (from filename), new_quote_text, and frontmatter dict from file."""
    from .quote_writer import read_quote_file_content, frontmatter_str_to_dict, extract_quote_text_from_content
    frontmatter, content = read_quote_file_content(file_path)
    fm = frontmatter_str_to_dict(frontmatter) if frontmatter else {}
    source_path = fm.get('source_path') if isinstance(fm.get('source_path'), str) else None
    block_id = _extract_block_id_from_filename(filename)
    new_quote_text = extract_quote_text_from_content(content or "")
    return source_path, block_id, new_quote_text, fm

def process_edited_quote(file_path: str, source_path: str, block_id: str, new_quote_text: str, fm: dict, dry_run: bool, source_vault_path: str) -> bool:
    """Overwrite quote in source file and update frontmatter if needed."""
    from .quote_writer import overwrite_quote_in_source
    if not (source_path and block_id and new_quote_text):
        return False
    source_file_path = _build_source_file_path(source_path, source_vault_path)
    if not isinstance(source_file_path, str) or not source_file_path:
        return False
    updated = overwrite_quote_in_source(source_file_path, block_id, new_quote_text, dry_run)
    if updated and not dry_run:
        fm['edited'] = False
        _update_quote_file_frontmatter(file_path, fm)
    return updated

def sync_edited_quotes(destination_path: str, dry_run: bool = False, vault_name: str = "Notes", source_vault_path: str = None) -> int:
    """Sync edited quotes back to source files."""
    if not isinstance(destination_path, str) or not destination_path:
        return 0
    updated_count = 0
    dest_path_str: str = str(destination_path)
    for root, dirs, files in os.walk(dest_path_str):
        for file in files:
            file_path = os.path.join(root, file)
            if not is_edited_quote_file(file_path):
                continue
            source_path, block_id, new_quote_text, fm = get_edited_quote_info(file_path, file)
            if process_edited_quote(file_path, source_path, block_id, new_quote_text, fm, dry_run, source_vault_path or ""):
                updated_count += 1
    return updated_count

def _init_results(source_file: str) -> Dict[str, Any]:
    """Initialize the results dictionary for sync operations."""
    return {
        'file': source_file,
        'quotes_processed': 0,
        'quotes_created': 0,
        'quotes_updated': 0,
        'block_ids_added': 0,
        'errors': []
    }

def _read_and_validate_source_file(source_file: str, results: Dict[str, Any]) -> str:
    """Read and validate a source file's content, returning the content or an empty string on error."""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        block_id_errors = validate_block_ids(content)
        if block_id_errors:
            for error in block_id_errors:
                results['errors'].append(f"{source_file}: {error}")
            return ""
        return content
    except UnicodeDecodeError as e:
        results['errors'].append(f"Unicode decode error in {source_file}: {e}")
    except PermissionError as e:
        results['errors'].append(f"Permission denied reading {source_file}: {e}")
    except Exception as e:
        results['errors'].append(f"Error reading {source_file}: {e}")
    return ""

def _collect_block_ids(quotes_with_ids):
    """Return a map of quote indices to block IDs and the next available block number."""
    block_id_map = {}
    used_block_nums = set()
    for idx, (_, block_id) in enumerate(quotes_with_ids):
        if block_id and block_id.startswith('^Quote'):
            try:
                num = int(block_id.replace('^Quote', ''))
                used_block_nums.add(num)
                block_id_map[idx] = block_id
            except Exception:
                pass
    next_block_num = max(used_block_nums) + 1 if used_block_nums else 1
    return block_id_map, next_block_num

def _assign_missing_block_ids(source_file, quotes_with_ids, block_id_map, next_block_num, dry_run, results):
    """Assign missing block IDs to quotes and update the source file. Returns updated quotes and a flag."""
    added = False
    updated_quotes = []
    for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
        if block_id is None:
            new_block_id = f'^Quote{next_block_num:03d}'
            next_block_num += 1
            ensure_block_id_in_source(source_file, quote_text, new_block_id, dry_run)
            results['block_ids_added'] += 1
            updated_quotes.append((quote_text, new_block_id))
            added = True
        else:
            updated_quotes.append((quote_text, block_id))
    return updated_quotes, added

def _sync_quote_files(
    source_file, destination_path, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path, results
):
    """Create or update quote files for all quotes in the source file."""
    book_title = get_book_title_from_path(source_file)
    for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
        results['quotes_processed'] += 1
        if block_id is None:
            results['errors'].append(f"Quote at index {idx} has no block ID after assignment")
            continue
        filename = create_quote_filename(book_title, block_id, quote_text)
        quote_file_path = os.path.join(destination_path, book_title, filename)
        if os.path.exists(quote_file_path):
            updated = update_quote_file_if_changed(
                quote_file_path, quote_text, source_file, block_id, 
                dry_run, vault_name, source_vault_path or ""
            )
            if updated:
                results['quotes_updated'] += 1
        else:
            write_quote_file(
                destination_path, book_title, block_id, quote_text, 
                source_file, dry_run, vault_name, source_vault_path or ""
            )
            results['quotes_created'] += 1

def _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results):
    """Remove quote files that no longer have a corresponding blockquote in the source file."""
    existing_block_ids = set(block_id_map.values())
    existing_quote_files = find_quote_files_for_source(destination_path, source_file)
    for quote_file in existing_quote_files:
        filename = os.path.basename(quote_file)
        if ' - Quote' in filename:
            parts = filename.split(' - Quote')
            if len(parts) >= 2:
                block_id_part = parts[1].split(' - ')[0]
                block_id = f"^Quote{block_id_part}"
                if block_id not in existing_block_ids:
                    results['quotes_deleted'] = results.get('quotes_deleted', 0) + 1
                    delete_quote_file(quote_file, dry_run) 
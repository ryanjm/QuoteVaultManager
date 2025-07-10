"""
Source file synchronization logic for processing individual source files.
"""

import os
from typing import Dict, Any, Optional
from .quote_parser import extract_blockquotes_with_ids, validate_block_ids
# All quote file utilities now live on DestinationFile or DestinationVault
from .file_utils import get_book_title_from_path, get_vault_name_from_path
from .models.source_file import SourceFile
from .models.destination_file import DestinationFile, Quote

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

    # Use SourceFile object for all operations
    source = SourceFile.from_file(source_file)
    errors = source.validate_block_ids()
    if errors:
        results['errors'].extend(errors)
        return results

    block_ids_added = source.assign_missing_block_ids(dry_run)
    results['block_ids_added'] += block_ids_added
    if block_ids_added and not dry_run:
        source = SourceFile.from_file(source_file)  # Reload to get updated block IDs

    # Prepare quotes_with_ids for downstream logic
    quotes_with_ids = [(q.text, q.block_id) for q in source.quotes]
    block_id_map = {i: q.block_id for i, q in enumerate(source.quotes) if q.block_id}

    _sync_quote_files(
        source_file, destination_path, quotes_with_ids, block_id_map, dry_run, vault_name, source_vault_path, results
    )
    _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results)

    # Save any changes to the source file (quotes, block IDs)
    if block_ids_added and not dry_run:
        source.save()

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

def sync_edited_quotes(destination_path: str, dry_run: bool = False, vault_name: str = "Notes", source_vault_path: str = None) -> int:
    """Sync edited quotes back to source files."""
    from .models.destination_file import DestinationFile
    from .models.source_file import SourceFile
    if not isinstance(destination_path, str) or not destination_path:
        return 0
    updated_count = 0
    dest_path_str: str = str(destination_path)
    for root, dirs, files in os.walk(dest_path_str):
        for file in files:
            file_path = os.path.join(root, file)
            if not DestinationFile.is_edited_quote_file(file_path):
                continue
            source_path, block_id, new_quote_text, fm = DestinationFile.get_edited_quote_info(file_path, file)
            svp = source_vault_path if source_vault_path is not None else ""
            if source_path is None or block_id is None or new_quote_text is None:
                continue
            if SourceFile.process_edited_quote(file_path, source_path, block_id, new_quote_text, fm, dry_run, svp):
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
            # All quote file utilities now live on DestinationFile or DestinationVault
            from .models.destination_file import DestinationFile
            DestinationFile.ensure_block_id_in_source(source_file, quote_text, new_block_id, dry_run)
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
    from .models.destination_file import DestinationFile
    book_title = get_book_title_from_path(source_file)
    for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
        results['quotes_processed'] += 1
        if block_id is None:
            results['errors'].append(f"Quote at index {idx} has no block ID after assignment")
            continue
        filename = DestinationFile.create_quote_filename(book_title, block_id, quote_text)
        quote_file_path = os.path.join(destination_path, book_title, filename)
        if os.path.exists(quote_file_path):
            dest = DestinationFile.from_file(quote_file_path)
            updated = False
            if dest.quote.text != quote_text:
                dest.quote.text = quote_text
                updated = True
            if dest.quote.block_id != block_id:
                dest.quote.block_id = block_id
                updated = True
            if updated and not dry_run:
                dest.save(quote_file_path)
                results['quotes_updated'] += 1
        else:
            # Create new DestinationFile and save
            from quote_vault_manager.quote_writer import frontmatter_dict_to_str
            frontmatter = {
                'block_id': block_id,
                'vault': vault_name,
                'delete': False,
                'favorite': False,
                'edited': False
            }
            dest = DestinationFile(frontmatter, Quote(quote_text, block_id))
            if not dry_run:
                os.makedirs(os.path.dirname(quote_file_path), exist_ok=True)
                dest.save(quote_file_path)
            results['quotes_created'] += 1

def _remove_orphaned_quote_files(source_file, destination_path, block_id_map, dry_run, results):
    """Remove quote files that no longer have a corresponding blockquote in the source file."""
    from .models.destination_file import DestinationFile
    from .models.destination_vault import DestinationVault
    existing_block_ids = set(block_id_map.values())
    vault = DestinationVault(destination_path)
    existing_quote_files = vault.find_quote_files_for_source(source_file)
    for quote_file in existing_quote_files:
        filename = os.path.basename(quote_file)
        if ' - Quote' in filename:
            parts = filename.split(' - Quote')
            if len(parts) >= 2:
                block_id_part = parts[1].split(' - ')[0]
                block_id = f"^Quote{block_id_part}"
                if block_id not in existing_block_ids:
                    results['quotes_deleted'] = results.get('quotes_deleted', 0) + 1
                    if not dry_run:
                        DestinationFile.delete(quote_file) 
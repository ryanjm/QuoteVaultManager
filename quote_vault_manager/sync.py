import os
import yaml
from typing import List, Dict, Any
from .config import load_config, ConfigError
from .quote_parser import extract_blockquotes_with_ids, get_next_block_id, validate_block_ids
from .quote_writer import (
    write_quote_file, update_quote_file_if_changed, delete_quote_file,
    find_quote_files_for_source, has_delete_flag, unwrap_quote_in_source,
    ensure_block_id_in_source, create_obsidian_uri,
    frontmatter_str_to_dict, frontmatter_dict_to_str, read_quote_file_content
)
import importlib
import glob
from . import VERSION

def has_sync_quotes_flag(file_path: str) -> bool:
    """
    Checks if a markdown file has sync_quotes: true in its frontmatter.
    Returns True if the flag is set, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                return 'sync_quotes: true' in frontmatter
        
        return False
    except Exception:
        return False

def get_markdown_files(directory: str) -> List[str]:
    """
    Recursively finds all markdown files in the given directory.
    Returns a list of file paths.
    """
    markdown_files = []
    
    if not os.path.exists(directory):
        return markdown_files
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    
    return markdown_files

def get_book_title_from_path(file_path: str) -> str:
    """
    Extracts the book title from a file path.
    Removes the .md extension and returns the filename.
    """
    filename = os.path.basename(file_path)
    return filename.replace('.md', '')

def get_vault_name_from_path(vault_path: str) -> str:
    """Extracts the vault name (last folder) from a full vault path."""
    return os.path.basename(os.path.normpath(vault_path))

def apply_transformations_to_quote_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Applies all necessary transformations to a quote file and updates it if needed.
    Returns True if the file was (or would be) updated, False otherwise.
    """
    frontmatter, content = read_quote_file_content(file_path)
    if frontmatter is None:
        return False
    fm_dict = frontmatter_str_to_dict(frontmatter)
    file_version = fm_dict.get('version', 'V0.0')
    updated = False
    # Only V0.1 for now, but this will scale
    if file_version != VERSION:
        from quote_vault_manager.transformations import v0_1_add_version
        note = {'frontmatter': fm_dict}
        note = v0_1_add_version.transform(note)
        note['frontmatter']['version'] = VERSION
        new_frontmatter = frontmatter_dict_to_str(note['frontmatter'])
        if new_frontmatter != frontmatter:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"---\n{new_frontmatter}\n---\n\n{content}")
            updated = True
    return updated

def sync_source_file(source_file: str, 
    destination_path: str, 
    dry_run: bool = False, 
    source_vault_path: str | None = None) -> Dict[str, Any]:
    """
    Syncs a single source file to the quote vault.
    Returns a dictionary with sync results.
    """
    results = {
        'file': source_file,
        'quotes_processed': 0,
        'quotes_created': 0,
        'quotes_updated': 0,
        'block_ids_added': 0,
        'errors': []
    }
    
    # Extract vault name for Obsidian URI
    vault_name = get_vault_name_from_path(source_vault_path) if source_vault_path else "Notes"
    
    try:
        # Read source file content
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            results['errors'].append(f"Unicode decode error in {source_file}: {e}")
            return results
        except PermissionError as e:
            results['errors'].append(f"Permission denied reading {source_file}: {e}")
            return results
        except Exception as e:
            results['errors'].append(f"Error reading {source_file}: {e}")
            return results
        
        # Validate block IDs before processing
        block_id_errors = validate_block_ids(content)
        if block_id_errors:
            for error in block_id_errors:
                results['errors'].append(f"{source_file}: {error}")
            return results
        
        # Extract quotes with their block IDs
        quotes_with_ids = extract_blockquotes_with_ids(content)
        
        # Track used block IDs
        used_block_nums = set()
        for _, block_id in quotes_with_ids:
            if block_id and block_id.startswith('^Quote'):
                try:
                    used_block_nums.add(int(block_id.replace('^Quote', '')))
                except Exception:
                    pass
        next_block_num = max(used_block_nums) + 1 if used_block_nums else 1
        
        # Get book title
        book_title = get_book_title_from_path(source_file)
        
        # Process each quote
        for idx, (quote_text, block_id) in enumerate(quotes_with_ids):
            results['quotes_processed'] += 1
            
            # If quote doesn't have a block ID, assign one
            if block_id is None:
                block_id = f'^Quote{next_block_num:03d}'
                next_block_num += 1
                ensure_block_id_in_source(source_file, quote_text, block_id, dry_run)
                results['block_ids_added'] += 1
                # Update content so subsequent get_next_block_id sees the new ID
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Generate quote filename
            from .quote_writer import create_quote_filename
            filename = create_quote_filename(book_title, block_id, quote_text)
            quote_file_path = os.path.join(destination_path, book_title, filename)
            
            # Check if quote file exists
            if os.path.exists(quote_file_path):
                # Update existing quote file if content changed
                updated = update_quote_file_if_changed(quote_file_path, quote_text, source_file, block_id, dry_run, vault_name, source_vault_path or "")
                if updated:
                    results['quotes_updated'] += 1
            else:
                # Create new quote file
                write_quote_file(destination_path, book_title, block_id, quote_text, source_file, dry_run, vault_name, source_vault_path or "")
                results['quotes_created'] += 1
        
        # Handle orphaned quotes (quotes that exist in destination but not in source)
        # Re-extract quotes to get updated block IDs after assignment
        with open(source_file, 'r', encoding='utf-8') as f:
            updated_content = f.read()
        updated_quotes_with_ids = extract_blockquotes_with_ids(updated_content)
        existing_block_ids = {block_id for _, block_id in updated_quotes_with_ids if block_id is not None}
        
        existing_quote_files = find_quote_files_for_source(destination_path, source_file)
        
        for quote_file in existing_quote_files:
            # Extract block ID from filename
            filename = os.path.basename(quote_file)
            if ' - Quote' in filename:
                parts = filename.split(' - Quote')
                if len(parts) >= 2:
                    block_id_part = parts[1].split(' - ')[0]
                    block_id = f"^Quote{block_id_part}"
                    
                    if block_id not in existing_block_ids:
                        # This quote no longer exists in source, delete it
                        results['quotes_deleted'] = results.get('quotes_deleted', 0) + 1
                        delete_quote_file(quote_file, dry_run)
        
    except Exception as e:
        results['errors'].append(f"Error processing {source_file}: {str(e)}")
    
    return results

def process_delete_flags(destination_path: str, source_vault_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Processes quote files with delete: true flag and unwraps them in source files.
    Returns a dictionary with processing results.
    """
    results = {
        'quotes_unwrapped': 0,
        'errors': []
    }
    
    if not os.path.exists(destination_path):
        return results
    
    # Find all quote files with delete: true
    for root, dirs, files in os.walk(destination_path):
        for file in files:
            if file.endswith('.md'):
                quote_file_path = os.path.join(root, file)
                
                if has_delete_flag(quote_file_path):
                    try:
                        # Read the quote file to get source file and block ID
                        frontmatter, _ = read_quote_file_content(quote_file_path)
                        if frontmatter:
                            # Extract source file from frontmatter
                            for line in frontmatter.split('\n'):
                                if line.strip().startswith('source_path:'):
                                    # Extract everything after 'source_path:' and strip whitespace/quotes
                                    source_file = line.split('source_path:', 1)[1].strip().strip('"')
                                    source_file_path = os.path.join(source_vault_path, source_file)
                                    if not os.path.exists(source_file_path):
                                        # Recursively search for the file in the source vault
                                        found_path = None
                                        for root_dir, _, files_in_dir in os.walk(source_vault_path):
                                            if source_file in files_in_dir:
                                                found_path = os.path.join(root_dir, source_file)
                                                break
                                        if found_path:
                                            source_file_path = found_path
                                        else:
                                            error_msg = f"  ERROR: Could not find source file {source_file} in {source_vault_path} for quote file {quote_file_path}"
                                            print(error_msg)
                                            results['errors'].append(error_msg)
                                            continue
                                    # Extract block ID from filename
                                    filename = os.path.basename(quote_file_path)
                                    if ' - Quote' in filename:
                                        parts = filename.split(' - Quote')
                                        if len(parts) >= 2:
                                            block_id_part = parts[1].split(' - ')[0]
                                            block_id = f"^Quote{block_id_part}"
                                            # Unwrap the quote in source file
                                            unwrapped = unwrap_quote_in_source(source_file_path, block_id, dry_run)
                                            if unwrapped:
                                                results['quotes_unwrapped'] += 1
                                            # Delete the quote file
                                            delete_quote_file(quote_file_path, dry_run)
                                            break
                    except Exception as e:
                        results['errors'].append(f"Error processing delete flag for {quote_file_path}: {str(e)}")
    
    return results

def sync_vaults(config: Dict[str, str], dry_run: bool = False) -> Dict[str, Any]:
    """
    Main sync function that orchestrates the entire quote vault synchronization process.
    Returns a dictionary with overall sync results.
    """
    results = {
        'source_files_processed': 0,
        'total_quotes_processed': 0,
        'total_quotes_created': 0,
        'total_quotes_updated': 0,
        'total_block_ids_added': 0,
        'total_quotes_deleted': 0,
        'total_quotes_unwrapped': 0,
        'errors': []
    }
    
    source_vault_path = config['source_vault_path']
    destination_vault_path = config['destination_vault_path']
    
    # Step 0: Apply transformations to all quote files before sync
    quote_files = glob.glob(os.path.join(destination_vault_path, '**', '*.md'), recursive=True)
    files_updated = 0
    for file_path in quote_files:
        if apply_transformations_to_quote_file(file_path, dry_run=dry_run):
            files_updated += 1
    if files_updated:
        if dry_run:
            print(f"🔄 [DRY-RUN] {files_updated} quote files would be updated to version {VERSION}")
        else:
            print(f"🔄 {files_updated} quote files updated to version {VERSION}")

    # Step 1: Process delete flags first
    delete_results = process_delete_flags(destination_vault_path, source_vault_path, dry_run)
    results['total_quotes_unwrapped'] = delete_results['quotes_unwrapped']
    results['errors'].extend(delete_results['errors'])
    
    # Step 2: Process source files
    markdown_files = get_markdown_files(source_vault_path)
    
    for file_path in markdown_files:
        if has_sync_quotes_flag(file_path):
            file_results = sync_source_file(file_path, destination_vault_path, dry_run, source_vault_path)
            
            results['source_files_processed'] += 1
            results['total_quotes_processed'] += file_results['quotes_processed']
            results['total_quotes_created'] += file_results['quotes_created']
            results['total_quotes_updated'] += file_results['quotes_updated']
            results['total_block_ids_added'] += file_results['block_ids_added']
            results['total_quotes_deleted'] += file_results.get('quotes_deleted', 0)
            results['errors'].extend(file_results['errors'])
    
    return results 
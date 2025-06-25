import argparse
import sys
from quote_vault_manager.config import load_config, ConfigError
from quote_vault_manager.sync import sync_vaults
from quote_vault_manager.logger import setup_logging, log_sync_action, log_error

def main():
    parser = argparse.ArgumentParser(
        description="Quote Vault Manager - Sync quotes between Obsidian vaults",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m quote_vault_manager --config config.yaml --dry-run
  python -m quote_vault_manager --config config.yaml
        """
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (show what would be done without making changes)")
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Setup logging
        std_logger, err_logger = setup_logging(config)
        
        # Run sync
        if args.dry_run:
            print("🔍 Running in DRY-RUN mode - no changes will be made")
            print("=" * 50)
            log_sync_action(std_logger, "DRY-RUN", "Starting sync in dry-run mode", dry_run=True)
        
        results = sync_vaults(config, dry_run=args.dry_run)
        
        # Log results
        log_sync_action(std_logger, "SYNC_COMPLETED", 
                       f"Processed {results['source_files_processed']} files, "
                       f"{results['total_quotes_processed']} quotes", 
                       dry_run=args.dry_run)
        
        # Display results
        print(f"\n📊 Sync Results:")
        print(f"  Source files processed: {results['source_files_processed']}")
        print(f"  Total quotes processed: {results['total_quotes_processed']}")
        print(f"  Quotes created: {results['total_quotes_created']}")
        print(f"  Quotes updated: {results['total_quotes_updated']}")
        print(f"  Block IDs added: {results['total_block_ids_added']}")
        print(f"  Quotes deleted: {results.get('total_quotes_deleted', 0)}")
        print(f"  Quotes unwrapped: {results.get('total_quotes_unwrapped', 0)}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
                log_error(err_logger, error, "Sync Error")
            sys.exit(1)
        else:
            print(f"\n✅ Sync completed successfully!")
            if args.dry_run:
                print("💡 Run without --dry-run to apply changes")
    
    except ConfigError as e:
        error_msg = f"Configuration error: {e}"
        print(f"❌ {error_msg}")
        if 'err_logger' in locals():
            log_error(err_logger, str(e), "Configuration Error")
        sys.exit(1)
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        print(f"❌ {error_msg}")
        if 'err_logger' in locals():
            log_error(err_logger, str(e), "File Not Found")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        if 'err_logger' in locals():
            log_error(err_logger, str(e), "Unexpected Error")
        sys.exit(1)

if __name__ == "__main__":
    main() 
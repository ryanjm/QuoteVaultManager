import argparse
from quote_vault_manager.config import load_config, ConfigError

def main():
    parser = argparse.ArgumentParser(description="Quote Vault Manager")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()
    # Placeholder for main logic
    print(f"Config: {args.config}, Dry run: {args.dry_run}")

if __name__ == "__main__":
    main() 
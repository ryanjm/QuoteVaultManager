# Quote Vault Manager

**Quote Vault Manager** is a Python tool to sync blockquotes between a source Obsidian vault (e.g., your main Notes vault) and a destination quote vault. It extracts blockquotes from markdown files, assigns stable block IDs, creates/updates/deletes quote files, and maintains bidirectional links using Obsidian URIs.

## Features

- Extracts multiline blockquotes from markdown files
- Assigns and maintains unique, stable block IDs per quote
- Creates individual quote files in the destination vault with proper naming and frontmatter
- Updates quote files if the source content changes
- Deletes orphaned quote files if the source quote is removed
- Maintains bidirectional links using Obsidian URIs
- Supports dry-run mode for safe testing
- Logs all actions and errors to configurable log files
- CLI interface for easy use

## Installation

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd quote_vault_manager
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

Create a `config.yaml` file in your project directory. Example:

```yaml
source_vault_path: "/path/to/your/Notes"
destination_vault_path: "/path/to/your/QuoteVault"
std_log_path: "./quote_vault_manager.log"
err_log_path: "./quote_vault_manager.err.log"
```

- `source_vault_path`: Full path to your source Obsidian vault (e.g., Notes)
- `destination_vault_path`: Full path to your destination quote vault
- `std_log_path`: Path for standard log output
- `err_log_path`: Path for error log output

## Usage

Run the sync from the command line:

**Dry run (no changes will be made):**
```sh
python -m quote_vault_manager --config config.yaml --dry-run
```

**Real sync (apply changes):**
```sh
python -m quote_vault_manager --config config.yaml
```

- The script will print a summary of actions and any errors.
- On success, quote files will be created/updated/deleted in the destination vault as needed.

## How It Works

- Only files in the source vault with `sync_quotes: true` in their frontmatter are processed.
- Each blockquote is assigned a unique block ID (e.g., `^Quote003`) if it doesn't already have one.
- Quote files are named `[Book Title] - QuoteNNN - [First Few Words].md`.
- Each quote file includes a link back to the source using an Obsidian URI:
  ```
  **Source:** [Book Title](obsidian://open?vault=Notes&file=Book%20Title%23%5EQuote003)
  ```
- If a quote is deleted from the source, the corresponding quote file is deleted from the destination.
- If a quote file is marked with `delete: true`, the quote is unwrapped in the source file.

## Example Directory Structure

```
Notes/
└── Deep Work.md

QuoteVault/
└── Deep Work - Quote003 - Focus without distraction.md
```

## Logging

- All actions and errors are logged to the files specified in your config.
- On error, check the error log for details.

## Requirements

- Python 3.8+
- [PyYAML](https://pyyaml.org/)

## Development & Testing

- Unit tests are included for all major features.
- To run tests:
  ```sh
  python -m unittest discover tests
  ```

## License

MIT License
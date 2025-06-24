## Product Design Requirements

The purpose of the quote vault manager script is to be used to copy quotes from the a source vault (notes) to a new quote vault. It'll look through the files in the main vault (`Notes`) and identify all of the block quotes. It'll then create a new dedicated note in the book vault for each block quote.

This will be run on only on a Mac.

Naming throughout this doc:
- Notes Vault: `'/Users/ryanjm/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes'`
- Quote Vault: `'/Users/ryanjm/Library/Mobile Documents/iCloud~md~obsidian/Documents/ReferenceQuotes'`

There should be a yaml config file for the script (use pyyaml library to read it). This will make it easy for a user to update these paths. The configuration should be a dictionary with the following keys:

- source_vault_path
- destination_vault_path
- std_log_path
- err_log_path

Example:

```YAML
source_vault_path: '/Users/ryanjm/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/_inbox'
destination_vault_path: '/Users/ryanjm/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/_inbox'
std_log_path: 'com.ryanjm.quote-vault-manager.out'
err_log_path: 'com.ryanjm.quote-vault-manager.err'
```

### **✅ GOALS** FOR NAMING CONVENTION

1. **Stable, unique identifier for each quote**
2. **Traceability to the source file and location**
3. **Bidirectional link between quote and book**
4. **Scalability even if quotes move around in the source**

### **🔖 FILE NAMING CONVENTION**

Use this for each quote file (in Quotes vault):

```
[Book Title] - Quote[ID] - [First Few Words].md
```

Example:

```
Deep Work - Quote003 - Focus without distraction.md
```

Where Quote003 is an ID you assign **once**, and do **not change** — even if the quote moves in the original file. These are unique to the file itself (that is there may be a Quote003 in another file). 

Where "First Few Words" is the first 4 or 5 words.

---

### **📁 DIRECTORY STRUCTURE**

In your quotes vault:

```
Quotes/
└── Deep Work - Quote 003 - Focus without distraction.md
```

In your notes vault:

```
Notes/
└── References
    └── Book Notes/
        └── Deep Work.md
```

---

### **🔗 BIDIRECTIONAL LINKING**

  #### **✍️ In the** **Quote File (Quotes/Deep Work - Quote 003 - Focus without distraction.md):**

Use Obisidian's URI to link back to the original Vault.

```
> Focus without distraction is the key to producing great work.

**Source:** [Deep Work](obsidian://open?vault=Notes&file=Deep%2FWork%23%5EQuote003)
```

> [!WARNING]
> Ensure that your values are properly URI encoded. For example, forward slash characters `/` must be encoded as `%2F` and space characters must be encoded as `%20`.

Note it also links to a block by using `%23%5E`.

#### **📖 In the** **Book File (Notes/.../Deep Work.md), format quotes like:**

```
## Quotes

> Focus without distraction is the key to producing great work.
^Quote003

> Clarity about what matters provides clarity about what does not.
^Quote004
```

Each quote has:
- A **stable ID**

### **🧠 BENEFITS TO THIS STRATEGY**

| **Goal**                     | **How it’s Achieved**                                                       |
| ---------------------------- | --------------------------------------------------------------------------- |
| **1. Unique ID**             | Quote 003 is permanent and in both files.                                   |
| **2. Traceability**          | Source file and ID are stored in quote file frontmatter or body.            |
| **3. Bidirectional link**    | Both files have information to link to each other                           |
| **4. Resilient to movement** | If the quote changes position in the book, the ID and file name still link. |

### Sync Automation Tips

If you ever automate updates or syncing:
- **Quote ID** is your stable key.
- A script can match based on frontmatter or filename.

### Front Matter for Notes in Quote Vault

To enable some features, the front matter properties need to include:

- delete: false
- favorite: false

### Objectives for the vault manager script

The Vault Manager will have a few different objectives, but we'll start with just 1.

Objective 1 - Sync Notes:
- For all quotes in the Quote Vault, search to see if any of them have `delete: true`. If they do, then look up the referenced quote, and remove the block quote formatting (`> `) and block ID line, but wrap the text in quotation marks (`"..."`).
- Look for all notes in the Notes Vault which have frontmatter where `sync_quotes: true`
    - Look at all the block quotes, if they don't have a block ID, then this is a new file which needs to be processed.
    - If the file does have ID on at least 1 quote then this is an existing file.
- For existing files:
    - For each blockquote
        - Make sure it has a unique block ID (unique to within that file), counting sequentially from the largest ID in the file (if the largest ID is Quote028 then the next ID should be Quote029).
    - Then go through each blockquote again and look up the corresponding files in the Vault Quote. 
        - If it isn't there, then create it. 
        - If it is there, verify the quote matches. If not, update the Quote Vault with the updated text. The Notes vault is the ground truth. Don't update the YAML section.
    - If there are files in the quote vault that are no longer in the original source file, delete those. 
- For new files:
    - Add block ID to each blockquote. Start with Quote001, then Quote002, ...
    - Create a new file for each blockquote in in the Quote Vault using the naming convention above.
        - The YAML section of the file should be a write-once system.
- Check for orphaned quotes. An orphan is a file in the Quote Vault that has an ID that is longer in the original note.
    - For every file in quote vault, look up the corresponding file in the vault (based on the reference URL) and check if the block ID is there. 
        - If it is, then this file is not an orphan
        - If it isn’t there, it is an orphan and should be deleted. 

Everything is best effort. If the script stops halfway through, it should be written such that the next time the script runs it could just start from the beginning again. No need to pick up from where it last left off or saving state in anyway.

When being run from the command line, a success message should be provided when it completes successfully. If it fails it should say that it failed to look at the logs and show the path to the the logs.

### Error handling

There should be two log files: standard and error logs. 

Each stage of the sync should write out a log message on success. 

If there are failures, details should be written to the error log. These can include:
- Cannot read or write files (e.g., due to permissions)
- Invalid file paths in the config
- Unexpected file content or formatting in source or quote files
- Duplicate block IDs (`^QuoteXXX`) within a single source file

Error messages should be clear about what the issue is and what change is needed to resolve the error. 
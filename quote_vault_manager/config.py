import yaml
import warnings

REQUIRED_KEYS = [
    "source_vault_path",
    "destination_vault_path",
    "std_log_path",
    "err_log_path",
]

CRITICAL_KEYS = [
    "delete",
    "favorite",
    "source_path",
]

class ConfigError(Exception):
    pass

def load_config(path):
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {e}")

    if not isinstance(config, dict):
        raise ConfigError("Config file must be a YAML dictionary.")

    # Check for missing required keys
    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(f"Missing required config keys: {', '.join(missing)}")

    # Check for unexpected keys and warn
    all_keys = set(config.keys())
    expected_keys = set(REQUIRED_KEYS)
    unexpected_keys = all_keys - expected_keys
    
    for key in unexpected_keys:
        if key in CRITICAL_KEYS:
            warnings.warn(f"Critical config key '{key}' found in config file. This may cause issues.", UserWarning)
        else:
            warnings.warn(f"Unexpected config key '{key}' found in config file. This key will be ignored.", UserWarning)

    return config 
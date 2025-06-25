import yaml

REQUIRED_KEYS = [
    "source_vault_path",
    "destination_vault_path",
    "std_log_path",
    "err_log_path",
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

    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(f"Missing required config keys: {', '.join(missing)}")

    return config 
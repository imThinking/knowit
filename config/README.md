# KnowIt Configuration Directory

This directory stores KnowIt configuration files.

## Files

- `config.yaml` - Main configuration file (created by `kv config init`)

## Configuration

Initialize default configuration:
```bash
kv config init
```

Edit configuration manually:
```bash
# Open config.yaml in your default editor
kv config edit
```

View current configuration:
```bash
kv config get <key>
```

Set configuration value:
```bash
kv config set <key> <value>
```

## Configuration Options

See the documentation or run `kv config --help` for available options.

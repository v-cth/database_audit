# Data Warehouse Table Auditor

High-performance data quality checks for data warehouses with security best practices.

## Project Structure

```
database_audit/
├── dw_auditor/                 # Main package
│   ├── __init__.py             # Package exports
│   ├── core/                   # Core auditing logic
│   │   ├── __init__.py
│   │   ├── auditor.py          # Main auditor class
│   │   └── config.py           # Configuration management
│   ├── checks/                 # Data quality checks
│   │   ├── __init__.py
│   │   ├── string_checks.py    # String validation checks
│   │   └── timestamp_checks.py # Timestamp validation checks
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── security.py         # PII masking & security
│   │   └── output.py           # Console output formatting
│   └── exporters/              # Export functionality
│       ├── __init__.py
│       ├── dataframe_export.py # DataFrame export
│       ├── json_export.py      # JSON export
│       └── html_export.py      # HTML report generation
├── main.py                     # Example usage/entry point
├── audit_config.yaml           # Configuration file
└── requirements.txt            # Dependencies
```

## Features

- **Direct Database Auditing**: Query tables directly without exporting files
- **PII Protection**: Automatic masking of sensitive columns
- **Smart Sampling**: Database-native sampling for large tables
- **Multiple Checks**: Trailing spaces, case duplicates, special characters, numeric strings, timestamp patterns
- **Flexible Export**: HTML reports, JSON, CSV, or Polars DataFrames
- **Audit Logging**: Track all audit activities with sanitized connection strings

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from dw_auditor import SecureTableAuditor

auditor = SecureTableAuditor()

# Audit from database
results = auditor.audit_from_database(
    table_name='users',
    connection_string='postgresql://user:pass@localhost:5432/mydb',
    schema='public',
    mask_pii=True
)

# Export results
auditor.export_results_to_html(results, 'report.html')
```

### Using Configuration File

```python
from dw_auditor import AuditConfig, SecureTableAuditor

# Load configuration
config = AuditConfig.from_yaml('audit_config.yaml')

# Create auditor
auditor = SecureTableAuditor(
    sample_size=config.sample_size,
    sample_threshold=config.sample_threshold
)

# Audit tables
for table in config.tables:
    results = auditor.audit_from_database(
        table_name=table,
        connection_string=config.connection_string,
        schema=config.schema,
        mask_pii=config.mask_pii
    )
```

## Modules

### Core (`dw_auditor/core/`)

- **`auditor.py`**: Main `SecureTableAuditor` class that coordinates all auditing
- **`config.py`**: `AuditConfig` class for YAML-based configuration

### Checks (`dw_auditor/checks/`)

- **`string_checks.py`**: String validation (trailing spaces, case duplicates, special chars, numeric strings)
- **`timestamp_checks.py`**: Timestamp validation (constant hour, midnight detection)

### Utils (`dw_auditor/utils/`)

- **`security.py`**: PII masking and connection string sanitization
- **`output.py`**: Console output formatting and summary statistics

### Exporters (`dw_auditor/exporters/`)

- **`dataframe_export.py`**: Export to Polars DataFrame
- **`json_export.py`**: Export to JSON format
- **`html_export.py`**: Generate beautiful HTML reports

## Configuration

See `audit_config.yaml` for a complete configuration example with:
- Database connection settings
- Sampling configuration
- Security settings (PII masking)
- Check enablement/disablement
- Thresholds
- Output formats
- Column filters

## Examples

Run the example file to see usage patterns:

```bash
python main.py
```

## License

MIT

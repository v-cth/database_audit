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

- **Direct Database Auditing**: Query tables directly without exporting files using Ibis
- **Multi-Database Support**: BigQuery and Snowflake (via Ibis framework)
- **PII Protection**: Automatic masking of sensitive columns
- **Smart Sampling**: Database-native sampling for large tables
- **Multiple Checks**: Trailing spaces, case duplicates, special characters, numeric strings, timestamp patterns, date outliers
- **Flexible Export**: HTML reports, JSON, CSV, or Polars DataFrames
- **Audit Logging**: Track all audit activities with sanitized connection strings

## Installation

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install polars ibis-framework[bigquery,snowflake] google-cloud-bigquery snowflake-connector-python pyyaml
```

## Quick Start

### Basic Usage - BigQuery

```python
from dw_auditor import SecureTableAuditor

auditor = SecureTableAuditor()

# Audit from BigQuery
results = auditor.audit_from_database(
    table_name='users',
    backend='bigquery',
    connection_params={
        'project_id': 'my-gcp-project',
        'dataset_id': 'analytics',
        'credentials_path': '/path/to/service-account-key.json'
    },
    mask_pii=True
)

# Export results
auditor.export_results_to_html(results, 'report.html')
```

### Basic Usage - Snowflake

```python
from dw_auditor import SecureTableAuditor

auditor = SecureTableAuditor()

# Audit from Snowflake
results = auditor.audit_from_database(
    table_name='CUSTOMERS',
    backend='snowflake',
    connection_params={
        'account': 'my-account',
        'user': 'my-user',
        'password': 'my-password',
        'database': 'ANALYTICS_DB',
        'warehouse': 'COMPUTE_WH',
        'schema': 'PUBLIC'
    },
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
        backend=config.backend,
        connection_params=config.connection_params,
        schema=config.schema,
        mask_pii=config.mask_pii,
        custom_pii_keywords=config.custom_pii_keywords
    )
```

See `audit_config.yaml` for the main configuration template and `audit_config_examples.yaml` for detailed examples for both BigQuery and Snowflake.

## Modules

### Core (`dw_auditor/core/`)

- **`auditor.py`**: Main `SecureTableAuditor` class that coordinates all auditing
- **`config.py`**: `AuditConfig` class for YAML-based configuration
- **`database.py`**: `DatabaseConnection` class for Ibis-based database connections (BigQuery, Snowflake)

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
- Database connection settings (backend + connection_params)
  - BigQuery: project_id, dataset_id, credentials_path
  - Snowflake: account, user, password, database, warehouse, schema
- Sampling configuration
- Security settings (PII masking)
- Check enablement/disablement
- Thresholds
- Output formats
- Column filters

For detailed examples, see `audit_config_examples.yaml` which includes:
- BigQuery with service account authentication
- BigQuery with Application Default Credentials
- Snowflake with basic authentication
- Custom queries for both databases
- Production configurations
- Minimal configurations

## Supported Databases

The auditor uses **Ibis** as the database abstraction layer, currently supporting:

- **BigQuery** (Google Cloud)
  - Service account authentication
  - Application Default Credentials
  - Dataset-level access control

- **Snowflake**
  - User/password authentication
  - Role-based access control
  - Warehouse and database selection

## Examples

Run the example file to see usage patterns:

```bash
python main.py
```

For configuration examples:
- `audit_config.yaml` - Main configuration template
- `audit_config_examples.yaml` - Complete examples for BigQuery and Snowflake

## License

MIT

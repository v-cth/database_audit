# Migration Guide: ConnectorX to Ibis

This guide helps you migrate from the old ConnectorX-based implementation to the new Ibis-based implementation.

## What Changed?

The auditor now uses **Ibis** instead of **ConnectorX** for database connections, with support for:
- **BigQuery** (Google Cloud Platform)
- **Snowflake**

## Key Changes

### 1. Connection Method

**Old (ConnectorX):**
```python
results = auditor.audit_from_database(
    table_name='users',
    connection_string='postgresql://user:pass@localhost:5432/mydb',
    schema='public'
)
```

**New (Ibis):**
```python
# BigQuery
results = auditor.audit_from_database(
    table_name='users',
    backend='bigquery',
    connection_params={
        'project_id': 'my-project',
        'dataset_id': 'analytics',
        'credentials_path': '/path/to/credentials.json'
    }
)

# Snowflake
results = auditor.audit_from_database(
    table_name='USERS',
    backend='snowflake',
    connection_params={
        'account': 'my-account',
        'user': 'my-user',
        'password': 'my-password',
        'database': 'MY_DB',
        'warehouse': 'MY_WH',
        'schema': 'PUBLIC'
    }
)
```

### 2. Configuration File

**Old YAML:**
```yaml
database:
  connection_string: "postgresql://user:pass@localhost/db"
  schema: "public"
```

**New YAML:**
```yaml
database:
  backend: "bigquery"
  connection_params:
    project_id: "my-project"
    dataset_id: "my_dataset"
    credentials_path: "/path/to/credentials.json"
  schema: null
```

### 3. Configuration Loading

**Old:**
```python
config = AuditConfig.from_yaml('audit_config.yaml')
results = auditor.audit_from_database(
    table_name=table,
    connection_string=config.connection_string,
    schema=config.schema
)
```

**New:**
```python
config = AuditConfig.from_yaml('audit_config.yaml')
results = auditor.audit_from_database(
    table_name=table,
    backend=config.backend,
    connection_params=config.connection_params,
    schema=config.schema
)
```

## Migration Steps

### Step 1: Update Dependencies

```bash
# Uninstall old dependencies (optional)
pip uninstall connectorx

# Install new dependencies
pip install -r requirements.txt
```

### Step 2: Update Configuration Files

Edit your `audit_config.yaml`:

**For BigQuery:**
```yaml
database:
  backend: "bigquery"
  connection_params:
    project_id: "your-gcp-project"
    dataset_id: "your_dataset"
    credentials_path: "/path/to/service-account-key.json"
  schema: null
```

**For Snowflake:**
```yaml
database:
  backend: "snowflake"
  connection_params:
    account: "your-account"
    user: "your-user"
    password: "your-password"
    database: "YOUR_DATABASE"
    warehouse: "YOUR_WAREHOUSE"
    schema: "YOUR_SCHEMA"
  schema: null
```

### Step 3: Update Your Code

Update any direct `audit_from_database()` calls:

```python
# Old
auditor.audit_from_database(
    table_name='users',
    connection_string='postgresql://...',
    schema='public'
)

# New (BigQuery)
auditor.audit_from_database(
    table_name='users',
    backend='bigquery',
    connection_params={
        'project_id': 'my-project',
        'dataset_id': 'analytics'
    }
)

# New (Snowflake)
auditor.audit_from_database(
    table_name='USERS',
    backend='snowflake',
    connection_params={
        'account': 'my-account',
        'user': 'my-user',
        'password': 'my-password',
        'database': 'MY_DB',
        'warehouse': 'MY_WH'
    }
)
```

## BigQuery Authentication

### Service Account (Recommended for Production)

```python
connection_params = {
    'project_id': 'my-project',
    'dataset_id': 'analytics',
    'credentials_path': '/path/to/service-account-key.json'
}
```

### Application Default Credentials (ADC)

```python
# No credentials_path needed - uses gcloud auth or GOOGLE_APPLICATION_CREDENTIALS
connection_params = {
    'project_id': 'my-project',
    'dataset_id': 'analytics'
}
```

### Credentials as JSON

```python
import json

with open('/path/to/credentials.json') as f:
    creds = json.load(f)

connection_params = {
    'project_id': 'my-project',
    'dataset_id': 'analytics',
    'credentials_json': creds
}
```

## Snowflake Authentication

### Basic Username/Password

```python
connection_params = {
    'account': 'my-account',
    'user': 'my-user',
    'password': 'my-password',
    'database': 'MY_DB',
    'warehouse': 'MY_WH',
    'schema': 'PUBLIC',  # Optional
    'role': 'MY_ROLE'    # Optional
}
```

## Breaking Changes

1. **No longer supported databases:**
   - PostgreSQL
   - MySQL
   - SQLite
   - SQL Server
   - Oracle

2. **`connection_string` parameter removed:**
   - Use `backend` + `connection_params` instead

3. **Config structure changed:**
   - `database.connection_string` → `database.backend` + `database.connection_params`

## Benefits of Ibis

1. **Unified API**: Same interface for BigQuery and Snowflake
2. **Lazy Evaluation**: Optimized query execution
3. **Type Safety**: Better type handling across databases
4. **Modern**: Active development and community support
5. **Extensible**: Easy to add more database backends in the future

## Need Help?

- Check `audit_config_examples.yaml` for complete configuration examples
- Run `python main.py` to see usage examples
- See README.md for detailed documentation

## Rollback

If you need to rollback to the old version:

```bash
git checkout <previous-commit>
pip install connectorx
```

The old version used ConnectorX with direct connection strings.

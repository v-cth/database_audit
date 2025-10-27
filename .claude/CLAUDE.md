# Data Warehouse Table Auditor - Claude Code Guide

## Project Overview

A high-performance data warehouse auditing tool that performs data quality checks and profiling on BigQuery and Snowflake tables using Ibis for secure, direct database access without file exports.

**Primary Language**: Python 3.10+
**Key Framework**: Ibis (database abstraction)
**Main Use Case**: Audit data warehouse tables for quality issues and generate insights

## Quick Start for Claude

### Running the Auditor
```bash
source audit_env/bin/activate && python audit.py                    # Use default audit_config.yaml
source audit_env/bin/activate && python audit.py custom_config.yaml # Use custom config
source audit_env/bin/activate && python audit.py --discover          # Discovery mode (metadata only)
```

### Key Entry Points
- **`audit.py`**: Main CLI script - starts here for user-facing audits
- **`dw_auditor/core/auditor.py`**: `SecureTableAuditor` class - core audit logic
- **`dw_auditor/exporters/html/`**: HTML report generation (modular package with 5 files)

### Recent Development Focus

**Completed** (October 2025):
1. ✅ **Class-based check framework** (926 lines → 11 modular classes with registry)
2. ✅ Modularized HTML export (1,558 lines → 5 focused modules)
3. ✅ Minimalist redesign: 4-tab structure, no emojis, cleaner UI
4. ✅ Visual distribution ranges for numeric columns (gradient bars)
5. ✅ Visual timeline bars for date ranges
6. ✅ Configurable number formatting (thousand separator + decimal places)

## Architecture Philosophy

### Core Principles
1. **Security First**: Never export data to files; PII masking; secure connection handling
2. **Database-Native Operations**: Push computation to the database (Ibis expressions)
3. **Separation of Concerns**:
   - Quality checks (`checks/`) are separate from profiling (`insights/`)
   - Exporters (`exporters/`) are modular and independent
4. **Configuration-Driven**: YAML config controls all behavior
5. **Visual-First Reporting**: HTML reports use inline CSS and visual elements (no external dependencies)

### Data Flow
```
audit.py
  → AuditConfig.from_yaml()
  → SecureTableAuditor
    → DatabaseConnection (Ibis)
      → Query execution (database-native sampling)
      → Check Framework (NEW - class-based with registry)
        → run_check_sync() → BaseCheck subclasses → CheckResult
      → Insights (numeric_insights, datetime_insights, string_insights)
    → ExporterMixin
      → HTML/JSON/CSV exports
```

## Key Conventions

### File Organization
- **`core/`**: Fundamental classes (auditor, config, database connection, **base_check, registry, runner**)
- **`checks/`**: Data quality check classes (class-based, auto-registered)
- **`insights/`**: Data profiling and statistics functions
- **`exporters/`**: Output format generators (HTML, JSON, CSV)
- **`utils/`**: Helper functions (security, output formatting)

### Naming Patterns
- **Functions**: `snake_case` (e.g., `get_column_insights`)
- **Classes**: `PascalCase` (e.g., `SecureTableAuditor`)
- **Private functions**: Prefix with `_` (e.g., `_render_numeric_insights`)
- **Config keys**: `snake_case` in YAML (e.g., `thousand_separator`)

### Code Style
- **Type hints**: Used throughout for function signatures
- **Docstrings**: Google style with Args/Returns sections
- **Imports**: Grouped (stdlib, third-party, local) with blank lines between
- **HTML generation**: f-strings with triple-quoted strings for readability

### HTML Report Conventions
- **Minimalist design**: Clean typography, no emojis, Inter font
- **Four-tab structure**: Summary → Insights → Quality Checks → Metadata
- **Inline CSS**: All styles inline (no external files for portability)
- **Color palette**:
  - Purple (`#6606dc`): Primary accent
  - Green (`#10b981`): Success/high frequency
  - Orange (`#f59e0b`): Mean/average markers
  - Red (`#ef4444`): Errors/issues
  - Gray (`#4b5563`, `#1f2937`): Text and labels
- **Visual elements**: CSS gradients and absolute positioning for charts

## Check Framework Architecture (NEW - October 27, 2025)

### Overview
The data quality check system has been refactored from procedural functions (926 lines in 4 files) to a **class-based, extensible framework** with:
- **Dynamic registry** with decorator-based auto-registration
- **Abstract base class** (BaseCheck) enforcing unified interface
- **Pydantic validation** for type-safe parameter handling
- **Async-ready** infrastructure for future concurrent execution
- **11 modular check classes** in individual files

### Core Components

#### 1. BaseCheck Abstract Class (`core/base_check.py`)
Foundation for all check classes with:
- Unified interface: `__init__()`, `_validate_params()`, `run()`
- Shared helper methods: `_get_non_null_df()`, `_get_examples()`, `_format_example_with_pk()`, `_calculate_percentage()`
- CheckResult Pydantic model for structured output

```python
from dw_auditor.core.base_check import BaseCheck, CheckResult

class MyCheck(BaseCheck):
    display_name = "My Custom Check"

    def _validate_params(self) -> None:
        # Validate parameters with Pydantic
        self.config = MyCheckParams(**self.params)

    async def run(self) -> List[CheckResult]:
        # Execute check logic
        results = []
        # ... perform checks ...
        return results
```

#### 2. Dynamic Registry (`core/registry.py`)
Auto-registration system using decorators:
- `CHECK_REGISTRY`: Dict mapping check names to classes
- `@register_check(name)`: Decorator to register classes
- `get_check(name)`: Retrieve check class by name
- `list_checks()`: List all registered checks
- `check_exists(name)`: Verify check availability

```python
from dw_auditor.core.registry import register_check

@register_check("my_check")
class MyCheck(BaseCheck):
    # Class automatically registered on import
    pass
```

#### 3. Runner API (`core/runner.py`)
Execution interface for running checks:
- `run_check()`: Async execution
- `run_check_sync()`: Synchronous wrapper
- `run_multiple_checks()`: Batch execution
- `validate_check_config()`: Parameter validation

```python
from dw_auditor.checks import run_check_sync

# Run a check
results = run_check_sync('numeric_range', df, 'age', ['user_id'], greater_than=0, less_than=150)
# Returns List[CheckResult] - Pydantic models
```

### Available Checks

#### String Checks (5)
1. **`trailing_characters`** (`string_trailing_check.py`): Detect leading/trailing whitespace or patterns
2. **`ending_characters`** (`string_ending_check.py`): Find strings ending with specific characters
3. **`case_duplicates`** (`string_case_check.py`): Identify case-insensitive duplicates
4. **`regex_pattern`** (`string_regex_check.py`): Validate against regex (contains/match modes)
5. **`numeric_strings`** (`string_numeric_check.py`): Detect string columns with only numbers

#### Timestamp Checks (4)
1. **`timestamp_patterns`** (`timestamp_pattern_check.py`): Find constant hours or midnight timestamps
2. **`date_range`** (`date_range_check.py`): Validate dates within boundaries (after/before)
3. **`date_outliers`** (`date_outlier_check.py`): Detect unusually old/future dates or suspicious years
4. **`future_dates`** (`date_future_check.py`): Find dates in the future relative to now

#### Numeric Checks (1)
1. **`numeric_range`** (`numeric_range_check.py`): Validate numeric values within boundaries

#### Universal Checks (1)
1. **`uniqueness`** (`uniqueness_check.py`): Check for duplicate values (works on all types)

### Usage in Auditor

The `SecureTableAuditor._audit_column()` method calls checks via the registry:

```python
# Old (procedural):
issues = check_trailing_characters(df, col, primary_key_columns)

# New (class-based):
results = run_check_sync('trailing_characters', df, col, primary_key_columns)
issues = [r.model_dump() for r in results]  # Convert Pydantic models to dicts
```

### Adding a New Check

1. **Create check file** in `dw_auditor/checks/my_check.py`:
```python
from pydantic import BaseModel, Field
from typing import List
from ..core.base_check import BaseCheck, CheckResult
from ..core.registry import register_check
import polars as pl

class MyCheckParams(BaseModel):
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)

@register_check("my_check")
class MyCheck(BaseCheck):
    display_name = "My Check"

    def _validate_params(self) -> None:
        self.config = MyCheckParams(**self.params)

    async def run(self) -> List[CheckResult]:
        results = []
        # Check logic here
        return results
```

2. **Import in `checks/__init__.py`** to trigger registration:
```python
from . import my_check
```

3. **Use in auditor or config**:
```python
results = run_check_sync('my_check', df, col, pk_cols, threshold=0.9)
```

### Benefits of New Architecture
- ✅ **Extensible**: Add checks without modifying core code
- ✅ **Type-safe**: Pydantic validates parameters at runtime
- ✅ **Testable**: Each check is isolated and independently testable
- ✅ **Self-documenting**: Check names in registry, docstrings in classes
- ✅ **Async-ready**: Infrastructure supports future concurrency
- ✅ **Modular**: One check per file, single responsibility

## Configuration (`audit_config.yaml`)

### Most Important Sections
1. **`version`, `project`, `description`, `last_modified`**: Optional audit metadata (displayed in Metadata tab)
2. **`database`**: Connection settings (backend, project_id, dataset_id)
3. **`tables`**: Tables to audit (with optional primary keys, custom queries, and per-table schemas)
4. **`column_insights`**: Profiling configuration per data type
5. **`output.number_format`**: Display formatting (thousand_separator, decimal_places)

### Audit Metadata (Top-level, Optional)
Descriptive fields that appear in the HTML report Metadata tab:
- `version`: Config version number (e.g., 1, 2.0)
- `project`: Project name (e.g., "Customer Data Quality Audit")
- `description`: Brief description of what this audit configuration does
- `last_modified`: Last update date (e.g., "2025-10-24")

### Per-Table Configuration
Tables can have individual settings that override global defaults:
- `primary_key`: Column(s) to use as primary key for context in error messages
- `query`: Custom SQL query to audit (instead of SELECT *)
- `schema`: Override dataset/schema for this specific table (allows auditing across multiple datasets)

### Config Access Pattern
```python
config = AuditConfig.from_yaml("audit_config.yaml")
config.sample_size           # Sampling configuration
config.output_dir            # Where to save results
config.column_insights       # Profiling settings
```

## Common Development Tasks

### Adding a New Visual Element to HTML Reports

1. **Find the renderer function** in `dw_auditor/exporters/html/insights.py`:
   - Numeric: `_render_numeric_insights()`
   - DateTime: `_render_datetime_insights()`
   - String: `_render_string_insights()`

2. **Add HTML with inline CSS**:
   ```python
   html += f"""
       <div style="position: relative; height: 50px;">
           <div style="position: absolute; top: 20px; left: {position}%; ...">
               {content}
           </div>
       </div>
   """
   ```

3. **Pass config parameters** through the function chain:
   - Renderer → `_generate_column_insights()` → `export_to_html()` in `export.py`

### Adding a New Configuration Option

1. **Update `audit_config.yaml`** with the new setting and comments
2. **Update `dw_auditor/core/config.py`** if needed (for complex validation)
3. **Pass through** the relevant function chain
4. **Document** in config comments and examples

### Testing the HTML Output

```bash
# Run audit to generate HTML
python audit.py

# HTML files generated in:
# audit_results/audit_run_TIMESTAMP/TABLE_NAME/audit.html
# audit_results/audit_run_TIMESTAMP/summary.html
```

## Tech Stack

### Core Dependencies
- **Ibis**: Database abstraction layer (SQL generation)
- **Polars**: High-performance DataFrames (used post-query)
- **PyYAML**: Configuration parsing
- **google-cloud-bigquery**: BigQuery backend (via Ibis)
- **snowflake-connector-python**: Snowflake backend (via Ibis)

### Why Ibis?
- Lazy evaluation: Builds SQL expressions without executing
- Database-native sampling: `TABLESAMPLE` in BigQuery, `SAMPLE` in Snowflake
- Type safety: Strong typing prevents SQL injection
- No data export: Queries run in database, results stream directly

### Why Polars (not Pandas)?
- Faster for large datasets
- Better memory efficiency
- Expressive API for transformations
- Native Arrow format

## Known Gotchas

### HTML Report Generation
1. **Label overlap**: Use vertical stacking (`v_offset`) when labels cluster
2. **Long numbers**: Always use `format_number()` helper for thousand separators
3. **Container overflow**: Set `overflow: hidden` on positioned containers
4. **Gradient colors**: Use 5+ stops for smooth visual transitions

### Ibis Queries
1. **Lazy evaluation**: Must call `.execute()` or `.to_polars()` to run query
2. **Type conversions**: Some Ibis types differ from Polars types (check schema)
3. **Sampling**: Use `sample(fraction=)` not `limit()` for statistical validity

### Config Management
1. **Nested dicts**: Access with `.get()` chains or use getattr patterns
2. **Default values**: Always provide defaults in function signatures
3. **Type safety**: Config values are raw Python types, not validated objects

## Recent Changes (October 2025)

### October 27: Class-Based Check Framework
- **Major refactoring**: 926 lines of procedural code → 11 modular check classes
- **New architecture**: Abstract BaseCheck + dynamic registry + async-ready runner
- **Core files**:
  - `core/base_check.py`: Abstract base class with shared helpers (180 lines)
  - `core/registry.py`: Dynamic registration with `@register_check` decorator (110 lines)
  - `core/runner.py`: Execution API with sync/async support (170 lines)
- **11 check classes**: Each in individual file (~70-130 lines each)
  - String checks: trailing_characters, ending_characters, case_duplicates, regex_pattern, numeric_strings
  - Timestamp checks: timestamp_patterns, date_range, date_outliers, future_dates
  - Numeric checks: numeric_range
  - Universal checks: uniqueness
- **Pydantic validation**: Type-safe parameter handling with validators
- **Updated auditor.py**: Now uses `run_check_sync()` API (~15 call sites updated)
- **Benefits**: Extensible, testable, self-documenting, async-ready

### October 23: Modularization & Minimalist Redesign
- **Refactored HTML export**: Split 1,558-line file into 5 focused modules
- **New structure**: `html/` package with `export.py`, `structure.py`, `insights.py`, `checks.py`, `assets.py`
- **Minimalist design**: Removed all emojis, cleaner UI, professional typography
- **Four tabs**: Summary (with column summary) → Insights → Quality Checks → Metadata
- **Layout refinements**: Duration moved to Metadata tab

### October 19-21: Visual Enhancements
- Visual gradient bars for numeric distributions (min/max/Q1/Q2/Q3/mean)
- Timeline bars for date ranges with duration badges
- Configurable number formatting (thousand separator, decimal places)
- Smart label combining and vertical stacking to prevent overlap

## Getting Help

### Understanding Existing Code
1. **Start with `audit.py`**: Follow the execution path from CLI
2. **Check docstrings**: All major functions have detailed docstrings
3. **Look at config**: `audit_config.yaml` shows all available options
4. **Run with example**: Use the BigQuery public crypto dataset (already configured)

### Making Changes
1. **Run existing audit first**: See current behavior
2. **Make small changes**: Test incrementally
3. **Check HTML output**: Visual bugs are easy to spot in browser
4. **Update config docs**: Keep YAML comments in sync with code

---

**Last Updated**: October 27, 2025
**Maintained for**: Claude Code (AI pair programming assistant)

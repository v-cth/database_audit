#!/usr/bin/env python
"""
Simple CLI for running database audits
Usage: python audit.py [config_file]
"""

import sys
from pathlib import Path
from dw_auditor import AuditConfig, SecureTableAuditor


def main():
    # Default config file
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'audit_config.yaml'

    if not Path(config_file).exists():
        print(f"❌ Config file not found: {config_file}")
        print(f"Usage: python audit.py [config_file]")
        sys.exit(1)

    # Load config
    print(f"📋 Loading config from: {config_file}")
    config = AuditConfig.from_yaml(config_file)

    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Create auditor
    auditor = SecureTableAuditor(
        sample_size=config.sample_size,
        sample_threshold=config.sample_threshold,
        min_year=config.min_year,
        max_year=config.max_year,
        outlier_threshold_pct=config.outlier_threshold_pct
    )

    # Audit tables
    for table in config.tables:
        print(f"\n{'='*70}")
        print(f"🔍 Auditing table: {table}")
        print(f"{'='*70}")

        try:
            results = auditor.audit_from_database(
                table_name=table,
                backend=config.backend,
                connection_params=config.connection_params,
                schema=config.schema,
                mask_pii=config.mask_pii,
                custom_pii_keywords=config.custom_pii_keywords
            )

            # Export results
            if 'html' in config.export_formats:
                output_file = config.output_dir / f'{config.file_prefix}_{table}.html'
                auditor.export_results_to_html(results, str(output_file))

            if 'json' in config.export_formats:
                output_file = config.output_dir / f'{config.file_prefix}_{table}.json'
                auditor.export_results_to_json(results, str(output_file))

            if 'csv' in config.export_formats:
                output_file = config.output_dir / f'{config.file_prefix}_{table}.csv'
                df = auditor.export_results_to_dataframe(results)
                df.write_csv(str(output_file))
                print(f"📄 CSV saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error auditing table '{table}': {e}")
            continue

    print(f"\n{'='*70}")
    print(f"✅ Audit completed! Results saved to: {config.output_dir}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

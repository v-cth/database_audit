"""
Output and display utilities for audit results
"""

from typing import Dict


def print_results(results: Dict):
    """Pretty print audit results"""
    has_issues = any(col_data['issues'] for col_data in results['columns'].values())

    if not has_issues:
        print("✅ No issues found!\n")
        return

    print("🔍 Issues Found:\n")

    for col_name, col_data in results['columns'].items():
        if not col_data['issues']:
            continue

        print(f"📊 Column: {col_name} ({col_data['dtype']})")
        if col_data['null_count'] > 0:
            print(f"   Nulls: {col_data['null_count']:,} ({col_data['null_pct']:.1f}%)")

        for issue in col_data['issues']:
            issue_type = issue['type']

            if issue_type == 'TRAILING_SPACES':
                print(f"   ⚠️  TRAILING SPACES: {issue['count']:,} rows ({issue['pct']:.1f}%)")
                print(f"      Examples: {issue['examples']}")

            elif issue_type == 'LEADING_SPACES':
                print(f"   ⚠️  LEADING SPACES: {issue['count']:,} rows ({issue['pct']:.1f}%)")
                print(f"      Examples: {issue['examples'][:3]}")

            elif issue_type == 'CASE_DUPLICATES':
                print(f"   ⚠️  CASE DUPLICATES: {issue['count']} unique values with case variations")
                for lower_val, variations in issue['examples']:
                    print(f"      '{lower_val}' → {variations}")

            elif issue_type == 'SPECIAL_CHARACTERS':
                print(f"   ⚠️  SPECIAL CHARS: {issue['count']:,} rows ({issue['pct']:.1f}%)")
                print(f"      Found chars: {issue['special_chars']}")
                print(f"      Examples: {issue['examples'][:2]}")

            elif issue_type == 'NUMERIC_STRINGS':
                print(f"   ⚠️  NUMERIC STRINGS: {issue['count']:,} rows ({issue['pct']:.1f}%)")
                print(f"      💡 {issue['suggestion']}")
                print(f"      Examples: {issue['examples']}")

            elif issue_type == 'CONSTANT_HOUR':
                print(f"   ⚠️  CONSTANT HOUR: {issue['pct']:.1f}% at hour {issue['hour']}")
                print(f"      💡 {issue['suggestion']}")

            elif issue_type == 'ALWAYS_MIDNIGHT':
                print(f"   ⚠️  ALWAYS MIDNIGHT: {issue['pct']:.1f}% of timestamps")
                print(f"      💡 {issue['suggestion']}")

        print()


def get_summary_stats(results: Dict) -> Dict:
    """
    Get high-level summary statistics from audit results

    Args:
        results: Audit results dictionary

    Returns:
        Dictionary with summary statistics
    """
    total_issues = sum(len(col_data['issues']) for col_data in results['columns'].values())
    columns_with_issues = len(results['columns'])

    issue_types = {}
    for col_data in results['columns'].values():
        for issue in col_data['issues']:
            issue_type = issue['type']
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    return {
        'table_name': results['table_name'],
        'total_rows': results['total_rows'],
        'analyzed_rows': results['analyzed_rows'],
        'sampled': results['sampled'],
        'total_issues': total_issues,
        'columns_with_issues': columns_with_issues,
        'issue_breakdown': issue_types,
        'timestamp': results.get('timestamp', '')
    }

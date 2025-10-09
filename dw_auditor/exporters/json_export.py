"""
Export audit results to JSON format
"""

import json
from typing import Dict, Optional


def export_to_json(results: Dict, file_path: Optional[str] = None) -> str:
    """
    Export audit results to JSON

    Args:
        results: Audit results dictionary
        file_path: Optional path to save JSON file

    Returns:
        JSON string
    """
    json_str = json.dumps(results, indent=2, default=str)

    if file_path:
        with open(file_path, 'w') as f:
            f.write(json_str)
        print(f"📄 Results saved to: {file_path}")

    return json_str

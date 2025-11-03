"""
HTML generation for table relationship visualizations
"""

from typing import List, Dict, Optional, Tuple, Set
import json
import math


def _get_table_columns_for_diagram(table_name: str, relationships: List[Dict], tables_metadata: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Extract columns to display in ER diagram for a table

    Args:
        table_name: Name of the table
        relationships: All relationships
        tables_metadata: Table metadata with primary key info

    Returns:
        Dict with 'pk', 'fk', and 'other' column lists
    """
    # Get primary key columns from metadata
    table_meta = tables_metadata.get(table_name, {})
    pk_columns = table_meta.get('primary_key_columns', [])
    if isinstance(pk_columns, str):
        pk_columns = [pk_columns]

    # Get foreign key columns (columns involved in relationships)
    fk_columns = set()
    for rel in relationships:
        if rel['table1'] == table_name:
            fk_columns.add(rel['column1'])
        elif rel['table2'] == table_name:
            fk_columns.add(rel['column2'])

    # Remove PKs from FK list (they'll be shown as PK)
    fk_columns = fk_columns - set(pk_columns)

    return {
        'pk': pk_columns,
        'fk': sorted(fk_columns),
        'other': []  # Don't show other columns for now to keep diagram clean
    }


def _calculate_table_positions(tables: List[str], num_cols: int = 3) -> Dict[str, Tuple[int, int]]:
    """
    Calculate grid positions for tables

    Args:
        tables: List of table names
        num_cols: Number of columns in grid

    Returns:
        Dict mapping table name to (x, y) position
    """
    positions = {}
    table_width = 280
    table_height = 200
    h_spacing = 150
    v_spacing = 100

    for idx, table in enumerate(tables):
        col = idx % num_cols
        row = idx // num_cols
        x = 50 + col * (table_width + h_spacing)
        y = 50 + row * (table_height + v_spacing)
        positions[table] = (x, y)

    return positions


def _get_crow_foot_path(relationship_type: str, direction: str, is_start: bool) -> str:
    """
    Generate SVG path for crow's foot notation

    Args:
        relationship_type: Type of relationship (one-to-one, many-to-one, many-to-many)
        direction: Direction of relationship
        is_start: Whether this is the start or end of the line

    Returns:
        SVG path string for the crow's foot symbol
    """
    # Determine cardinality at this end
    if relationship_type == "one-to-one":
        cardinality = "one"
    elif relationship_type == "many-to-one":
        if direction == "table1_to_table2":
            cardinality = "many" if is_start else "one"
        elif direction == "table2_to_table1":
            cardinality = "one" if is_start else "many"
        else:
            cardinality = "one"
    elif relationship_type == "many-to-many":
        cardinality = "many"
    else:
        cardinality = "one"

    if cardinality == "one":
        # Perpendicular line for "one" side
        return "M -10,0 L 10,0 M 0,-10 L 0,10"
    else:
        # Crow's foot for "many" side (three prongs)
        return "M -10,-10 L 0,0 L -10,10 M 0,-10 L 0,10"


def generate_relationships_summary_section(relationships: List[Dict], tables_metadata: Dict[str, Dict], min_confidence: float = 0.5) -> str:
    """
    Generate ER diagram with crow's foot notation for summary.html

    Args:
        relationships: List of relationship dictionaries
        tables_metadata: Metadata about tables (row counts, column counts, primary keys)
        min_confidence: Minimum confidence to display

    Returns:
        HTML string with relationship section including interactive ER diagram
    """
    # Filter relationships by minimum display confidence
    display_relationships = [r for r in relationships if r['confidence'] >= min_confidence]

    if not display_relationships:
        return ""

    # Sort by confidence descending
    display_relationships.sort(key=lambda x: x['confidence'], reverse=True)

    # Get tables involved in relationships
    tables_in_relationships = set()
    for rel in display_relationships:
        tables_in_relationships.add(rel['table1'])
        tables_in_relationships.add(rel['table2'])

    tables_list = sorted(tables_in_relationships)

    # Calculate table positions
    positions = _calculate_table_positions(tables_list, num_cols=3)

    # Calculate SVG canvas size
    max_x = max(pos[0] for pos in positions.values()) + 300
    max_y = max(pos[1] for pos in positions.values()) + 250

    # Build table boxes SVG
    table_boxes_svg = ""
    for table_name in tables_list:
        x, y = positions[table_name]
        columns = _get_table_columns_for_diagram(table_name, display_relationships, tables_metadata)

        # Get metadata
        metadata = tables_metadata.get(table_name, {})
        row_count = metadata.get('total_rows', 'N/A')
        if isinstance(row_count, int):
            row_count_str = f"{row_count:,}"
        else:
            row_count_str = str(row_count)

        # Calculate box height based on number of columns
        total_columns = len(columns['pk']) + len(columns['fk'])
        box_height = 60 + (total_columns * 22)  # Header + columns

        # Create table box
        table_boxes_svg += f"""
        <g class="er-table" data-table="{table_name}">
            <rect x="{x}" y="{y}" width="280" height="{box_height}"
                  fill="white" stroke="#d1d5db" stroke-width="1.5" rx="6"/>
            <rect x="{x}" y="{y}" width="280" height="40"
                  fill="#6606dc" rx="6"/>
            <rect x="{x}" y="{y + 40}" width="280" height="{box_height - 40}"
                  fill="white" rx="0"/>
            <text x="{x + 140}" y="{y + 25}"
                  font-family="Inter, sans-serif" font-size="14" font-weight="600"
                  fill="white" text-anchor="middle">{table_name}</text>
            <text x="{x + 140}" y="{y + 36}"
                  font-family="Inter, sans-serif" font-size="10"
                  fill="rgba(255,255,255,0.8)" text-anchor="middle">{row_count_str} rows</text>
        """

        # Add columns
        y_offset = y + 58
        for pk_col in columns['pk']:
            table_boxes_svg += f"""
            <text x="{x + 10}" y="{y_offset}"
                  font-family="'Courier New', monospace" font-size="12" font-weight="bold"
                  fill="#1f2937">🔑 {pk_col}</text>
        """
            y_offset += 22

        for fk_col in columns['fk']:
            table_boxes_svg += f"""
            <text x="{x + 10}" y="{y_offset}"
                  font-family="'Courier New', monospace" font-size="12"
                  fill="#4b5563">{fk_col}</text>
        """
            y_offset += 22

        table_boxes_svg += "</g>"

    # Group relationships by table pair to handle multiple relationships between same tables
    from collections import defaultdict
    table_pair_rels = defaultdict(list)
    for rel in display_relationships:
        # Create consistent key for table pair (always sort to avoid duplicates)
        pair_key = tuple(sorted([rel['table1'], rel['table2']]))
        table_pair_rels[pair_key].append(rel)

    # Build relationship lines with crow's foot notation
    relationship_lines_svg = ""
    rel_idx = 0
    for pair_key, rels in table_pair_rels.items():
        table1, table2 = pair_key

        if table1 not in positions or table2 not in positions:
            continue

        x1, y1 = positions[table1]
        x2, y2 = positions[table2]

        # Calculate center points of table boxes
        center_x1 = x1 + 140
        center_y1 = y1 + 100
        center_x2 = x2 + 140
        center_y2 = y2 + 100

        # Calculate edge connection points (sides of boxes)
        dx = center_x2 - center_x1
        dy = center_y2 - center_y1

        # Determine base connection points
        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0:
                base_start_x, base_start_y = x1 + 280, center_y1
                base_end_x, base_end_y = x2, center_y2
            else:
                base_start_x, base_start_y = x1, center_y1
                base_end_x, base_end_y = x2 + 280, center_y2
            offset_axis = 'vertical'  # Offset vertically for horizontal lines
        else:
            # Vertical connection
            if dy > 0:
                base_start_x, base_start_y = center_x1, y1 + 150
                base_end_x, base_end_y = center_x2, y2
            else:
                base_start_x, base_start_y = center_x1, y1
                base_end_x, base_end_y = center_x2, y2 + 150
            offset_axis = 'horizontal'  # Offset horizontally for vertical lines

        # Draw each relationship with offset if multiple
        num_rels = len(rels)
        for i, rel in enumerate(rels):
            # Calculate offset for multiple relationships
            if num_rels > 1:
                # Spread relationships evenly with 25px spacing
                offset = (i - (num_rels - 1) / 2) * 25
            else:
                offset = 0

            # Apply offset
            if offset_axis == 'vertical':
                start_x, start_y = base_start_x, base_start_y + offset
                end_x, end_y = base_end_x, base_end_y + offset
            else:
                start_x, start_y = base_start_x + offset, base_start_y
                end_x, end_y = base_end_x + offset, base_end_y

            # Line color based on confidence
            confidence = rel['confidence']
            if confidence >= 0.9:
                line_color = "#6606dc"
                line_width = 2.5
            elif confidence >= 0.7:
                line_color = "#9ca3af"
                line_width = 2
            else:
                line_color = "#d1d5db"
                line_width = 1.5

            # Calculate angle for crow's foot rotation
            angle_start = math.atan2(end_y - start_y, end_x - start_x) * 180 / math.pi
            angle_end = math.atan2(start_y - end_y, start_x - end_x) * 180 / math.pi

            # Get crow's foot paths
            crow_foot_start = _get_crow_foot_path(rel['relationship_type'], rel.get('direction', 'bidirectional'), True)
            crow_foot_end = _get_crow_foot_path(rel['relationship_type'], rel.get('direction', 'bidirectional'), False)

            # Build tooltip text
            tooltip_text = f"{rel['column1']} ↔ {rel['column2']}&#10;Confidence: {confidence:.1%}&#10;Type: {rel['relationship_type']}&#10;Overlap: {rel['overlap_ratio']:.1%}&#10;Matching: {rel['matching_values']:,}"

            # Add labels on the lines
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2

            relationship_lines_svg += f"""
        <g class="er-relationship" data-table1="{rel['table1']}" data-table2="{rel['table2']}" data-rel-id="rel-{rel_idx}">
            <title>{tooltip_text}</title>
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="{line_color}" stroke-width="{line_width}" stroke-dasharray="{5 if i > 0 else 0}"/>
            <g transform="translate({start_x},{start_y}) rotate({angle_start})">
                <path d="{crow_foot_start}" stroke="{line_color}" stroke-width="2" fill="none"/>
            </g>
            <g transform="translate({end_x},{end_y}) rotate({angle_end})">
                <path d="{crow_foot_end}" stroke="{line_color}" stroke-width="2" fill="none"/>
            </g>
            <!-- Label on line -->
            <text x="{mid_x}" y="{mid_y - 5}" font-family="Inter, sans-serif" font-size="11"
                  fill="{line_color}" text-anchor="middle" style="pointer-events: none;">
                {rel['column1']}
            </text>
        </g>
        """
            rel_idx += 1

    html = f"""
    <section class="relationships-section">
        <h2 class="relationships-title">
            Table Relationships
        </h2>
        <p class="relationships-description">
            Automatically detected relationships between tables based on column names, data types, and value overlaps.
        </p>

        <!-- ER Diagram with Crow's Foot Notation -->
        <div class="alert-info mb-20">
            <strong>Interactive ER Diagram:</strong> Click on a table to highlight its relationships. Hover over connection lines to see details.
        </div>

        <div class="er-diagram-container">
            <svg id="er-diagram" width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">
                <!-- Relationship lines (drawn first, behind tables) -->
                {relationship_lines_svg}

                <!-- Table boxes -->
                {table_boxes_svg}
            </svg>
        </div>

        <style>
            .er-diagram-container {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                overflow-x: auto;
            }}
            .er-table {{
                cursor: pointer;
                transition: all 0.2s;
            }}
            .er-table:hover rect {{
                filter: brightness(0.95);
            }}
            .er-table.highlighted rect:first-child {{
                fill: #5005b8;
                stroke: #4004a0;
                stroke-width: 3;
            }}
            .er-relationship {{
                transition: all 0.2s;
            }}
            .er-relationship.highlighted line {{
                stroke: #6606dc !important;
                stroke-width: 3.5 !important;
            }}
            .er-relationship.highlighted path {{
                stroke: #6606dc !important;
                stroke-width: 2 !important;
            }}
            .er-relationship.dimmed {{
                opacity: 0.2;
            }}
            .er-table.dimmed {{
                opacity: 0.3;
            }}
        </style>

        <script>
            (function() {{
                const tables = document.querySelectorAll('.er-table');
                const relationships = document.querySelectorAll('.er-relationship');
                let selectedTable = null;

                tables.forEach(table => {{
                    table.addEventListener('click', function() {{
                        const tableName = this.getAttribute('data-table');

                        // Toggle selection
                        if (selectedTable === tableName) {{
                            // Deselect
                            selectedTable = null;
                            tables.forEach(t => t.classList.remove('highlighted', 'dimmed'));
                            relationships.forEach(r => r.classList.remove('highlighted', 'dimmed'));
                        }} else {{
                            // Select
                            selectedTable = tableName;

                            // Dim all tables and relationships
                            tables.forEach(t => t.classList.add('dimmed'));
                            relationships.forEach(r => r.classList.add('dimmed'));

                            // Highlight selected table
                            this.classList.remove('dimmed');
                            this.classList.add('highlighted');

                            // Highlight related tables and relationships
                            relationships.forEach(rel => {{
                                const table1 = rel.getAttribute('data-table1');
                                const table2 = rel.getAttribute('data-table2');

                                if (table1 === tableName || table2 === tableName) {{
                                    rel.classList.remove('dimmed');
                                    rel.classList.add('highlighted');

                                    // Highlight the connected table
                                    const connectedTable = table1 === tableName ? table2 : table1;
                                    tables.forEach(t => {{
                                        if (t.getAttribute('data-table') === connectedTable) {{
                                            t.classList.remove('dimmed');
                                            t.classList.add('highlighted');
                                        }}
                                    }});
                                }}
                            }});
                        }}
                    }});
                }});
            }})();
        </script>

        <!-- Detailed Table View -->
        <h3 class="relationships-table-title">
            Relationship Details
        </h3>

        <table class="relationship-table">
            <thead>
                <tr>
                    <th>SOURCE</th>
                    <th class="center col-arrow"></th>
                    <th>TARGET</th>
                    <th class="center col-type">TYPE</th>
                    <th class="center col-matching">MATCHING</th>
                    <th class="center col-overlap">OVERLAP</th>
                    <th class="col-confidence">CONFIDENCE</th>
                </tr>
            </thead>
            <tbody>
    """

    for rel in display_relationships:
        confidence_pct = rel['confidence'] * 100
        overlap_pct = rel['overlap_ratio'] * 100

        # Confidence color based on threshold
        if confidence_pct >= 90:
            confidence_color = "#10b981"  # Green
        elif confidence_pct >= 70:
            confidence_color = "#6606dc"  # Purple
        else:
            confidence_color = "#f59e0b"  # Orange

        # Overlap color based on value
        if overlap_pct >= 90:
            overlap_color = "#10b981"  # Green
        elif overlap_pct >= 70:
            overlap_color = "#6606dc"  # Purple
        else:
            overlap_color = "#f59e0b"  # Orange

        # Determine arrow direction
        if rel.get('direction') == 'table1_to_table2':
            arrow = "→"
        elif rel.get('direction') == 'table2_to_table1':
            arrow = "←"
        else:
            arrow = "↔"

        # Relationship type badge styling
        type_styles = {
            "one-to-one": "background: #dbeafe; color: #1e40af;",
            "many-to-one": "background: #e0e7ff; color: #4338ca;",
            "many-to-many": "background: #fce7f3; color: #9f1239;"
        }
        type_style = type_styles.get(rel['relationship_type'], "background: #f3f4f6; color: #4b5563;")

        html += f"""
                <tr>
                    <td>
                        <div class="relationship-cell-table">{rel['table1']}</div>
                        <div class="relationship-cell-column">{rel['column1']}</div>
                    </td>
                    <td class="center arrow">
                        {arrow}
                    </td>
                    <td>
                        <div class="relationship-cell-table">{rel['table2']}</div>
                        <div class="relationship-cell-column">{rel['column2']}</div>
                    </td>
                    <td class="center">
                        <span class="relationship-type-badge" style="{type_style}">
                            {rel['relationship_type']}
                        </span>
                    </td>
                    <td class="center relationship-matching">
                        {rel['matching_values']:,}
                    </td>
                    <td class="center">
                        <span class="confidence-pct" style="color: {overlap_color};">{overlap_pct:.0f}%</span>
                    </td>
                    <td>
                        <div class="confidence-bar-container">
                            <div class="confidence-bar-bg">
                                <div class="confidence-bar-fill" style="width: {confidence_pct:.1f}%; background: {confidence_color};"></div>
                            </div>
                            <span class="confidence-pct" style="color: {confidence_color};">{confidence_pct:.0f}%</span>
                        </div>
                    </td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </section>
    """

    return html


def generate_standalone_relationships_report(
    relationships: List[Dict],
    tables_metadata: Dict[str, Dict],
    output_path: str,
    min_confidence_display: float = 0.5
) -> None:
    """
    Generate full interactive ER diagram report

    Args:
        relationships: List of relationship dictionaries
        tables_metadata: Metadata about tables (row counts, column counts, primary keys)
        output_path: Path to save HTML file
        min_confidence_display: Minimum confidence to display
    """
    # Filter relationships
    display_relationships = [r for r in relationships if r['confidence'] >= min_confidence_display]
    display_relationships.sort(key=lambda x: x['confidence'], reverse=True)

    # Get tables involved in relationships
    tables_in_relationships = set()
    for rel in display_relationships:
        tables_in_relationships.add(rel['table1'])
        tables_in_relationships.add(rel['table2'])

    tables_list = sorted(tables_in_relationships)

    # Calculate table positions
    positions = _calculate_table_positions(tables_list, num_cols=4)

    # Calculate SVG canvas size
    max_x = max(pos[0] for pos in positions.values()) + 300
    max_y = max(pos[1] for pos in positions.values()) + 250

    # Build table boxes SVG
    table_boxes_svg = ""
    for table_name in tables_list:
        x, y = positions[table_name]
        columns = _get_table_columns_for_diagram(table_name, display_relationships, tables_metadata)

        # Get metadata
        metadata = tables_metadata.get(table_name, {})
        row_count = metadata.get('total_rows', 'N/A')
        if isinstance(row_count, int):
            row_count_str = f"{row_count:,}"
        else:
            row_count_str = str(row_count)

        # Calculate box height based on number of columns
        total_columns = len(columns['pk']) + len(columns['fk'])
        box_height = 60 + (total_columns * 22)

        # Create table box
        table_boxes_svg += f"""
        <g class="er-table" data-table="{table_name}">
            <rect x="{x}" y="{y}" width="280" height="{box_height}"
                  fill="white" stroke="#d1d5db" stroke-width="1.5" rx="6"/>
            <rect x="{x}" y="{y}" width="280" height="40"
                  fill="#6606dc" rx="6"/>
            <rect x="{x}" y="{y + 40}" width="280" height="{box_height - 40}"
                  fill="white" rx="0"/>
            <text x="{x + 140}" y="{y + 25}"
                  font-family="Inter, sans-serif" font-size="14" font-weight="600"
                  fill="white" text-anchor="middle">{table_name}</text>
            <text x="{x + 140}" y="{y + 36}"
                  font-family="Inter, sans-serif" font-size="10"
                  fill="rgba(255,255,255,0.8)" text-anchor="middle">{row_count_str} rows</text>
        """

        # Add columns
        y_offset = y + 58
        for pk_col in columns['pk']:
            table_boxes_svg += f"""
            <text x="{x + 10}" y="{y_offset}"
                  font-family="'Courier New', monospace" font-size="12" font-weight="bold"
                  fill="#1f2937">🔑 {pk_col}</text>
        """
            y_offset += 22

        for fk_col in columns['fk']:
            table_boxes_svg += f"""
            <text x="{x + 10}" y="{y_offset}"
                  font-family="'Courier New', monospace" font-size="12"
                  fill="#4b5563">{fk_col}</text>
        """
            y_offset += 22

        table_boxes_svg += "</g>"

    # Group relationships by table pair (same logic as summary section)
    table_pair_rels = defaultdict(list)
    for rel in display_relationships:
        pair_key = tuple(sorted([rel['table1'], rel['table2']]))
        table_pair_rels[pair_key].append(rel)

    # Build relationship lines with crow's foot notation
    relationship_lines_svg = ""
    rel_idx = 0
    for pair_key, rels in table_pair_rels.items():
        table1, table2 = pair_key

        if table1 not in positions or table2 not in positions:
            continue

        x1, y1 = positions[table1]
        x2, y2 = positions[table2]

        # Calculate center points of table boxes
        center_x1 = x1 + 140
        center_y1 = y1 + 100
        center_x2 = x2 + 140
        center_y2 = y2 + 100

        # Calculate edge connection points
        dx = center_x2 - center_x1
        dy = center_y2 - center_y1

        # Determine base connection points
        if abs(dx) > abs(dy):
            if dx > 0:
                base_start_x, base_start_y = x1 + 280, center_y1
                base_end_x, base_end_y = x2, center_y2
            else:
                base_start_x, base_start_y = x1, center_y1
                base_end_x, base_end_y = x2 + 280, center_y2
            offset_axis = 'vertical'
        else:
            if dy > 0:
                base_start_x, base_start_y = center_x1, y1 + 150
                base_end_x, base_end_y = center_x2, y2
            else:
                base_start_x, base_start_y = center_x1, y1
                base_end_x, base_end_y = center_x2, y2 + 150
            offset_axis = 'horizontal'

        # Draw each relationship with offset if multiple
        num_rels = len(rels)
        for i, rel in enumerate(rels):
            # Calculate offset for multiple relationships
            if num_rels > 1:
                offset = (i - (num_rels - 1) / 2) * 25
            else:
                offset = 0

            # Apply offset
            if offset_axis == 'vertical':
                start_x, start_y = base_start_x, base_start_y + offset
                end_x, end_y = base_end_x, base_end_y + offset
            else:
                start_x, start_y = base_start_x + offset, base_start_y
                end_x, end_y = base_end_x + offset, base_end_y

            # Line color based on confidence
            confidence = rel['confidence']
            if confidence >= 0.9:
                line_color = "#6606dc"
                line_width = 2.5
            elif confidence >= 0.7:
                line_color = "#9ca3af"
                line_width = 2
            else:
                line_color = "#d1d5db"
                line_width = 1.5

            # Calculate angles for crow's foot rotation
            angle_start = math.atan2(end_y - start_y, end_x - start_x) * 180 / math.pi
            angle_end = math.atan2(start_y - end_y, start_x - end_x) * 180 / math.pi

            # Get crow's foot paths
            crow_foot_start = _get_crow_foot_path(rel['relationship_type'], rel.get('direction', 'bidirectional'), True)
            crow_foot_end = _get_crow_foot_path(rel['relationship_type'], rel.get('direction', 'bidirectional'), False)

            # Build tooltip text
            tooltip_text = f"{rel['column1']} ↔ {rel['column2']}&#10;Confidence: {confidence:.1%}&#10;Type: {rel['relationship_type']}&#10;Overlap: {rel['overlap_ratio']:.1%}&#10;Matching: {rel['matching_values']:,}"

            # Add labels on the lines
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2

            relationship_lines_svg += f"""
        <g class="er-relationship" data-table1="{rel['table1']}" data-table2="{rel['table2']}" data-rel-id="rel-{rel_idx}">
            <title>{tooltip_text}</title>
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="{line_color}" stroke-width="{line_width}" stroke-dasharray="{5 if i > 0 else 0}"/>
            <g transform="translate({start_x},{start_y}) rotate({angle_start})">
                <path d="{crow_foot_start}" stroke="{line_color}" stroke-width="2" fill="none"/>
            </g>
            <g transform="translate({end_x},{end_y}) rotate({angle_end})">
                <path d="{crow_foot_end}" stroke="{line_color}" stroke-width="2" fill="none"/>
            </g>
            <!-- Label on line -->
            <text x="{mid_x}" y="{mid_y - 5}" font-family="Inter, sans-serif" font-size="11"
                  fill="{line_color}" text-anchor="middle" style="pointer-events: none;">
                {rel['column1']}
            </text>
        </g>
        """
            rel_idx += 1

    # Generate relationships HTML list
    relationships_html = ""
    for rel in display_relationships:
        confidence_pct = rel['confidence'] * 100

        if confidence_pct >= 80:
            confidence_class = 'confidence-high'
        elif confidence_pct >= 50:
            confidence_class = 'confidence-medium'
        else:
            confidence_class = 'confidence-low'

        # Determine arrow direction for display
        if rel.get('direction') == 'table1_to_table2':
            arrow = "→"
        elif rel.get('direction') == 'table2_to_table1':
            arrow = "←"
        else:
            arrow = "↔"

        relationships_html += f'''
        <div class="relationship-item {confidence_class}">
            <strong>{rel['table1']}.{rel['column1']}</strong> {arrow}
            <strong>{rel['table2']}.{rel['column2']}</strong><br>
            <small>
                Confidence: {confidence_pct:.1f}% |
                Type: {rel['relationship_type']} |
                Matching values: {rel['matching_values']:,} |
                Overlap: {rel['overlap_ratio']:.1%}
            </small>
        </div>
        '''

    # Generate HTML template
    html_template = f'''<!DOCTYPE html>
<html>
<head>
    <title>Table Relationships - ER Diagram</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f9fafb;
            color: #1f2937;
        }}
        .header {{
            background: linear-gradient(135deg, #6606dc 0%, #8b5cf6 100%);
            color: white;
            padding: 40px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 32px;
            font-weight: 700;
        }}
        .header p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .er-diagram-container {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 30px;
            margin: 20px 0;
            overflow-x: auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .er-table {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        .er-table:hover rect {{
            filter: brightness(0.95);
        }}
        .er-table.highlighted rect:first-child {{
            fill: #5005b8;
            stroke: #4004a0;
            stroke-width: 3;
        }}
        .er-relationship {{
            transition: all 0.2s;
        }}
        .er-relationship.highlighted line {{
            stroke: #6606dc !important;
            stroke-width: 3.5 !important;
        }}
        .er-relationship.highlighted path {{
            stroke: #6606dc !important;
            stroke-width: 2 !important;
        }}
        .er-relationship.dimmed {{
            opacity: 0.2;
        }}
        .er-table.dimmed {{
            opacity: 0.3;
        }}
        .info-panel {{
            background-color: white;
            border: 1px solid #e5e7eb;
            padding: 30px;
            margin-top: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .info-panel h2 {{
            margin: 0 0 20px 0;
            font-size: 24px;
            font-weight: 600;
            color: #1f2937;
        }}
        .relationship-item {{
            padding: 15px;
            margin: 10px 0;
            background-color: #f9fafb;
            border-left: 4px solid #10b981;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        .relationship-item:hover {{
            background-color: #f3f4f6;
            transform: translateX(4px);
        }}
        .confidence-high {{ border-left-color: #10b981; }}
        .confidence-medium {{ border-left-color: #f59e0b; }}
        .confidence-low {{ border-left-color: #ef4444; }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f9fafb;
            border-radius: 8px;
        }}
        .stat {{
            flex: 1;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #6606dc;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6b7280;
            margin-top: 4px;
        }}
        .tip-box {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            color: #0c4a6e;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Table Relationships - ER Diagram</h1>
        <p>Entity-Relationship diagram with crow's foot notation showing detected relationships</p>
    </div>

    <div class="container">
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(tables_in_relationships)}</div>
                <div class="stat-label">Tables</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(display_relationships)}</div>
                <div class="stat-label">Relationships</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(1 for r in display_relationships if r['confidence'] >= 0.8)}</div>
                <div class="stat-label">High Confidence (&ge;80%)</div>
            </div>
        </div>

        <div class="tip-box">
            <strong>Interactive ER Diagram:</strong> Click on a table to highlight its relationships. Hover over connection lines to see details.
        </div>

        <div class="er-diagram-container">
            <svg id="er-diagram" width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">
                <!-- Relationship lines (drawn first, behind tables) -->
                {relationship_lines_svg}

                <!-- Table boxes -->
                {table_boxes_svg}
            </svg>
        </div>

        <div class="info-panel">
            <h2>Detected Relationships</h2>
            <div id="relationships-list">
                {relationships_html}
            </div>
        </div>
    </div>

    <script>
        (function() {{
            const tables = document.querySelectorAll('.er-table');
            const relationships = document.querySelectorAll('.er-relationship');
            let selectedTable = null;

            tables.forEach(table => {{
                table.addEventListener('click', function() {{
                    const tableName = this.getAttribute('data-table');

                    // Toggle selection
                    if (selectedTable === tableName) {{
                        // Deselect
                        selectedTable = null;
                        tables.forEach(t => t.classList.remove('highlighted', 'dimmed'));
                        relationships.forEach(r => r.classList.remove('highlighted', 'dimmed'));
                    }} else {{
                        // Select
                        selectedTable = tableName;

                        // Dim all tables and relationships
                        tables.forEach(t => t.classList.add('dimmed'));
                        relationships.forEach(r => r.classList.add('dimmed'));

                        // Highlight selected table
                        this.classList.remove('dimmed');
                        this.classList.add('highlighted');

                        // Highlight related tables and relationships
                        relationships.forEach(rel => {{
                            const table1 = rel.getAttribute('data-table1');
                            const table2 = rel.getAttribute('data-table2');

                            if (table1 === tableName || table2 === tableName) {{
                                rel.classList.remove('dimmed');
                                rel.classList.add('highlighted');

                                // Highlight the connected table
                                const connectedTable = table1 === tableName ? table2 : table1;
                                tables.forEach(t => {{
                                    if (t.getAttribute('data-table') === connectedTable) {{
                                        t.classList.remove('dimmed');
                                        t.classList.add('highlighted');
                                    }}
                                }});
                            }}
                        }});
                    }}
                }});
            }});
        }})();
    </script>
</body>
</html>'''

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

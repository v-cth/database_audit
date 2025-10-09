"""
Database connection and query execution using Ibis
Supports BigQuery and Snowflake
"""

import ibis
import polars as pl
from typing import Optional, Dict, Any
from pathlib import Path
import json


class DatabaseConnection:
    """Handles database connections using Ibis framework"""

    SUPPORTED_BACKENDS = ['bigquery', 'snowflake']

    def __init__(self, backend: str, **connection_params):
        """
        Initialize database connection

        Args:
            backend: Database backend ('bigquery' or 'snowflake')
            **connection_params: Backend-specific connection parameters
        """
        if backend.lower() not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Backend '{backend}' not supported. "
                f"Supported backends: {', '.join(self.SUPPORTED_BACKENDS)}"
            )

        self.backend = backend.lower()
        self.connection_params = connection_params
        self.conn = None

    def connect(self) -> ibis.BaseBackend:
        """
        Establish database connection

        Returns:
            Ibis backend connection
        """
        if self.conn is not None:
            return self.conn

        try:
            if self.backend == 'bigquery':
                self.conn = self._connect_bigquery()
            elif self.backend == 'snowflake':
                self.conn = self._connect_snowflake()

            print(f"✅ Connected to {self.backend.upper()}")
            return self.conn

        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.backend}: {str(e)}")

    def _connect_bigquery(self) -> ibis.BaseBackend:
        """Connect to BigQuery"""
        # BigQuery connection parameters
        project_id = self.connection_params.get('project_id')
        dataset_id = self.connection_params.get('dataset_id')
        credentials_path = self.connection_params.get('credentials_path')
        credentials_json = self.connection_params.get('credentials_json')

        if not project_id:
            raise ValueError("BigQuery requires 'project_id' parameter")

        conn_kwargs = {'project_id': project_id}

        # Handle credentials
        if credentials_path:
            conn_kwargs['credentials'] = credentials_path
        elif credentials_json:
            # If credentials are provided as JSON string/dict
            if isinstance(credentials_json, str):
                credentials_json = json.loads(credentials_json)
            conn_kwargs['credentials'] = credentials_json

        if dataset_id:
            conn_kwargs['dataset_id'] = dataset_id

        return ibis.bigquery.connect(**conn_kwargs)

    def _connect_snowflake(self) -> ibis.BaseBackend:
        """Connect to Snowflake"""
        # Snowflake connection parameters
        required_params = ['account', 'user', 'password']
        for param in required_params:
            if param not in self.connection_params:
                raise ValueError(f"Snowflake requires '{param}' parameter")

        conn_kwargs = {
            'user': self.connection_params['user'],
            'password': self.connection_params['password'],
            'account': self.connection_params['account'],
        }

        # Optional parameters
        optional_params = ['database', 'schema', 'warehouse', 'role']
        for param in optional_params:
            if param in self.connection_params:
                conn_kwargs[param] = self.connection_params[param]

        return ibis.snowflake.connect(**conn_kwargs)

    def get_table(self, table_name: str, schema: Optional[str] = None) -> ibis.expr.types.Table:
        """
        Get table reference

        Args:
            table_name: Name of the table
            schema: Optional schema name (overrides connection default)

        Returns:
            Ibis table expression
        """
        if self.conn is None:
            self.connect()

        if schema:
            # Use schema.table notation
            full_name = f"{schema}.{table_name}"
            return self.conn.table(full_name)
        else:
            return self.conn.table(table_name)

    def execute_query(
        self,
        table_name: str,
        schema: Optional[str] = None,
        limit: Optional[int] = None,
        custom_query: Optional[str] = None,
        sample_size: Optional[int] = None
    ) -> pl.DataFrame:
        """
        Execute query and return Polars DataFrame

        Args:
            table_name: Name of the table
            schema: Optional schema name
            limit: Limit number of rows
            custom_query: Custom SQL query (overrides table_name)
            sample_size: Sample size for large tables

        Returns:
            Polars DataFrame with query results
        """
        if self.conn is None:
            self.connect()

        if custom_query:
            # Execute raw SQL only if explicitly provided
            result = self.conn.sql(custom_query)
        else:
            # Get table reference
            table = self.get_table(table_name, schema)

            # Apply sampling if specified
            if sample_size:
                if self.backend == 'bigquery':
                    # BigQuery uses TABLESAMPLE
                    # Note: BigQuery requires percent, so calculate based on estimate
                    # For simplicity, we'll use limit after sample
                    table = table.order_by(ibis.random()).limit(sample_size)
                elif self.backend == 'snowflake':
                    # Snowflake supports SAMPLE
                    table = table.order_by(ibis.random()).limit(sample_size)
            elif limit:
                table = table.limit(limit)

            result = table

        # Convert to Polars DataFrame directly
        # Ibis natively supports Polars conversion
        polars_df = result.to_polars()
        return polars_df

    def get_row_count(self, table_name: str, schema: Optional[str] = None, approximate: bool = True) -> int:
        """
        Get row count for a table

        Args:
            table_name: Name of the table
            schema: Optional schema name
            approximate: If True, use INFORMATION_SCHEMA for fast approximate count (default: True)
                        If False, use COUNT(*) for exact count (slower, more expensive)

        Returns:
            Number of rows in the table
        """
        if self.conn is None:
            self.connect()

        # Use INFORMATION_SCHEMA for fast approximate counts
        if approximate:
            try:
                if self.backend == 'bigquery':
                    # BigQuery INFORMATION_SCHEMA uses __TABLES__ for row counts
                    # Determine the dataset
                    dataset = schema or self.connection_params.get('dataset_id')
                    if not dataset:
                        raise ValueError("Dataset must be specified for BigQuery row count")

                    project_id = self.connection_params.get('project_id')

                    # Use Ibis API to query __TABLES__ metadata
                    tables_meta = self.conn.table(f'{project_id}.{dataset}.__TABLES__')
                    result = (
                        tables_meta
                        .filter(tables_meta.table_id == table_name)
                        .select('row_count')
                        .to_polars()
                    )
                    if len(result) > 0 and result['row_count'][0] is not None:
                        return int(result['row_count'][0])

                elif self.backend == 'snowflake':
                    # Snowflake INFORMATION_SCHEMA
                    database = self.connection_params.get('database')
                    schema_name = schema or self.connection_params.get('schema', 'PUBLIC')

                    # Use Ibis API to query INFORMATION_SCHEMA
                    info_schema = self.conn.table(f'{database}.INFORMATION_SCHEMA.TABLES')
                    result = (
                        info_schema
                        .filter(
                            (info_schema.table_schema == schema_name) &
                            (info_schema.table_name == table_name.upper())
                        )
                        .select('row_count')
                        .to_polars()
                    )
                    if len(result) > 0:
                        return int(result['ROW_COUNT'][0])

            except Exception as e:
                print(f"⚠️  Could not get approximate row count from INFORMATION_SCHEMA: {e}")
                print(f"   Falling back to COUNT(*) query...")

        # Fallback to exact count using COUNT(*)
        try:
            table = self.get_table(table_name, schema)
            count_result = table.count().to_polars()
            # Polars returns a DataFrame with one row, extract the value
            return int(count_result[0, 0])
        except Exception as e:
            print(f"⚠️  Could not get exact count: {e}")
            # If all else fails, return None to skip row count
            return None

    def list_tables(self, schema: Optional[str] = None) -> list:
        """
        List available tables

        Args:
            schema: Optional schema name to filter tables

        Returns:
            List of table names
        """
        if self.conn is None:
            self.connect()

        if schema:
            return self.conn.list_tables(database=schema)
        else:
            return self.conn.list_tables()

    def close(self):
        """Close database connection"""
        if self.conn is not None:
            # Ibis connections don't always need explicit closing,
            # but we'll set to None to allow garbage collection
            self.conn = None
            print(f"🔒 Closed {self.backend.upper()} connection")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def create_connection(backend: str, **connection_params) -> DatabaseConnection:
    """
    Factory function to create database connection

    Args:
        backend: Database backend ('bigquery' or 'snowflake')
        **connection_params: Backend-specific connection parameters

    Returns:
        DatabaseConnection instance

    Examples:
        # BigQuery
        conn = create_connection(
            'bigquery',
            project_id='my-project',
            dataset_id='my_dataset',
            credentials_path='/path/to/credentials.json'
        )

        # Snowflake
        conn = create_connection(
            'snowflake',
            account='my-account',
            user='my-user',
            password='my-password',
            database='my_db',
            schema='my_schema',
            warehouse='my_warehouse'
        )
    """
    return DatabaseConnection(backend, **connection_params)

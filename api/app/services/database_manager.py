import os
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta


class DatabaseManager:
    def __init__(self):
        self.connection_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432"),
        }
        self.schema_info = None
        self.schema_info_timestamp = None
        self.cache_duration = timedelta(hours=1)

    def get_schema_info(self):
        current_time = datetime.now()

        # Return cached result if it exists and hasn't expired
        if (
            self.schema_info is not None
            and self.schema_info_timestamp is not None
            and current_time - self.schema_info_timestamp < self.cache_duration
        ):
            return self.schema_info

        # Cache expired or doesn't exist, fetch new data
        try:
            conn = psycopg.connect(**self.connection_params)
            conn.row_factory = dict_row

            with conn.cursor() as cur:
                cur.execute("""
                    WITH fk_info AS (
                        SELECT
                            tc.table_name,
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage ccu
                            ON ccu.constraint_name = tc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                    )
                    SELECT 
                        t.table_name,
                        array_agg(
                            json_build_object(
                                'column_name', c.column_name,
                                'data_type', c.data_type,
                                'is_nullable', c.is_nullable,
                                'foreign_key', json_build_object(
                                    'references_table', fk.foreign_table_name,
                                    'references_column', fk.foreign_column_name
                                )
                            )
                        ) as columns
                    FROM information_schema.tables t
                    JOIN information_schema.columns c 
                        ON t.table_name = c.table_name
                    LEFT JOIN fk_info fk
                        ON t.table_name = fk.table_name 
                        AND c.column_name = fk.column_name
                    WHERE t.table_schema = 'public'
                        AND t.table_type = 'BASE TABLE'
                    GROUP BY t.table_name
                """)

                self.schema_info = cur.fetchall()
                self.schema_info_timestamp = current_time
            conn.close()
        except Exception as e:
            raise ValueError(f"Database query failed: {str(e)}")
        return self.schema_info

    def execute_query(self, sql_query, limit_rows=None, read_only=False):
        try:
            conn = psycopg.connect(**self.connection_params)
            conn.set_read_only(read_only)
            conn.row_factory = dict_row
            with conn.cursor() as cur:
                cur.execute(sql_query)
                if limit_rows:
                    rows = cur.fetchmany(limit_rows)
                else:
                    rows = cur.fetchall()

                if not rows:
                    return []

                headers = list(rows[0].keys())
                csv_lines = [",".join(headers)]
                for row in rows:
                    values = [
                        str(row[h] if row[h] is not None else "") for h in headers
                    ]
                    csv_lines.append(",".join(values))
                return csv_lines

        except Exception as e:
            raise ValueError(f"Database query failed: {str(e)}")
        finally:
            conn.close()

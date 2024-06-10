from datetime import datetime
from typing import Any, Iterable
import psycopg2
from psycopg2 import sql
from logger import Logger


type QueryCondition = tuple[str, str, str | bool]


class DatabaseHandler:
    def __init__(
        self,
        db_name: str,
        user: str,
        password: str,
        host: str,
        port: int,
        logger: Logger,
    ) -> None:
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.logger = logger
        self.conn = None
        self.cur = None

    def connect(self) -> None:
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            self.cur = self.conn.cursor()
            self.logger.info(f"{"DB Connected":-^50}")
        except Exception as e:
            self.logger.info(f"Error connecting to the database: {e}")

    def close(self) -> None:
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
            self.logger.info(f"{"DB Connection Closed":-^50}")
        except Exception as e:
            self.logger.info(f"Error closing the connection: {e}")

    def create_table(self, table_name: str, schema: str) -> None:
        try:
            self.cur.execute(
                sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table_name), sql.SQL(schema)
                )
            )
            self.conn.commit()
            self.logger.info(f"Table {table_name} created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {e}")

    def delete_table(self, table_name: str) -> None:
        try:
            self.cur.execute(f"DROP TABLE {table_name}")
            self.conn.commit()
            self.logger.info(f"Table {table_name} deleted successfully.")
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {e}")

    def get_query_based_on_conditions(
        self,
        target_table_name: str,
        select_columns: list[str] | None = None,
        conditions: Iterable[QueryCondition] | None = None,
    ) -> list[dict[str, Any]]:
        """
        conditions = [(column_name, logic, condition),] -> [("active", "=", True)]
        """
        try:
            select_input = (
                sql.SQL(", ").join([sql.Identifier(c) for c in select_columns])
                if select_columns
                else sql.SQL("*")
            )

            if conditions:
                where_clause_parts = []
                where_values = []

                for column, logic, condition in conditions:
                    if column == "initiation_time":
                        where_clause_parts.append(
                            sql.SQL("{} {} {}").format(
                                sql.Identifier(column),
                                sql.SQL(logic),
                                sql.SQL(condition),
                            )
                        )
                        continue
                    where_clause_parts.append(
                        sql.SQL("{} {} {}").format(
                            sql.Identifier(column), sql.SQL(logic), sql.Placeholder()
                        )
                    )
                    where_values.append(condition)

                where_clause = sql.SQL(" AND ").join(where_clause_parts)
                query = sql.SQL("SELECT {} FROM {} WHERE {}").format(
                    select_input, sql.Identifier(target_table_name), where_clause
                )
                self.cur.execute(query, where_values)
            else:
                query = sql.SQL("SELECT {} FROM {}").format(
                    select_input, sql.Identifier(target_table_name)
                )
                self.cur.execute(query)
            column_names = [desc[0] for desc in self.cur.description]
            result = self.cur.fetchall()
            return [dict(zip(column_names, row)) for row in result]
        except Exception as e:
            self.logger.error(f"{e.__class__} Error: {e}")

    def execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> list[tuple]:
        try:
            self.cur.execute(query, params)
            self.conn.commit()
            return self.cur.fetchall()
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")

    def insert_row(self, table_name: str, data: dict[str, Any]) -> None:
        try:
            columns = data.keys()
            values = [data[column] for column in columns]
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.SQL(", ").join(sql.Placeholder() * len(values)),
            )
            self.cur.execute(insert_query, values)
            self.conn.commit()
            self.logger.info("Successful")
        except Exception as e:
            self.logger.error(f"Error inserting data into table {table_name}: {e}")

    def update_column(
        self, table_name: str, primary_key: dict[str, Any], update_data: dict[str, Any]
    ) -> None:
        try:
            set_clause = sql.SQL(", ").join(
                sql.Composed(
                    [sql.Identifier(column), sql.SQL(" = "), sql.Placeholder()]
                )
                for column in update_data.keys()
            )
            set_values = list(update_data.values())

            where_clause = sql.SQL(" AND ").join(
                sql.Composed(
                    [sql.Identifier(column), sql.SQL(" = "), sql.Placeholder()]
                )
                for column in primary_key.keys()
            )
            where_values = list(primary_key.values())

            query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
                sql.Identifier(table_name), set_clause, where_clause
            )

            values = set_values + where_values
            self.cur.execute(query, values)
            self.conn.commit()
            self.logger.info(f"Data in table {table_name} updated successfully.")
        except Exception as e:
            self.logger.error(f"Error updating data in table {table_name}: {e}")
            self.conn.rollback()

    def get_last_station_sequence(self, table_name: str, plate_number: str, initiation_time: datetime) -> int | None:
        try:
            query = """
                SELECT station_sequence
                FROM {}
                WHERE plate_number = %s
                AND initiation_time = %s
            """.format(
                table_name
            )
            self.cur.execute(
                query,
                (
                    plate_number,
                    initiation_time,
                ),
            )
            result = self.cur.fetchall()
            if result:
                return result[-1][0]
            return None
        except Exception as e:
            self.logger.error(f"Error: {e}")

import os
from datetime import datetime, timezone, timedelta
from bus_api import DataFetcher, DataParser
from db_controller import DatabaseHandler
from db_operation import (
    convert_api_raw,
    get_target_with_index,
    push_new,
    push_intersections,
    push_inactive,
    identify_differences,
    filter_inactive_db,
)
from logger import Logger, LOGGING_CONFIG
from config import Config
from exceptions import NoDataError


def run_get_and_record(
    db: DatabaseHandler, logger: Logger, table_names: tuple[str, str]
) -> None:
    ### Set table names for bus_initial_entry, bus_stop_record
    parent_table, child_table = table_names

    ### Get bus API
    ### Bus Locations API Call
    logger.info(f"{"Get Bus API":-<30}")
    fetched, _ = DataFetcher(
        service_name="buslocationservice",
        service_operation="getBusLocationList",
        service_key=Config.SERVICE_KEY_BUS_API,
        route_id=Config.BUS_ROUTE_ID,
    ).request_get_data()
    api_bus = DataParser(fetched).explore_new_xml()
    api_query_time: str = api_bus.get("msgHeader").get("queryTime")
    api_bus_locations: list[dict[str, str]] = api_bus.get("msgBody").get(
        "busLocationList"
    )
    if not (api_query_time and api_bus_locations):
        raise NoDataError("No bus is operating in the route.")
    logger.info(f"--{len(api_bus_locations) = }")
    for bus in api_bus_locations:
        converted = convert_api_raw(bus, api_query_time)
        logger.info(f"api bus {converted.get("plate_number")} / {converted.get("query_time")}")

    ### Get DB
    logger.info(f"{"Get DB":-<30}")
    db_query = db.get_query_based_on_conditions(
        target_table_name=parent_table,
        select_columns=["initiation_time", "plate_number"],
        conditions=[("active", "=", True)],
        # conditions=[("active", "=", True), ("initiation_time", ">=", "NOW() - INTERVAL '3 HOURS'")],
    )
    for bus in db_query:
        logger.info(f"db  bus {bus.get("plate_number")} / {bus.get("initiation_time")}")
    # Filter active which is supposed to be inactive
    # especially when script is starting after long pause
    db_query_filtered, inactive_filtered = filter_inactive_db(
        db_query=db_query,
        now_utc=datetime.now(tz=timezone.utc),
        filter_timedelta=timedelta(hours=3),
    )
    logger.info(f"--{len(db_query) = } {len(db_query_filtered) = } {len(inactive_filtered) = }")

    ### Extracts plates with indices from either API and DB
    active_plates_api = get_target_with_index(api_bus_locations, "plateNo")
    active_plates_db = get_target_with_index(db_query_filtered, "plate_number")
    logger.info(f"{active_plates_api = }")
    logger.info(f"{active_plates_db = }")

    ### Categorize plates
    logger.info(f"{"Categorize plates":-<30}")
    new_plates, intersection, inactive = identify_differences(
        active_plates_api, active_plates_db
    )
    logger.info(f"--{len(new_plates) = }")
    logger.info(f"--{len(intersection) = }")
    logger.info(f"--{len(inactive) = }")

    ## Gather bus data for each category with indices -> Update DB
    if new_plates:
        logger.info(f"{"Push new":-^25}{len(new_plates):-^5}")
        new_push_data = [
            convert_api_raw(api_bus_locations[i], api_query_time)
            for i in new_plates.values()
        ]
        for d in new_push_data:
            logger.info(f"new push {d = }")
            push_new(
                db=db,
                bus_data=d,
                bus_initial_entry_table=parent_table,
                bus_stops_table=child_table,
            )

    if intersection:
        logger.info(f"{"Push intersections":-^25}{len(intersection):-^5}")
        intersection_push_api_db_combined = [
            {
                **convert_api_raw(api_bus_locations[api_idx], api_query_time),
                **db_query[db_idx],
            }
            for api_idx, db_idx in intersection.values()
        ]
        for d in intersection_push_api_db_combined:
            logger.info(f"intersections d => {d}")
        intersection_result = [
            push_intersections(
                db=db,
                bus_data=d,
                bus_stops_table=child_table,
            )
            for d in intersection_push_api_db_combined
        ]
        intersection_push_result = {
            res: intersection_result.count(res) for res in set(intersection_result)
        }
        logger.info(f"{intersection_push_result = }")

    if inactive:
        logger.info(f"{"Push inactive":-^25}{len(inactive):-^5}")
        inactive_push_data = [db_query[i] for i in inactive.values()]
        for d in inactive_push_data:
            logger.info(f"inactive {d = }")
            push_inactive(
                db=db,
                target_data=d,
                bus_initial_entry_table=parent_table,
            )

    if inactive_filtered:
        logger.info(f"{"Push inactive_filtered":-^25}{len(inactive_filtered):-^5}")
        for d in inactive_filtered:
            logger.info(f"inactive {d = }")
            push_inactive(
                db=db,
                target_data=d,
                bus_initial_entry_table=parent_table,
            )


def main() -> None:
    log_file_name = os.path.join(
        Config.WORKING_DIRECTORY,
        "logs",
        f"{"_".join(Config.APP_NAME)}.log",
    )
    logger = Logger(__name__, LOGGING_CONFIG, log_file_name).logger
    logger.info("")
    try:
        logger.info(f"{"Script started":-^50}")
        db = DatabaseHandler(
            db_name=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            logger=logger,
        )
        db.connect()
        if not (db.conn and db.cur):
            raise ConnectionError("No connection.")
        run_get_and_record(
            db=db,
            logger=logger,
            table_names=(Config.DB_TABLE_PARENT, Config.DB_TABLE_CHILD),
        )
        db.close()
        logger.info(f"{"End":-^50}")
    except Exception as exc:
        logger.error(exc.__class__, exc_info=True)


if __name__ == "__main__":
    main()

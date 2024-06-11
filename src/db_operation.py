from datetime import datetime, timezone, timedelta
from typing import Any, Iterable
from db_controller import DatabaseHandler
from config import Config


type IdentifyDiffResult = tuple[
    dict[str, int], dict[str, tuple[int, int]], dict[str, int]
]
type QueryReturn = list[dict[str, str | datetime]]


def convert_dt_as_utc(date_time: str, timez_zone: str) -> datetime:
    """Convert date&time str to dt object, as UTC, according to system timezone"""
    as_dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f").astimezone(tz=timezone.utc)
    if timez_zone == "UTC":
        return as_dt - timedelta(hours=9)
    return as_dt


def convert_api_raw(bus_data: dict[str, Any], query_time: str) -> dict[str, Any]:
    """From API raw data, extract onlyl necessary data and match to database keys
    :param query_time: is added for handling this single bus data
    """
    query_time_astimezone = convert_dt_as_utc(query_time, Config.SYSTEM_TIMEZONE)
    return {
        "plate_number": bus_data.get("plateNo"),
        "query_time": query_time_astimezone,
        "station_sequence": int(bus_data.get("stationSeq")),
        "station_id": bus_data.get("stationId"),
        "route_id": bus_data.get("routeId"),
    }


def generate_for_bus_history(bus_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "plate_number": bus_data.get("plate_number"),
        "route_id": bus_data.get("route_id"),
        "initiation_time": bus_data.get("query_time"),
        "active": True,
    }


def generate_for_bus_stops(bus_data: dict[str, Any]) -> dict[str, Any]:
    """New plates -> query_time will be initiation_time
    new bus -> query_time == initiation_time
    intersection bus -> query_time != initiation_time
    initiation_time data is added by combining API and DB data
    """
    initiation_time = bus_data.get("initiation_time")
    if not initiation_time:
        initiation_time = bus_data.get("query_time")
    return {
        "initiation_time": initiation_time,
        "plate_number": bus_data.get("plate_number"),
        "station_sequence": int(bus_data.get("station_sequence")),
        "arrival_time": bus_data.get("query_time"),
        "station_id": bus_data.get("station_id"),
    }


def get_target_with_index[T](data: Iterable[T], target: str) -> dict[str, int] | None:
    return {d.get(target): i for i, d in enumerate(data)}


def push_new(
    db: DatabaseHandler,
    bus_data: dict[str, Any],
    bus_initial_entry_table: str,
    bus_stops_table: str,
) -> None:
    """For NEW"""
    # add to bus history
    history_data = generate_for_bus_history(bus_data)
    db.insert_row(bus_initial_entry_table, history_data)
    # add to bus stops
    stop_data = generate_for_bus_stops(bus_data)
    db.insert_row(bus_stops_table, stop_data)


def push_intersections(
    db: DatabaseHandler, bus_data: dict[str, Any], bus_stops_table: str
) -> bool | str:
    """For INTERSECTION"""
    plate_number = bus_data.get("plate_number")
    initiation_time = bus_data.get("initiation_time")
    station_sequence = bus_data.get("station_sequence")
    last_station_seq_in_db = db.get_last_station_sequence(
        bus_stops_table, plate_number, initiation_time
    )
    if not last_station_seq_in_db:
        stop_data = generate_for_bus_stops(bus_data)
        db.insert_row(bus_stops_table, stop_data)
        return True
    if station_sequence > last_station_seq_in_db:
        stop_data = generate_for_bus_stops(bus_data)
        db.insert_row(bus_stops_table, stop_data)
        return True
    return "NOT previous seq < current seq"


def push_inactive(
    db: DatabaseHandler, target_data: dict[str, Any], bus_initial_entry_table: str
) -> None:
    """For INACTIVE / primary key needs key value pair for initiation_time and plate_number"""
    filter_keys = {"initiation_time", "plate_number"}
    def _filter_necessary_keys_values(data: dict[str, str | datetime]) -> dict[str, str | datetime]:
        return {k: v for k, v in data.items() if k in filter_keys}
    filtered_data = _filter_necessary_keys_values(target_data)
    if len(filtered_data) < 2:
        raise KeyError("Necessary keys not found in target_data while pushing inactive to DB.")
    db.update_column(
        bus_initial_entry_table, filtered_data, update_data={"active": False}
    )


def identify_differences(left: dict, right: dict) -> IdentifyDiffResult:
    """Returns (left, intersection, right)"""
    intersection = {}
    left_temp = left.copy()
    right_temp = right.copy()

    for i in left:
        if i in right:
            # for intersections record indices from each left and right
            # since therir indices coming from api and db are different
            # same indices do not represent the same bus
            intersection[i] = (left_temp[i], right_temp[i])
            left_temp.pop(i)
            right_temp.pop(i)

    return left_temp, intersection, right_temp


def filter_inactive_db(
    db_query: QueryReturn, now_utc: datetime, filter_timedelta: timedelta
) -> tuple[QueryReturn, QueryReturn]:
    """If init_time is passed more than filter_timedelta, set as inactive"""
    db, filtered, inactive = db_query[:], [], []
    while db:
        popped = db.pop()
        init_time = popped.get("initiation_time")
        if (now_utc - init_time) > filter_timedelta:
            inactive.append(popped)
            continue
        filtered.append(popped)
    return filtered, inactive

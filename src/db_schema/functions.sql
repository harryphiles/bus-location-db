CREATE OR REPLACE FUNCTION get_duration_all(departure_station INT, arrival_station INT)
RETURNS TABLE (
    Init TIMESTAMP,
    Plate VARCHAR,
    DEPARTURE TEXT,
    ARRIVAL TEXT,
    DIFF NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bi.initiation_time AT TIME ZONE 'Asia/Seoul' AS Init,
        bi.plate_number AS Plate,
        TO_CHAR(origin.arrival_time AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS DEPARTURE,
        TO_CHAR(dest.arrival_time AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS ARRIVAL,
        ROUND(EXTRACT(EPOCH FROM (dest.arrival_time - origin.arrival_time)) / 60, 0) AS DIFF
    FROM 
        bus_initial_entry bi
    LEFT JOIN 
        bus_stop_record dest 
        ON bi.initiation_time = dest.initiation_time 
        AND bi.plate_number = dest.plate_number 
        AND dest.station_sequence = arrival_station
    LEFT JOIN 
        bus_stop_record origin 
        ON bi.initiation_time = origin.initiation_time 
        AND bi.plate_number = origin.plate_number 
        AND origin.station_sequence = departure_station
    ORDER BY Init ASC;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_duration(departure_station INT, arrival_station INT)
RETURNS TABLE (
    Init TIMESTAMP,
    Plate VARCHAR,
    DEPARTURE TEXT,
    ARRIVAL TEXT,
    DIFF NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bi.initiation_time AT TIME ZONE 'Asia/Seoul' AS Init,
        bi.plate_number AS Plate,
        TO_CHAR(origin.arrival_time AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS DEPARTURE,
        TO_CHAR(dest.arrival_time AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS ARRIVAL,
        ROUND(EXTRACT(EPOCH FROM (dest.arrival_time - origin.arrival_time)) / 60, 0) AS DIFF
    FROM 
        bus_initial_entry bi
    LEFT JOIN 
        bus_stop_record dest 
        ON bi.initiation_time = dest.initiation_time 
        AND bi.plate_number = dest.plate_number 
        AND dest.station_sequence = arrival_station
    LEFT JOIN 
        bus_stop_record origin 
        ON bi.initiation_time = origin.initiation_time 
        AND bi.plate_number = origin.plate_number 
        AND origin.station_sequence = departure_station
    WHERE
        dest.arrival_time IS NOT NULL
        AND origin.arrival_time IS NOT NULL
    ORDER BY Init ASC;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_duration_dates(
    departure_station INT,
    arrival_station INT,
    from_date TIMESTAMP,
    to_date TIMESTAMP
)
RETURNS TABLE (
    Init TIMESTAMP,
    Plate VARCHAR,
    Depart TIMESTAMP,
    Arrive TIMESTAMP,
    DIFF NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bi.initiation_time AT TIME ZONE 'Asia/Seoul' AS Init,
        bi.plate_number AS Plate,
        origin.arrival_time AT TIME ZONE 'Asia/Seoul' AS Depart,
        dest.arrival_time AT TIME ZONE 'Asia/Seoul' AS Arrive,
        ROUND(EXTRACT(EPOCH FROM (dest.arrival_time - origin.arrival_time)) / 60, 0) AS DIFF
    FROM 
        bus_initial_entry bi
    LEFT JOIN 
        bus_stop_record dest 
        ON bi.initiation_time = dest.initiation_time 
        AND bi.plate_number = dest.plate_number 
        AND dest.station_sequence = arrival_station
    LEFT JOIN 
        bus_stop_record origin 
        ON bi.initiation_time = origin.initiation_time 
        AND bi.plate_number = origin.plate_number 
        AND origin.station_sequence = departure_station
    WHERE
        dest.arrival_time IS NOT NULL
        AND origin.arrival_time IS NOT NULL
        AND bi.initiation_time BETWEEN from_date AND to_date
    ORDER BY Depart ASC;
END;
$$ LANGUAGE plpgsql;

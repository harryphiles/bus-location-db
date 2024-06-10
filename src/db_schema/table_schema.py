bus_parent = """
    initiation_time TIMESTAMPTZ NOT NULL,  -- Start time of the bus route
    plate_number VARCHAR(20) NOT NULL,
	route_id VARCHAR(20) NOT NULL,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (initiation_time, plate_number)
"""

bus_child = """
    plate_number VARCHAR(20) NOT NULL,
    station_sequence INT NOT NULL,
    arrival_time TIMESTAMPTZ NOT NULL,
    station_id VARCHAR(100),
    initiation_time TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (initiation_time, plate_number, station_sequence),
    FOREIGN KEY (initiation_time, plate_number) REFERENCES test_1_bus_initial_entry(initiation_time, plate_number)
"""

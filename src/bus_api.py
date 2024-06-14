import xml.etree.ElementTree as ET
from typing import Any
import requests


class DataFetcher:
    """Fetches Bus Data from API"""
    services = {
        "buslocationservice",
        "busrouteservice",
    }
    operations = {
        "getBusLocationList",
        "getBusRouteInfoItem",
    }

    def __init__(
        self,
        service_key: str,
        route_id: int,
        service_name: str,
        service_operation: str,
        station_id: int | None = None,
    ) -> None:
        if (
            service_name not in self.services
            or service_operation not in self.operations
        ):
            raise KeyError("Given services are not allowed.")
        self.api_url = (
            f"http://apis.data.go.kr/6410000/{service_name}/{service_operation}"
        )
        self.api_url_operation = self.api_url
        self.api_service_key = service_key
        self.params = {"routeId": route_id}

    def request_get_data(self) -> tuple[ET.Element, str] | None:
        p = {"serviceKey": self.api_service_key, **self.params}

        try:
            r = requests.get(url=self.api_url_operation, params=p)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            return root, r.url
        except Exception as exc:
            raise exc.__class__


class DataParser:
    """Parse XML data"""
    def __init__(self, xml_element: ET.Element) -> None:
        self.xml_element = xml_element

    def _get_query_time(self) -> str | None:
        return self.xml_element.find("msgHeader/queryTime").text

    def _get_msg_body(self) -> ET.Element:
        """Extracts the <msgBody>...</msgBody> portion from the XML"""
        return self.xml_element.find("msgBody")
        # return self.xml_element.find("msgBody/busLocationList")

    def _extract_bus_location(self, xml_element: ET.Element) -> dict[str, Any] | None:
        """Recursively parse XML element into a dictionary."""
        parsed_data = {}

        for child in xml_element:
            sub_data = {}
            # plate_no = ""
            station_seq = 0
            for c in child:
                if c.tag == "stationSeq":
                    station_seq = c.text
                    parsed_data[station_seq] = {}
                    continue
                sub_data[c.tag] = c.text
            parsed_data[station_seq] = sub_data

        return parsed_data

    def get_bus_location(self) -> dict[str, Any]:
        _msg_body = self._get_msg_body()
        return {
            "query_time": self._get_query_time(),
            "bus_locations": self._extract_bus_location(_msg_body),
        }

    def _explore_xml_to_dict(self, xml_element: ET.Element) -> dict[str, Any]:
        """Recursively parse XML element into a dictionary."""
        parsed_data = {}

        for child in xml_element:
            child_data = (
                self._explore_xml_to_dict(child) if len(child) > 0 else child.text
            )

            if child.tag in parsed_data:
                if isinstance(parsed_data[child.tag], list):
                    parsed_data[child.tag].append(child_data)
                else:
                    parsed_data[child.tag] = [parsed_data[child.tag], child_data]
            else:
                parsed_data[child.tag] = child_data

        return parsed_data

    def explore_new_xml(self) -> dict[str, Any]:
        return self._explore_xml_to_dict(self.xml_element)

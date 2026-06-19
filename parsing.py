from __future__ import annotations
import re
from exceptions import InvalidLine
from matplotlib.colors import is_color_like
from typing import IO


class DataValidator():
    """Parser and validator for drone flight configuration files.

        Reads a structured text file line by line, validates each line against
        expected formats using regex, and populates zone, connection, and drone
        count data for downstream use.

        Attributes:
            nb_drones: Number of drones to deploy (default 12).
            zone_list: Dict of parsed zone entries keyed by role
                (``'start_hub'``, ``'end_hub'``, ``'hub1'``, etc.).
            connection_list: Dict mapping ``(zone_a, zone_b)`` tuples to
                connection metadata dicts.
            position: List of ``(x, y)`` coordinate tuples for all zones.
        """

    def __init__(self: "DataValidator") -> None:
        """Initialise DataValidator with empty data structures and defaults."""
        self.nb_drones = 12
        self.zone_list: dict = {}
        self.connection_list: dict = {}
        self.position: list = []

    def parsing_metadata_block(
            self: "DataValidator", string: str,
            idx: int, linetype: str) -> dict | None:
        """Parse and validate the optional metadata block of a config line.

        Handles three line types with different allowed keys and defaults:
        ``'zone'``, ``'special'`` (start/end hubs), and ``'connection'``.

        Args:
            string: Raw content of the ``[...]`` metadata block, stripped
                of brackets. Empty string applies defaults.
            idx: 1-based line number used in error messages.
            linetype: One of ``'zone'``, ``'special'``, or ``'connection'``.

        Returns:
            Dict of parsed metadata:
            - For zones/specials: ``{'color': str, 'zone': str,
              'max_drones': int | float}``.
            - For connections: ``{'links_num': int}``.
            - ``None`` if ``linetype`` is unrecognised.

        Raises:
            InvalidLine: If the metadata block structure is invalid, the
                color is not a recognised color string, ``max_drones`` is
                zero, the zone type is unknown, or ``links_num`` is zero.
        """
        if linetype in ("zone", "special"):
            if len(string) == 0 and linetype == "special":
                return {"color": "yellow", "max_drones": float("inf"),
                        "zone": "normal"}
            if len(string) == 0 and linetype == "zone":
                return {"color": "yellow", "max_drones": 1, "zone": "normal"}
            rules = (r"^(?!.*color=.*color=)(?!.*max_drones=.*max_drones)"
                     r"(?!.*zone=.*zone)"
                     r"\s*((color=(?P<color>\w+)|"
                     r"max_drones=(?P<max_drones>\d+)|"
                     r"zone=(?P<zone>\w+))\s*)*\s*$")
            zones = ["normal", "blocked", "priority", "restricted"]
            patteren = re.compile(rules)
            search = patteren.search(string)
            if not search:
                raise InvalidLine(f"error in line {idx}:\n"
                                  "     invalid metadata structure should be "
                                  "like\n[<color=(valid color)> <zone=(can be "
                                  "restricted or normal or blocked or priority"
                                  ")> <max_drones=(a positive integer number)>"
                                  "  <OPTIONAL>]")
            if not search.group("color"):
                color = "yellow"
            else:
                color = search.group("color")
                if color == "rainbow":
                    color = "yellow"
                if not is_color_like(color):
                    raise InvalidLine(
                        f"invalid metadata for color in line {idx}")
            if (search.group("max_drones") and
                    int(search.group("max_drones")) == 0):
                raise InvalidLine(f"error in line {idx}:\n  "
                                  "max_drones should be a positive integer")

            if linetype == "special":
                max_drones = float("inf")
            elif not search.group("max_drones"):
                max_drones = 1
            else:
                max_drones = int(search.group("max_drones"))
            if not search.group("zone"):
                zone = "normal"
            else:
                zone = search.group("zone")
                if zone not in zones:
                    raise InvalidLine(
                        f"invalid metadata for zone in line {idx}")
            return {"color": color, "zone": zone, "max_drones": max_drones}
        if linetype == "connection":
            if len(string) == 0:
                return {"links_num": 1}
            pattern = r"^\s*max_link_capacity=(?P<links_num>\d+)(?:\s+)?$"
            search = re.search(pattern, string)
            if search is None or int(search.group("links_num")) == 0:
                raise InvalidLine(
                    f"  invalid metadata for connection in line {idx}")
            links_num = int(search.group("links_num"))
            return {"links_num": links_num}
        return None

    def validate_lines(self: "DataValidator", f: IO[str]) -> None:
        """Validate and parse all lines from the configuration file object.

        Iterates through the file, skipping blank lines and comments.
        Expects the first non-comment line to declare ``nb_drones``,
        followed by exactly one ``start_hub``, exactly one ``end_hub``,
        any number of ``hub`` lines, and any number of ``connection`` lines.

        Args:
            f: Open file-like object in text read mode (``IO[str]``).

        Raises:
            InvalidLine: On any structural error — wrong first line,
                duplicate zone names or coordinates, duplicate connections,
                self-connections, missing start or end hub, no connections
                provided, or unrecognised line format.
        """
        duplicate_name: dict = dict()
        duplicate_coords: dict = dict()
        duplicate_connections: dict = dict()
        hub_count: int = 0
        start_count: int = 0
        connections_names: dict = dict()
        first_time: bool = True
        end_count: int = 0
        first_connection = False
        for idx, i in enumerate(f):
            idx += 1
            if not i or i.isspace() or i.startswith("#"):
                continue
            if first_time:
                if not re.match("^nb_drones:", i):
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "     nb_drones should be in first "
                                      "line of configuration file if there's"
                                      " no comments line")
                pateren = r"^nb_drones:\s+(?P<nb_drones>(\d+))\s*(#|$)"
                search = re.search(pateren, i)
                if search is None or int(search.group("nb_drones")) == 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "     should be like (nb_drones:"
                                      "  <strict_positive_integer>)")
                first_time = False
                self.nb_drones = int(search.group("nb_drones"))
            elif re.match("start_hub:", i):
                pateren = (r"^start_hub:\s+"
                           r"(?P<zone_name>[^-\n\s]+)\s+(?P<x_coord>-?\d+)\s*"
                           r"(?P<y_coord>-?\d+)\s+"
                           r"(?:\[(?P<metadata_block>.*)\])?\s*(#|$)")
                if start_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "the start_hub line "
                                      "have been duplicated")
                start_count += 1
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "     should be like (start_hub: <name> "
                                      "(not space or '-')> <x> (int)"
                                      " <y> (int) [optional]\n[color=...."
                                      "max_drones=(should be an int)]")
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                x = int(search.group("x_coord"))
                y = int(search.group("y_coord"))
                coords = (x, y)
                self.position.append(coords)
                if ((x, y)) in duplicate_coords:
                    raise InvalidLine("Error duplicate coords:\n"
                                      f"    in line {duplicate_coords[(x, y)]}"
                                      f"and line {idx}")
                duplicate_coords.update({(x, y): idx})
                name = search.group("zone_name")
                if name in duplicate_name:
                    raise InvalidLine(f"Erro duplicate name {name}:\n"
                                      f"    in line {duplicate_name[name]}"
                                      f" and line {idx}")
                duplicate_name.update({name: idx})
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "special")
                start_data = {"start_hub": {
                            "name": name, "coords": coords,
                            "metadata": metadata}}
                self.zone_list.update(start_data)

            elif re.match("end_hub:", i):
                pateren = (r"^end_hub:\s+"
                           r"(?P<zone_name>[^-\n\s]+)\s+(?P<x_coord>-?\d+)\s+"
                           r"(?P<y_coord>-?\d+)\s*"
                           r"(?:\[(?P<metadata_block>.*)\])?\s*(#|$)")
                if end_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "     the end_hub line "
                                      "have been duplicated")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (end_hub: <name> "
                                      "(not space or '-')> <x> (positive int)"
                                      " <y> (positive int) [.....]")
                end_count = +1
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                x = int(search.group("x_coord"))
                y = int(search.group("y_coord"))
                coords = (x, y)
                self.position.append(coords)
                if ((x, y)) in duplicate_coords:
                    raise InvalidLine("Error duplicate coords:\n"
                                      f"    in line {duplicate_coords[(x, y)]}"
                                      f" and line {idx}")
                duplicate_coords.update({(x, y): idx})
                name = search.group("zone_name")
                if name in duplicate_name:
                    raise InvalidLine(f"Erro duplicate name {name}:"
                                      f"in line {duplicate_name[name]} "
                                      f"and line {idx}")
                duplicate_name.update({name: idx})
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "special")
                end_data = {"end_hub": {
                            "name": name, "coords": coords,
                            "metadata": metadata}}
                self.zone_list.update(end_data)
            elif re.match("hub: ", i):
                pateren = (r"^hub:\s+"
                           r"(?P<zone_name>[^-\n\s]+)\s+(?P<x_coord>-?\d+)\s+"
                           r"(?P<y_coord>-?\d+)\s*"
                           r"(?:\[(?P<metadata_block>.*)?\])?\s*(#|$)")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "\tshould be like (hub: <name>"
                                      "(not space or '-')> <x> (positive int)"
                                      "<y> (positive int) [.....]")
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                x = int(search.group("x_coord"))
                y = int(search.group("y_coord"))
                coords = (x, y)
                self.position.append(coords)
                if ((x, y)) in duplicate_coords:
                    raise InvalidLine(f"Error duplicate coords in line "
                                      f"{duplicate_coords[(x, y)]} "
                                      f"and line {idx}")
                duplicate_coords.update({(x, y): idx})
                name = search.group("zone_name")
                if name in duplicate_name:
                    raise InvalidLine(f"Erro duplicate name {name}:"
                                      f"in line {idx} and "
                                      f"line {duplicate_name[name]}")
                duplicate_name.update({name: idx})
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "zone")
                hub_count += 1
                hub_data = {f"hub{hub_count}": {
                            "name": name, "coords": coords,
                            "metadata": metadata}}
                self.zone_list.update(hub_data)
            elif re.match("connection: ", i):
                if not first_connection:
                    first_connection = not first_connection
                pateren = (r"^connection:\s+"
                           r"(?P<from>[^-\n\s]+)-(?P<to>[^-\n\s]+)"
                           r"\s*(?:\[(?P<metadata_block>.*)\])?\s*($|#)")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (connection): "
                                      "zone_name1-zone_name2 "
                                      "[max_link_capacity=(num)] "
                                      "[OPTIONAL]")
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "connection")
                start = search.group("from")
                end = search.group("to")
                connections_names.update({start: idx, end: idx})
                bridge = (start, end)
                if ((start, end) in duplicate_connections or
                   (end, start) in duplicate_connections):
                    duplication_line = (duplicate_connections[(start, end)]
                                        if (start, end) in
                                        duplicate_connections else
                                        duplicate_connections[(end, start)])
                    raise InvalidLine(f"Error: duplicate connection"
                                      f" in line {duplication_line} "
                                      f"and line {idx}")
                if start == end:
                    raise InvalidLine(
                        f"Error: duplicate connection in line {idx}")
                duplicate_connections.update({bridge: idx})
                connection = {bridge: metadata}
                self.connection_list.update(connection)
            else:
                raise InvalidLine(f"Error: invalid line format {idx}")
        if start_count == 0:
            raise InvalidLine("Error: no start_hub line been found")
        if end_count == 0:
            raise InvalidLine("Error: no end_hub line been found")

        self.invalid_connection_name(connections_names, duplicate_name)
        if not first_connection:
            raise InvalidLine("Error:   you provid no connections")

    def invalid_connection_name(self: "DataValidator",
                                list_names: dict, check_list: dict) -> None:
        """Verify that every zone name referenced in connections was declared.

        Args:
            list_names: Dict mapping zone names found in connection lines
                to their line numbers.
            check_list: Dict of all declared zone names (from ``zone_list``).

        Raises:
            InvalidLine: If any connection references a zone name that was
                not declared as a hub, start_hub, or end_hub.
        """
        for i in list_names.keys():
            if i not in check_list:
                raise InvalidLine(f"Error invalid zone given '{i}' "
                                  f"in line {list_names[i]}")

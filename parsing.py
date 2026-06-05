import re
from typing import IO, List, Dict
from exceptions import InvalidLine


class DataValidator():
    def __init__(self: "DataValidator") -> None:
        self.nb_drones = 12
        self.zone_list: Dict[dict] = {}
        self.connection_list: List[dict] = []

    def parsing_metadata_block(
            self: "DataValidator", string: str,
            idx: int, linetype: str) -> dict | None:
        if linetype == "zone":
            if len(string) == 0:
                return {"color": "none", "max_drones": 1, "zone": "normal"}
            rules = (r"^(?!.*color=.*color=)(?!.*max_drones=.*max_drones)"
                     r"(?!.*zone=.*zone)"
                     r"(?:\s+)?((color=(?P<color>\w+)|"
                     r"max_drones=(?P<max_drones>\d+)|"
                     r"zone=(?P<zone>\w+))(?:\s+)?)*$")
            colors = ["yellow", "blue", "magenta", "red", "black", "white",
                      "green", "lime", "cyan", "purple", "brown", "orange",
                      "maroon", "gold", "darkred", "violet",
                      "crimson", "rainbow"]
            zones = ["normal", "blocked", "priority", "restricted"]
            patteren = re.compile(rules)
            search = patteren.search(string)
            if not search:
                raise InvalidLine(f"error in line {idx}:\n"
                                  "invalid metadata structure [...]")
            if not search.group("color"):
                color = "none"
            else:
                color = search.group("color")
                if color not in colors:
                    raise InvalidLine(
                        f"invalid metadata for color in line {idx}")

            if not search.group("max_drones"):
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
            pattern = r"(?:\s+)?max_link_capacity=(?P<links_num>\d+)(?:\s+)?$"
            search = re.search(pattern, string)
            if search is None:
                raise InvalidLine(
                    f"invalid metada for connection in line {idx}")
            links_num = int(search.group("links_num"))
            return {"links_num": links_num}
        return None

    def validate_lines(self: "DataValidator", f: IO[str]) -> None:
        duplicate_name: Dict = dict()
        duplicate_coords: Dict = dict()
        duplicate_connections: Dict = dict()
        hub_count: int = 0
        start_count: int = 0
        connections_names: Dict = dict()
        first_time: bool = True
        end_count: int = 0
        for idx, i in enumerate(f):
            idx += 1
            if not i or i.isspace() or i.startswith("#"):
                continue
            if first_time:
                pateren = r"^nb_drones:\s+(?P<nb_drones>(\d+))(?:\s+|$|#)"
                search = re.search(pateren, i)
                if search is None or int(search.group("nb_drones")) == 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (nb_drones: "
                                      "<strict_positive_integer>)")
                first_time = False
                self.nb_drones = int(search.group("nb_drones"))
            elif re.match("start_hub:", i):
                pateren = (r"^start_hub:\s+"
                           r"(?P<zone_name>\w+)\s+(?P<x_coord>(?:-)?\d+)\s+"
                           r"(?P<y_coord>(?:-)?\d+)(?:\s+"
                           r"(?:\[(?P<metadata_block>.*)\])?(?:#|$|\s+)"
                           r"|#|\s+|$)")
                if start_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "the start_hub line "
                                      "have been duplicated")
                start_count += 1
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (start_hub: <name> "
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
                if ((x, y)) in duplicate_coords:
                    raise InvalidLine("Error duplicate coords"
                                      f"in line {duplicate_coords[(x, y)]}"
                                      f"and line {idx}")
                duplicate_coords.update({(x, y): idx})
                name = search.group("zone_name")
                if name in duplicate_name:
                    raise InvalidLine(f"Erro duplicate name {name}:"
                                      f"in line {duplicate_name[name]}"
                                      f" and line {idx}")
                duplicate_name.update({name: idx})
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "zone")
                start_data = {"start_hub": {
                            "name": name, "coords": coords,
                            "metadata": metadata}}
                self.zone_list.update(start_data)

            elif re.match("end_hub:", i):
                pateren = (r"^end_hub:\s+"
                           r"(?P<zone_name>\w+)\s+(?P<x_coord>(?:-)?\d+)\s+"
                           r"(?P<y_coord>(?:-)?\d+)(?:\s+"
                           r"(?:\[(?P<metadata_block>.*)\])?(?:$|\s+|#)|#|$)")
                if end_count != 0:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "the end_hub line "
                                      "have been duplicated")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (end_hub: <name>"
                                      "(not space or '-')> <x> (positive int)"
                                      "<y> (positive int) [.....]")
                end_count = +1
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                x = int(search.group("x_coord"))
                y = int(search.group("y_coord"))
                coords = (x, y)
                if ((x, y)) in duplicate_coords:
                    raise InvalidLine("Error duplicate coords"
                                      f"in line {duplicate_coords[(x, y)]} "
                                      f"and line {idx}")
                duplicate_coords.update({(x, y): idx})
                name = search.group("zone_name")
                if name in duplicate_name:
                    raise InvalidLine(f"Erro duplicate name {name}:"
                                      f"in line {duplicate_name[name]} "
                                      f"and line {idx}")
                duplicate_name.update({name: idx})
                metadata = self.parsing_metadata_block(metadata_block,
                                                       idx, "zone")
                end_data = {"end_hub": {
                            "name": name, "coords": coords,
                            "metadata": metadata}}
                self.zone_list.update(end_data)
            elif re.match("hub: ", i):
                pateren = (r"^hub:\s+"
                           r"(?P<zone_name>\w+)\s+(?P<x_coord>(?:-)?\d+)\s+"
                           r"(?P<y_coord>(?:-)?\d+)(?:\s+"
                           r"(?:\[(?P<metadata_block>.*)\])?(?:$|\s+|#)"
                           r"|#|/s+|$)")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (hub: <name>"
                                      "(not space or '-')> <x> (positive int)"
                                      "<y> (positive int) [.....]")
                if search.group("metadata_block"):
                    metadata_block = search.group("metadata_block")
                else:
                    metadata_block = ""
                x = int(search.group("x_coord"))
                y = int(search.group("y_coord"))
                coords = (x, y)
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
                pateren = (r"^connection:\s+(?P<from>\w+)-(?P<to>\w+)"
                           r"(?:\s+(?:\[(?P<metadata_block>\w+)\])?(?:\s+|#|$)"
                           r"|#|$)")
                search = re.search(pateren, i)
                if search is None:
                    raise InvalidLine(f"Error in line {idx}:\n"
                                      "should be like (connection): "
                                      "zone_name1-zone_name2"
                                      "[max_link_capacity=(num)]"
                                      "(metadata optional)")
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
                    raise InvalidLine("Error: duplicate connection")
                duplicate_connections.update({bridge: idx})
                connection = {bridge: metadata}
                self.connection_list.append(connection)
            else:
                raise InvalidLine(f"Error: invalid line format {idx}")
        if start_count == 0:
            raise InvalidLine("Error: no start_hub line been found")
        if end_count == 0:
            raise InvalidLine("Error: no end_hub line been found")
        self.invalid_connection_name(connections_names, duplicate_name)

    def invalid_connection_name(self: "DataValidator",
                                list_names: dict, check_list: dict) -> None:
        for i in list_names.keys():
            if i not in check_list:
                raise InvalidLine(f"Error invalid zone given '{i}' "
                                  f"in line {list_names[i]}")

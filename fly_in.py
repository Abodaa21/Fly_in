from __future__ import annotations
try:
    from parsing import DataValidator
    import sys
    from collections import defaultdict
    from cbs import Path_finder
    from display import Visualization

    class Fly_in:
        """Entry point that wires parsing, pathfinding,
            and visualization together.

        Reads the configuration file, builds the zone graph and metadata,
        runs CBS to find conflict-free drone paths, prints the structured
        solution, and launches the Pygame visualizer.
        """

        solution = None

        def create_graph(self: "Fly_in", connections: dict) -> dict:
            """Build an adjacency list graph from the parsed connection dict.

            Each undirected connection ``(a, b)`` is stored as both
            ``a -> (weight, b)`` and ``b -> (weight, a)``.

            Args:
                connections: Dict mapping ``(zone_a, zone_b)`` tuples to
                    metadata dicts containing ``'links_num'``.

            Returns:
                ``defaultdict(list)`` mapping zone names to lists of
                ``(links_num, neighbour)`` tuples.
            """
            cnts = defaultdict(list)
            for con1, con2 in connections.keys():
                cnts[con1].append(
                    (connections[(con1, con2)]['links_num'], con2))
                cnts[con2].append(
                    (connections[(con1, con2)]['links_num'], con1))
            return cnts

        def create_info(self: "Fly_in", zones: dict) -> dict:
            """Flatten zone metadata into a name-keyed lookup dict.

                Args:
                    zones: Raw zone dict from ``DataValidator.zone_list``,
                    where values contain ``'name'``, ``'coords'``, and
                    ``'metadata'`` sub-dicts.

                Returns:
                    ``defaultdict(dict)`` mapping zone names to flattened dicts
                    with ``'zone'``, ``'max_drones'``, ``'coords'``, and
                    ``'color'`` keys.
                """
            lst: dict = defaultdict(dict)
            for _, value in zones.items():
                lst[value['name']].update(
                    {"zone": value['metadata']['zone'],
                     "max_drones": value['metadata']['max_drones'],
                     "coords": value["coords"],
                     "color": value["metadata"]["color"]})
            return lst

        def struct_solution(
                self: "Fly_in", solution: dict,
                start: str, zone_data: dict) -> dict:
            """Convert raw CBS paths into a turn-indexed printable structure.

            Groups each agent's movement by turn number and formats each
            move as ``"agent-location"`` or ``"agent-from-to"`` for
            restricted zone transits.

            Args:
                solution: Dict mapping agent names to ordered path lists
                    as returned by ``Path_finder.cbs``.
                start: Name of the global start hub (moves from start are
                    skipped).
                zone_data: Zone metadata dict used to identify restricted
                    zones.

            Returns:
                ``defaultdict(list)`` mapping turn numbers (int) to lists
                of formatted move strings for that turn.
            """
            if not solution:
                return {}
            s = defaultdict(list)
            max_turns = max(len(p) for p in solution.values())
            agents = list(solution.keys())
            for agent in agents:
                previous_path = start
                for turn in range(1, max_turns):
                    path_len = len(solution[agent]) - 1
                    if turn > path_len:
                        continue
                    curr_loc = solution[agent][turn]
                    if curr_loc in (start, previous_path):
                        if zone_data[curr_loc]["zone"] == "restricted":
                            s[turn].append(f"{agent}-{curr_loc}")
                        continue
                    if zone_data[curr_loc]["zone"] == "restricted":
                        s[turn].append(f"{agent}-{previous_path}-{curr_loc}")
                    else:
                        s[turn].append(f"{agent}-{curr_loc}")
                    previous_path = curr_loc
            return s

        def main(self: "Fly_in") -> None:
            """Parse the config file, run CBS, print results, and visualize.

            Reads the file path from ``sys.argv[1]``, validates its contents
            via ``DataValidator``, computes conflict-free drone paths with
            ``Path_finder.cbs``, prints the structured turn-by-turn solution,
            and launches ``Visualization.display``.

            Exits with an error message if the argument count is wrong or
            any exception is raised during processing.
            """
            if len(sys.argv) < 2:
                print("invalid number of arguments")
                exit()
            try:
                with open(sys.argv[1], "r") as f:
                    data = DataValidator()
                    data.validate_lines(f)
                    zone_data = self.create_info(data.zone_list)
                start = data.zone_list["start_hub"]["name"]
                goal = data.zone_list["end_hub"]["name"]
                graph = self.create_graph(data.connection_list)
                solution = Path_finder().cbs(graph, start, goal, zone_data,
                                             data.nb_drones,
                                             data.connection_list)
                if solution:
                    Fly_in.solution = self.struct_solution(
                        solution, start, zone_data)
                    print()
                    for key in Fly_in.solution.keys():
                        for value in Fly_in.solution[key]:
                            print(value, end=" ")
                        print()
                    Visualization().display(
                        data.position, zone_data,
                        data.connection_list, solution)

                else:
                    print("no solution been found")
            except Exception as e:
                print(e)

    Fly_in().main()
except (Exception, KeyboardInterrupt) as error:
    print(error)

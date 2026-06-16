from parsing import DataValidator
import sys
from collections import defaultdict
from cbs import Path_finder
from display import Visualization


class Fly_in:
    solution = None

    def create_graph(self, connections):
        cnts = defaultdict(list)
        for con1, con2 in connections.keys():
            cnts[con1].append((connections[(con1, con2)]['links_num'], con2))
            cnts[con2].append((connections[(con1, con2)]['links_num'], con1))
        return cnts

    def create_info(self, zones):
        lst = defaultdict(dict)
        for key, value in zones.items():
            lst[value['name']].update({"zone": value['metadata']['zone'], "max_drones": value['metadata']['max_drones'], "coords": value["coords"], "color": value["metadata"]["color"]})
        return lst

    def struct_solution(self, solution: dict, start, goal, zone_data):
        if not solution:
            return []
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

    def main(self):
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
            solution = Path_finder().cbs(graph, start, goal, zone_data, data.nb_drones, data.connection_list)
            if solution:
                Fly_in.solution = self.struct_solution(solution, start, goal, zone_data)
                Visualization().display(data.position, data.zone_list, zone_data, data.connection_list, solution)
            else:
                print("no solution been found")
        except Exception as e:
            print(e)


Fly_in().main()
# Visualization().display()

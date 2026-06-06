from parsing import DataValidator
import sys
from collections import defaultdict
import heapq
from cbs import cbs


def create_graph(connections):
    cnts = defaultdict(list)
    for con1, con2 in connections.keys():
        cnts[con1].append((connections[(con1, con2)]['links_num'], con2))
        cnts[con2].append((connections[(con1, con2)]['links_num'], con1))
    return cnts

def create_info(zones):
    lst = defaultdict(dict)
    for key, value in zones.items():
        lst[value['name']].update({"zone": value['metadata']['zone'], "max_drones": value['metadata']['max_drones']})
    return lst


# def solution_struct(solution):



if len(sys.argv) < 2:
    print("invalid number of arguments")
    exit()

with open(sys.argv[1], "r") as f:
    data = DataValidator()
    data.validate_lines(f)
    zone_data = create_info(data.zone_list)
start = data.zone_list["start_hub"]["name"]
goal = data.zone_list["end_hub"]["name"]

graph = create_graph(data.connection_list)
solution = cbs(graph, start, goal, data.zone_list, zone_data, data.nb_drones, data.connection_list)
print(solution)
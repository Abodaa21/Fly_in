import heapq
import copy


class Path_finder():
    def dijkstra(self, graph, start, goal, zone_data, constraints, agent):
        path = []
        visited = []
        open_list = [(0, 0, start, path)]
        if goal not in graph:
            return []
        while open_list:
            cost, turn, node, path = heapq.heappop(open_list)
            if node == goal:
                return path + [goal]
            visited.append(node)
            count = 0
            restrict = []
            for _, neighbour in graph[node]:
                if neighbour in visited:
                    continue
                new_turn = turn + 1
                new_path = path + [node]
                if zone_data[neighbour]['zone'] == 'normal':
                    new_cost = cost + 1
                elif zone_data[neighbour]['zone'] == 'priority':
                    new_cost = cost + 0.9
                elif zone_data[neighbour]['zone'] == 'restricted':
                    new_cost = cost + 2
                    if neighbour not in restrict:
                        restrict.append(neighbour)
                        new_path += [neighbour]
                        new_turn = turn + 2
                elif zone_data[neighbour]['zone'] == 'blocked':
                    continue
                count += 1
                if (agent, neighbour, turn + 1) in constraints:
                    continue
                heapq.heappush(open_list, (new_cost, new_turn, neighbour, new_path))
            if (agent, node, turn + 1) not in constraints and count != 0:
                if zone_data[node]['zone'] == 'normal':
                    new_cost = cost + 1
                elif zone_data[node]['zone'] == 'priority':
                    new_cost = cost + 0.9
                elif zone_data[node]['zone'] == 'restricted':
                    new_cost = cost + 2
                elif zone_data[node]['zone'] == 'blocked':
                    continue
                new_path = path + [node]
                heapq.heappush(open_list, (new_cost, turn + 1, node, new_path))
        return None


    def find_conflict(self, agents, zone_data, connection_list, start, goal):
        lst_agents = list(agents.keys())
        max_turns = max(len(p) for p in agents.values())
        previous_loc = None
        for turn in range(max_turns):
            zones = copy.deepcopy(zone_data)
            connections = copy.deepcopy(connection_list)
            for i in range(len(lst_agents)):
                conect = {"links_num": float("inf")}
                agent = lst_agents[i]
                path_size = len(agents[agent]) - 1
                agent_loc = agents[agent][min(turn, path_size)]
                if min(turn, path_size) != 0:
                    previous_loc = agents[agent][min(turn, path_size) - 1]
                if turn > path_size:
                    continue
                if (previous_loc, agent_loc) in connections:
                    conect = connections[(previous_loc, agent_loc)]
                elif (agent_loc, previous_loc) in connections:
                    conect = connections[(agent_loc, previous_loc)]
                if previous_loc != agent_loc:
                    if zones[agent_loc]["max_drones"] < 1 or conect["links_num"] < 1:
                        return {
                            "agent_a": agent,
                            "agent_b": None,
                            "location": agent_loc,
                            "turn": turn
                        }
                    else:
                        zones[agent_loc]["max_drones"] -= 1
                        conect["links_num"] -= 1
                else:
                    if zones[agent_loc]["max_drones"] < 1 or conect["links_num"] < 1:
                        return {
                            "agent_a": agent,
                            "agent_b": None,
                            "location": agent_loc,
                            "turn": turn
                        }
                    else:
                        zones[agent_loc]["max_drones"] -= 1
        return None


    def cbs(self, graph, start, goal, zone_data, nb_agents, connection_list):
        path = self.dijkstra(graph, start, goal, zone_data, set(), None)
        agents = {}
        if path is None:
            return []
        for agent in range(1, nb_agents + 1):
            agents[f"D{agent}"] = path
        root = {"cost": sum(len(p) for p in agents.values()),
                "constraints": set(),
                "agents": agents}
        count = 0
        node = [(root["cost"], count, root)]
        while node:
            _, _, root = heapq.heappop(node)
            conflict = self.find_conflict(root["agents"], zone_data, connection_list, start, goal)
            if conflict is None:
                return root["agents"]
            for agent in [conflict["agent_a"], conflict["agent_b"]]:
                if agent is None:
                    continue
                new_constraint = root["constraints"].copy()
                new_constraint.add((agent, conflict['location'], conflict['turn']))
                new_agents = root["agents"].copy()
                path = self.dijkstra(graph, start, goal, zone_data, new_constraint, agent)
                if not path:
                    continue
                new_agents[agent] = path
                new_root = {
                    "cost": sum(len(p) for p in new_agents.values()),
                    "constraints": new_constraint,
                    "agents": new_agents
                }
                count += 1
                heapq.heappush(node, (new_root["cost"], count, new_root))
        return []

import heapq
import copy


def astar(graph, start, goal, zone_data, constraints, agent):
    visited = set()
    path = []
    open_list = [(0, 0, start, path)]
    while open_list:
        cost, turn, node, path = heapq.heappop(open_list)
        if node == goal:
            return path + [goal]
        if (node, turn) in visited:
            continue
        visited.add((node, turn))
        for _, neighbour in graph[node]:
            if (agent, neighbour, turn + 1) in constraints:
                continue
            new_path = path + [node]
            if zone_data[neighbour]['zone'] == 'normal':
                new_cost = cost + 1
            elif zone_data[neighbour]['zone'] == 'priority':
                new_cost = cost + 0.9
            elif zone_data[neighbour]['zone'] == 'restricted':
                new_cost = cost + 2
            elif zone_data[neighbour]['zone'] == 'blocked':
                continue
            heapq.heappush(open_list, (new_cost, turn + 1, neighbour, new_path))
        if (agent, node, turn + 1) not in constraints:
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


def find_conflict(agents, zone_data, connection_list, start):
    lst_agents = list(agents.keys())
    max_turns = max(len(p) for p in agents.values())
    i = 0
    for turn in range(max_turns):
        zones = copy.deepcopy(zone_data)
        connections = copy.deepcopy(connection_list)
        for i in range(len(lst_agents)):
            agent = lst_agents[i]
            i += 1
            path_size = len(agents[agent]) - 1
            agent_loc = agents[agent][min(turn, path_size)]
            previous_loc = start
            if min(turn, path_size) != 0:
                previous_loc = agents[agent][min(turn, path_size) - 1]
            if previous_loc != agent_loc:
                if zones[agent_loc]["max_drones"] < 1 and connections[(previous_loc, agent_loc)]["links_num"] < 1:
                    print("inside")
                    return {
                        "agent_a": agent,
                        "agent_b": None,
                        "location": agent_loc,
                        "turn": turn
                    }
                else:
                    zones[agent_loc]["max_drones"] -= 1
                    connections[(previous_loc, agent_loc)]["links_num"] -= 1
            else:
                if zones[agent_loc]["max_drones"] < 1:
                    print(agent, agent_loc, turn)
                    print(connections)
                    return {
                        "agent_a": agent,
                        "agent_b": None,
                        "location": agent_loc,
                        "turn": turn
                    }
                else:
                    zones[agent_loc]["max_drones"] -= 1
                
            # for j in range(i + 1, len(lst_agents)):
            #     agent_a = lst_agents[i]
            #     agent_b = lst_agents[j]
            #     path_a = len(agents[agent_a]) - 1
            #     path_b = len(agents[agent_b]) - 1
            #     loc_a = agents[agent_a][min(turn, path_a)]
            #     loc_b = agents[agent_b][min(turn, path_b)]
            #     if loc_a == loc_b:
            #         print(loc_a, agent_a, agent_b)
            #         if zones[loc_a]['max_drones'] <= 1:
            #             return {
            #                 "agent_a": agent_a,
            #                 "agent_b": None,
            #                 "location": loc_a,
            #                 "turn": turn
            #             }
            #         elif zones[loc_a]['max_drones'] > 1:
            #             zones[loc_a]['max_drones'] -= 1
    return None


def cbs(graph, start, goal, zone_list, zone_data, nb_agents, connection_list):
    path = astar(graph, start, goal, zone_data, set(), None)
    agents = {}
    for agent in range(1, nb_agents + 1):
        agents[f"D{agent}"] = path
    root = {"cost": sum(len(p) for p in agents.values()),
            "constraints": set(),
            "agents": agents}
    # print(agents)
    count = 0
    node = [(root["cost"], count, root)]
    while node:
        _, _, root = heapq.heappop(node)
        conflict = find_conflict(root["agents"], zone_data, connection_list, start)
        if conflict is None:
            return root["agents"]
        for agent in [conflict["agent_a"], conflict["agent_b"]]:
            if agent is None:continue
            new_constraint = root["constraints"].copy()
            new_constraint.add((agent, conflict['location'], conflict['turn']))
            new_agents = root["agents"].copy()
            path = astar(graph, start, goal, zone_data, new_constraint, agent)
            if path is None:
                continue
            new_agents[agent] = path
            new_root = {
                "cost": sum(len(p) for p in new_agents.values()),
                "constraints": new_constraint,
                "agents": new_agents
            }
            count += 1
            heapq.heappush(node, (new_root["cost"], count, new_root))
    return "NO SOULUTION"

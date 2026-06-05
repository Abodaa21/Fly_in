import heapq


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
        for link_capacity, neighbour in graph[node]:
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



def find_conflict(agents, start, goal):
    lst_agents = list(agents.keys())
    max_turns = max(len(p) for p in agents.values())
    for turn in range(max_turns):
        for i in range(len(lst_agents)):
            for j in range(i + 1, len(lst_agents)):
                agent_a = lst_agents[i]
                agent_b = lst_agents[j]
                a_path = len(agents[agent_a]) - 1
                b_path = len(agents[agent_b]) - 1
                loc_a = agents[agent_a][min(turn, a_path)]
                loc_b = agents[agent_b][min(turn, b_path)]
                if loc_a == loc_b and loc_a not in [start, goal]:
                    return {
                        "agent_a": agent_a,
                        "agent_b": agent_b,
                        "location": loc_a,
                        "turn": turn
                    }
    return None


def cbs(graph, start, goal, zone_list, zone_data, nb_agents):
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
        conflict = find_conflict(root["agents"], start, goal)
        if conflict is None:
            return root["agents"]
        for agent in [conflict["agent_a"], conflict["agent_b"]]:
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

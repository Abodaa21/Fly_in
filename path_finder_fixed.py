import heapq
import copy


class Path_finder():

    def dijkstra(self, graph, start, goal, zone_data, constraints, agent):
        # (cost, turn, node, path)
        open_list = [(0, 0, start, [])]
        # visited tracks (node, turn) not just node — needed for wait moves
        visited = set()

        if goal not in graph:
            return []

        while open_list:
            cost, turn, node, path = heapq.heappop(open_list)

            if node == goal:
                return path + [goal]

            state = (node, turn)
            if state in visited:
                continue
            visited.add(state)

            for _, neighbour in graph[node]:
                zone = zone_data[neighbour]['zone']

                if zone == 'blocked':
                    continue

                new_turn = turn + 1

                if zone == 'normal':
                    new_cost = cost + 1
                elif zone == 'priority':
                    new_cost = cost + 0.9
                elif zone == 'restricted':
                    new_cost = cost + 2   # penalty for restricted, no path hack
                else:
                    continue

                if (agent, neighbour, new_turn) in constraints:
                    continue

                (new_node, new_turn_state) = (neighbour, new_turn)
                if (new_node, new_turn_state) in visited:
                    continue

                heapq.heappush(
                    open_list,
                    (new_cost, new_turn, neighbour, path + [node])
                )

            # wait in place option
            wait_turn = turn + 1
            if (agent, node, wait_turn) not in constraints:
                zone = zone_data[node]['zone']
                if zone == 'blocked':
                    continue
                wait_cost = cost + 1
                if (node, wait_turn) not in visited:
                    heapq.heappush(
                        open_list,
                        (wait_cost, wait_turn, node, path + [node])
                    )

        return None

    def find_conflict(self, agents, zone_data, connection_list, start, goal):
        lst_agents = list(agents.keys())
        max_turns = max(len(p) for p in agents.values())

        for turn in range(max_turns):
            zones = copy.deepcopy(zone_data)
            connections = copy.deepcopy(connection_list)

            for i in range(len(lst_agents)):
                agent = lst_agents[i]
                path = agents[agent]
                path_size = len(path) - 1
                agent_loc = path[min(turn, path_size)]

                # FIX: previous_loc is local per agent, not shared
                if min(turn, path_size) != 0:
                    previous_loc = path[min(turn, path_size) - 1]
                else:
                    previous_loc = agent_loc

                conect = {"links_num": float("inf")}
                if (previous_loc, agent_loc) in connections:
                    conect = connections[(previous_loc, agent_loc)]
                elif (agent_loc, previous_loc) in connections:
                    conect = connections[(agent_loc, previous_loc)]

                if turn > path_size:
                    continue

                moving = previous_loc != agent_loc

                if moving:
                    if (zones[agent_loc]["max_drones"] < 1 or
                            conect["links_num"] < 1):
                        # find who else is at agent_loc this turn
                        for j in range(len(lst_agents)):
                            if lst_agents[j] == agent:
                                continue
                            other_path = agents[lst_agents[j]]
                            other_size = len(other_path) - 1
                            if min(turn, other_size) >= len(other_path):
                                continue
                            if other_path[min(turn, other_size)] == agent_loc:
                                return {
                                    "agent_a": agent,
                                    # FIX: return agent_b so CBS can branch both ways
                                    "agent_b": lst_agents[j],
                                    "location": agent_loc,
                                    "turn": turn
                                }
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
                    # waiting in place
                    if (zones[agent_loc]["max_drones"] < 1 or
                            conect["links_num"] < 1):
                        for j in range(len(lst_agents)):
                            if turn >= len(agents[lst_agents[j]]):
                                continue
                            other = lst_agents[j]
                            if (other == agent or
                                    agents[other][turn] in [start, goal]):
                                continue
                            if agents[other][turn] == agent_loc:
                                if agents[other][turn - 1] == agent_loc:
                                    continue
                                return {
                                    "agent_a": other,
                                    "agent_b": agent,  # FIX: include agent_b
                                    "location": agent_loc,
                                    "turn": turn
                                }
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
        base_path = self.dijkstra(graph, start, goal, zone_data, set(), None)
        if base_path is None:
            return []

        agents = {}
        for agent in range(1, nb_agents + 1):
            # FIX: each agent gets its OWN copy of the path
            agents[f"D{agent}"] = list(base_path)

        root = {
            "cost": sum(len(p) for p in agents.values()),
            "constraints": set(),
            "agents": agents
        }

        count = 0
        open_nodes = [(root["cost"], count, root)]

        while open_nodes:
            _, _, current = heapq.heappop(open_nodes)

            conflict = self.find_conflict(
                current["agents"], zone_data, connection_list, start, goal)

            if conflict is None:
                return current["agents"]

            # FIX: branch on BOTH agents, not just agent_a
            for agent in [conflict["agent_a"], conflict["agent_b"]]:
                if agent is None:
                    continue

                new_constraints = current["constraints"].copy()
                new_constraints.add(
                    (agent, conflict["location"], conflict["turn"]))

                new_agents = {k: list(v)
                              for k, v in current["agents"].items()}

                new_path = self.dijkstra(
                    graph, start, goal, zone_data, new_constraints, agent)

                if not new_path:
                    continue

                new_agents[agent] = new_path

                new_root = {
                    "cost": sum(len(p) for p in new_agents.values()),
                    "constraints": new_constraints,
                    "agents": new_agents
                }

                count += 1
                heapq.heappush(
                    open_nodes, (new_root["cost"], count, new_root))

        return None

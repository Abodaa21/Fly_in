from __future__ import annotations
import heapq
import copy
from typing import Any


class Path_finder():
    """Pathfinding engine for multi-agent drone routing using CBS.

    Provides single-agent shortest-path search via a constraint-aware
    Dijkstra variant, conflict detection across agent paths, and a
    Conflict-Based Search (CBS) solver that coordinates all agents.
    """
    def dijkstra(self: "Path_finder", graph: dict, start: str, goal: str,
                 zone_data: dict, constraints: set,
                 agent: str | None) -> None | list:
        """Find the lowest-cost path from start to goal for a single agent.

        Uses a priority queue (min-heap) to explore nodes by cumulative cost.
        Zone types affect traversal cost, and (agent, location, turn) triples
        in ``constraints`` are treated as forbidden positions.

        Args:
            graph: Adjacency dict mapping node names to lists of
                (weight, neighbour) tuples.
            start: Name of the source node.
            goal: Name of the destination node.
            zone_data: Dict mapping node names to zone metadata including
                the ``'zone'`` type (``'normal'``, ``'priority'``,
                ``'restricted'``, or ``'blocked'``).
            constraints: Set of ``(agent, location, turn)`` triples that
                the agent must avoid.
            agent: Identifier of the agent being routed, or ``None`` when
                called without agent-specific constraints.

        Returns:
            Ordered list of node names from start to goal (inclusive),
            ``None`` if no path exists, or ``[]`` if the goal is not in
            the graph.
        """
        path: list = []
        visited = set()
        open_list: list = [(0, 0, start, path)]
        if goal not in graph:
            return []
        while open_list:
            cost, turn, node, path = heapq.heappop(open_list)
            if node == goal:
                return path + [goal]
            visited.add(node)
            count = 0
            restrict = set()
            for _, neighbour in graph[node]:
                if neighbour in visited:
                    continue
                new_turn = turn + 1
                new_path = path + [node]
                if zone_data[neighbour]['zone'] == 'normal':
                    new_cost = cost + 1.0
                elif zone_data[neighbour]['zone'] == 'priority':
                    new_cost = cost + 0.9
                elif zone_data[neighbour]['zone'] == 'restricted':
                    new_cost = cost + 1.0
                    if (neighbour not in restrict and
                       (agent, neighbour, new_turn) not in constraints):
                        restrict.add(neighbour)
                        new_path += [neighbour]
                        new_cost = cost + 2.0
                        new_turn = turn + 2
                elif zone_data[neighbour]['zone'] == 'blocked':
                    continue
                count += 1
                if (agent, neighbour, new_turn) in constraints:
                    continue
                heapq.heappush(
                    open_list, (new_cost, new_turn, neighbour, new_path))
            if (agent, node, turn + 1) not in constraints and count != 0:
                new_path = path + [node]
                heapq.heappush(open_list, (cost + 1, turn + 1, node, new_path))

        return None

    def find_conflict(self: "Path_finder", agents: dict, zone_data: dict,
                      connection_list: dict, start: str,
                      goal: str) -> None | dict:
        """Detect the first capacity or collision conflict across all agent
           paths.
        Simulates all agents moving simultaneously turn by turn. On each turn
        it checks whether the drone count at a zone or the link capacity
        between zones is exceeded.
        Args:
            agents: Dict mapping agent names to their ordered path lists.
            zone_data: Dict mapping node names to zone metadata including
                ``'max_drones'`` capacity.
            connection_list: Dict mapping ``(zone_a, zone_b)`` tuples to
                connection metadata including ``'links_num'`` capacity.
            start: Name of the global start hub (used to exempt waiting agents)
            goal: Name of the global end hub (used to exempt waiting agents).
        Returns:
            A conflict dict with keys ``'agent_a'``, ``'agent_b'``,
            ``'location'``, and ``'turn'`` describing the first conflict
            found, or ``None`` if all paths are conflict-free.
        """
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
# here i have to do a when the previous is a start point
#  or if the zone was waiting in his zone
# so if i waited in my place their no need to modifie the links_num
                if previous_loc != agent_loc:
                    if (zones[agent_loc]["max_drones"] < 1 or
                       conect["links_num"] < 1):
                        return {
                            "agent_a": agent,
                            "agent_b": None,
                            "location": agent_loc,
                            "turn": turn
                        }
                    else:
                        zones[agent_loc]["max_drones"] -= 1
                        conect["links_num"] -= 1
# this in case of an agent is already on position so
# you can not constraint that position
#  cause in case of no neighbours available an
# you will not found a solution
                else:
                    if (zones[agent_loc]["max_drones"] < 1 or
                       conect["links_num"] < 1):
                        for j in range(len(lst_agents)):
                            if turn >= len(agents[lst_agents[j]]):
                                continue
                            if (lst_agents[j] == agent or
                               agents[lst_agents[j]][turn] in [start, goal]):
                                continue
                            if agents[lst_agents[j]][turn] == agent_loc:
                                if (
                                 agents[lst_agents[j]][turn - 1] == agent_loc):
                                    continue
                                return {
                                    "agent_a": lst_agents[j],
                                    "agent_b": None,
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

    def cbs(self: "Path_finder", graph: dict, start: str, goal: str,
            zone_data: dict, nb_agents: int,
            connection_list: dict) -> Any:
        """Resolve multi-agent paths using Conflict-Based Search (CBS).

        Initialises all agents on the same base path, then iteratively
        detects conflicts and branches the search tree by adding constraints
        to individual agents until a conflict-free solution is found.

        Args:
            graph: Adjacency dict as produced by ``Fly_in.create_graph``.
            start: Name of the global start hub.
            goal: Name of the global end hub.
            zone_data: Dict mapping node names to zone metadata.
            nb_agents: Number of drones to route simultaneously.
            connection_list: Dict mapping ``(zone_a, zone_b)`` tuples to
                connection metadata.

        Returns:
            Dict mapping each agent name to its conflict-free path list,
            ``{}`` if no base path exists, or ``None`` if CBS exhausts the
            search space without a solution.
        """
        path = self.dijkstra(graph, start, goal, zone_data, set(), None)
        agents: dict = {}
        if path is None:
            return {}
        for agent in range(1, nb_agents + 1):
            agents[f"D{agent}"] = path
        root: dict = {"cost": sum(len(p) for p in agents.values()),
                      "constraints": set(),
                      "agents": agents}
        count = 0
        node = [(root["cost"], count, root)]

        while node:
            _, _, root = heapq.heappop(node)
            conflict = self.find_conflict(
                root["agents"], zone_data, connection_list, start, goal)
            if conflict is None:
                return root["agents"]
            for agent in [conflict["agent_a"], conflict["agent_b"]]:
                if agent is None:
                    continue
                new_constraint = copy.deepcopy(root["constraints"])
                new_constraint.add(
                    (agent, conflict['location'], conflict['turn']))
                new_agents = copy.deepcopy(root["agents"])
                path = self.dijkstra(
                    graph, start, goal, zone_data, new_constraint, agent)
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
        return None

*This project has been created as part of the 42 curriculum by abamine.*

# Fly-in — Drone Routing Simulation

## Description

Fly-in is a multi-agent pathfinding simulation written in Python. The goal is to route a fleet of drones from a central start hub to a target end hub across a network of zones, while respecting movement rules, zone capacities, and connection limits — in the fewest possible simulation turns.

The network is defined in a custom config file format: zones have types (normal, restricted, priority, blocked), optional drone capacity limits, and named bidirectional connections with optional link capacity constraints.

The system parses the config, builds the graph, runs a CBS-based pathfinding algorithm, outputs the step-by-step simulation to the terminal, and optionally renders it visually with Pygame.

---

## Instructions

### Requirements

- Python 3.10 or later
- pip

### Install dependencies

```bash
make install
```

This installs: `pygame`, `flake8`, `mypy`, `matplotlib`.

### Run

```bash
make run
```

Or with a custom map:

```bash
python3 fly_in.py path/to/your_map.txt
```

### Debug

```bash
make debug
```

### Lint

```bash
make lint
```

### Clean

```bash
make clean
```

---

## Usage Example

**Input (`config.txt`):**

```
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue max_drones=2]
hub: waypoint2 2 0 [color=blue zone=restricted max_drones=1]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1 [max_link_capacity=2]
connection: waypoint1-waypoint2 [max_link_capacity=2]
connection: waypoint2-goal
```

**Expected output:**

```
D1-waypoint1 
D1-waypoint1-waypoint2 D2-waypoint1 
D1-waypoint2 D3-waypoint1 
D1-goal D2-waypoint1-waypoint2 
D2-waypoint2 D4-waypoint1 
D2-goal D3-waypoint1-waypoint2 
D3-waypoint2 
D3-goal D4-waypoint1-waypoint2 
D4-waypoint2 
D4-goal 
```

Each line is one simulation turn. Each token is `D<ID>-<zone>` (or `D<ID>-<prev_zone>-<restricted_zone>` when a drone is mid-transit toward a restricted zone). Drones that don't move in a turn are omitted.

---

## Algorithm Explanation

### Overview

The pathfinding uses **Conflict-Based Search (CBS)**, a two-level algorithm designed for multi-agent pathfinding.

**High level:** a constraint tree where each node holds a set of constraints (agent, location, turn) and the agents' current paths. CBS pops the lowest-cost node, checks for conflicts, and if found, branches into two children (not in this case i go with only one child) — each adding a new constraint to resolve the conflict.

**Low level:** a modified **Dijkstra** search that finds the optimal path for a single agent given its current constraints. It handles:
- Zone type costs: normal = 1 turn, restricted = 2 turns, priority = 0.9 (preferred), blocked = skipped entirely
- Waiting in place (staying at a node costs 1 additional turn)
- Constraint avoidance: if (agent, node, turn) is in the constraint set, that move is skipped

### Conflict Detection (`find_conflict`)

At each turn, the simulation state is replayed. For every agent and turn, the function checks:
- Whether the destination zone exceeds its `max_drones` capacity
- Whether the traversed connection exceeds its `max_link_capacity`

If a conflict is found, it returns the offending agent(s), location, and turn — which CBS uses to generate new constraints.

### Why CBS?

CBS is complete and optimal for multi-agent pathfinding. It avoids replanning all agents simultaneously (which is exponential) by isolating conflicts one at a time. For the scale of this project (up to 25 drones, medium-sized graphs), it fits well.

### Complexity

- Low-level Dijkstra: O((V + E) log V) per agent per CBS node
- CBS high level: exponential worst case, but practical performance is strong when conflicts are sparse

### Output Structuring (`struct_solution`)

After CBS returns a solution dict `{agent: [path]}`, `struct_solution` converts it into the required output format: turn-indexed, with restricted-zone transit encoded as `agent-prev-current`.

---

## Visual Representation

The simulation includes a **Pygame graphical interface** (in `display.py`), activated by uncommenting the `Visualization().display(...)` call in `fly_in.py`.

Features:
- The graph is drawn with yellow edges connecting zone nodes
- Each zone is rendered as a colored circle matching its config color (white border for visibility)
- Zone type icons are overlaid: stop sign for restricted, star for priority, block image for blocked
- Drones are represented by animated sprite characters (three different images cycling by agent ID), positioned at their current zone each turn
- Restricted-zone transit is shown by placing the drone midway between source and destination
- Sounds play at timed intervals during the simulation for audio feedback
- Spacebar pauses/resumes the animation
- The simulation advances one turn per second (1000ms delay per frame)

The terminal output always runs regardless of whether the visual mode is active, so the simulation is usable in headless environments.

---

## Resources

### Pathfinding & Multi-Agent Search

- Sharon et al. (2015) — *Conflict-Based Search for Optimal Multi-Agent Pathfinding* (AAAI)
- [Dijkstra's algorithm](https://youtu.be/XB4MIexjvY0?si=arAgi_I5KqyYPpJQ)
- [CBS algorithm](https://youtu.be/FnrZyL6965o?si=BW3P-6UrnAF2BKnE)

### Python References

- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [Python `re` module](https://docs.python.org/3/library/re.html)
- [Pygame documentation](https://www.pygame.org/docs/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [flake8 documentation](https://flake8.pycqa.org/)

### AI Usage

AI was used during this project for:
- learning and clarifying the topics


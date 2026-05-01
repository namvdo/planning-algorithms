from collections import deque

def forward_search(x_init, x_goal, get_actions, transition):
    
    
    # 1. initialize - insert x_I, mark visited 
    queue = deque([x_init])
    visited = {x_init} 
    parent = {x_init: (None, None) } # state -> (parent_state, action_taken)
    while queue: 

        x = queue.popleft() 
        
        if is_goal(x): 
            return _extract_plan(parent, x) 
        
        for u in get_actions(x):
            x_next = transition(x, u) 
            if x_next not in visited:
                visited.add(x_next)
                parent[x_next] = (x, u)
                queue.append(x_next)
    
    return None
        
        

def _extract_plan(parent, goal): 
    "walk the parent map backward to reconstruct the action sequence"
    plan, state = [], goal 

    while parent[state][0] is not None: 
        prev, action = parent[state]
        plan.append((state, action))
        state = prev 
    
    plan.reverse() 
    return plan 


# S = start G = goal . free # walls
GRID = [
     "S.....#.",
     ".####...",
     "....#..G",
     "..#.....",
]

def parse_grid(grid):
    start, goal = None, None
    walls = set() 
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S':
                start = (r, c) 
            if ch == 'G':
                goal = (r, c)
            if ch == '#':
                walls.add((r, c))
    rows, cols = len(grid), len(grid[0])
    return start, goal, walls, rows, cols 


def make_grid_problem(grid):
    start, goal, walls, rows, cols  = parse_grid(grid)

    directions = { "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    
    def get_actions(state):
        r, c = state 
        return [
            action for action, (dr, dc) in directions.items() 
            if 0 <= r + dr < rows and 0 <= c + dc < cols 
            and (r + dr, c + dc) not in walls
        ]

    def transition(state, action): 
        dr, dc = directions[action]

        return (state[0] + dr, state[1] + dc)
    return start, lambda x: x == goal, get_actions, transition 

def print_solution(grid, plan): 
    if plan is None: 
        print("No plan found")
        return 
    
    path_state = {state for state, _ in plan }

    print(f"\nPlan found - {len(plan)} steps")

    for r, row in enumerate(grid):
        line = ""
        for c, ch in enumerate(row):
            if ch in ("S", "G", "#"):
                line += ch
            elif (r, c) in path_state: 
                line += "*"
            else:
                line += ch 
        print(" ", line)
    print() 
    
    for i, (state, action) in enumerate(plan, 1):
        print(f"step {i:2d}: move {action:5s}  → {state}")
    
    
    
if __name__ == "__main__":
    start, is_goal, get_actions, transition = make_grid_problem(GRID)
    
    print("GRID: ")
    for row in GRID:
        print(" ", row)
    
    plan = forward_search(start, is_goal, get_actions=get_actions, transition=transition)
    print_solution(GRID, plan)


         
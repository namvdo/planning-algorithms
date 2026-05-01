from collections import deque 

DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

INVERSE = {"up": "down", "down": "up", "left": "right", "right": "left"}

def backward_search(x_init, x_goal, get_inverse_actions, inverse_transition):
    
    queue = deque([x_goal])
    visited = {x_goal}
    parent = {x_goal: (None, None)} # parent[x'] = (x, u) where x is closer to goal 
    
    while queue: 
        x = queue.popleft() 
        
        if x == x_init:
            return _extract_plan(parent, x_init, x_goal)

        for u in get_inverse_actions(x):
            x_prev = inverse_transition(x, u) 
            if x_prev not in visited:
                visited.add(x_prev)
                parent[x_prev] = (x, u)
                queue.append(x_prev)
                
    return None




def _extract_plan(parent, x_init, x_goal): 
    plan, state = [], x_init 
    while state != x_goal: 
        next_state, action = parent[state]
        plan.append((next_state, action))
        state = next_state
    
    return plan
        
    


def parse_grid(grid):
    start = goal = None
    walls = set()
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "S": start = (r, c)
            if ch == "G": goal  = (r, c)
            if ch == "#": walls.add((r, c))
    return start, goal, walls, len(grid), len(grid[0])
 

def make_grid_problem(grid):
    start, goal, walls, rows, cols = parse_grid(grid)
    
    
    def get_inverse_actions(state):
        r, c = state 
        valid = []
        for action in DIRECTIONS:
            dr, dc = DIRECTIONS[INVERSE[action]]
            pr, pc = r + dr, c + dc 
            
            if 0 <= pr < rows and 0 <= pc < cols and (pr, pc) not in walls: 
                valid.append(action)
            
        
        return valid
    
    def inverse_transition(state, action):
        dr, dc = DIRECTIONS[INVERSE[action]]

        return (state[0] + dr, state[1] + dc)


    return start, goal, get_inverse_actions, inverse_transition
            
            
GRID = [
    "S.....#.",
    ".####...",
    "....#..G",
    "..#.....",
]


def print_solution(grid, plan):
    if plan is None:
        print("No plan found.")
        return
 
    path_states = {state for state, _ in plan}
    print(f"\nPlan found — {len(plan)} steps:\n")
    for r, row in enumerate(grid):
        line = ""
        for c, ch in enumerate(row):
            if ch in ("S", "G", "#"):
                line += ch
            elif (r, c) in path_states:
                line += "*"
            else:
                line += ch
        print(" ", line)
    print()
    for i, (state, action) in enumerate(plan, 1):
        print(f"  step {i:2d}: move {action:5s}  -> {state}")
        
        
if __name__ == "__main__":
    start, goal, get_inverse_actions, inverse_transition = make_grid_problem(GRID)
 
    print("Grid:")
    for row in GRID:
        print(" ", row)
 
    plan = backward_search(start, goal, get_inverse_actions, inverse_transition)
    print_solution(GRID, plan)
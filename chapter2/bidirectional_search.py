from collections import deque
"""
Bidirectional search - Lavalle's Planning Algorithms

Runs forward from x_I and backward from x_G simultaneously.
Terminates when the two frontiers share a state (x_mid)

Complexity advantage: 
Forward only: O(b^d)
Bidirectional: O(b^(d/2)) + O(b^(d/2)) two half-depth trees

The two searches alternate one expansion at a time (the "interleaving" strategy).

"""

DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

INVERSE = {"up": "down", "down": "up", "left": "right", "right": "left"}


def bidirectional_search(
    x_init,
    x_goal,
    get_actions,
    transition,
    get_inverse_actions,
    inverse_transition
):
    if x_init == x_goal:
        return [] 
    
    # forward queue (grows from x_init)
    fwd_queue = deque([x_init])
    fwd_visited = {x_init}
    fwd_parent = {x_init: (None, None)} # state -> (prev_state, action_taken)

    # backward queue (grows from x_goal)
    bwd_queue = deque([x_goal])
    bwd_visited = {x_goal}
    bwd_parent = {x_goal: (None, None)} # state -> (next_state, forward_action)

    while fwd_queue or bwd_queue:
        if fwd_queue:
            x_mid = _expand(
                queue = fwd_queue,
                visited= fwd_visited,
                parent=fwd_parent,
                get_actions=get_actions,
                transition=transition,
                other=bwd_visited
            )
            if x_mid is not None: 
                return _build_plan(fwd_parent, bwd_parent, x_init, x_mid, x_goal)
        
        if bwd_queue:
            x_mid = _expand(
                queue = bwd_queue,
                visited=bwd_visited,
                parent=bwd_parent,
                transition=inverse_transition,
                get_actions=get_inverse_actions,
                other=fwd_visited
            )
            
            if x_mid is not None:
                return _build_plan(fwd_parent, bwd_parent, x_init, x_mid, x_goal)
        
    return None 


def _expand(queue, visited, parent, get_actions, transition, other):
    if not queue:
        return None 
    
    x = queue.popleft() 
    # connection detected x is already known to other frontier
    
    if x in other: 
        return x 
    for u in get_actions(x):
        x_next = transition(x, u)
        if x_next not in visited:
            visited.add(x_next)
            parent[x_next] = (x, u)
            queue.append(x_next)
            
            # new node already visited by the other side -> connection
            if x_next in other:
                return x_next
    return None


def _build_plan(fwd_parent, bwd_parent, x_init, x_mid, x_goal):
    fwd_half = []
    
    state = x_mid 
    
    while fwd_parent[state][0] is not None:
        prev, action = fwd_parent[state]
        fwd_half.append((state, action))
        state = prev 
        
    fwd_half.reverse() 
    
    
    bwd_half = []
    state = x_mid 
    while bwd_parent[state][0] is not None:
        next_state, action = bwd_parent[state]
        bwd_half.append((next_state, action))
        state = next_state

    return fwd_half + bwd_half


GRID = [
    "S.....#.",
    ".####...",
    "....#..G",
    "..#.....",
]


def parse_grid(grid):
    start = goal = None 
    walls = set() 
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S': start = (r, c)
            if ch == 'G': goal = (r, c)
            if ch == '#': walls.add((r, c))
            
    return start, goal, walls, len(grid), len(grid[0])


def make_grid_problem(grid):
    start, goal, walls, rows, cols = parse_grid(grid)
    
    def get_actions(state):
        r, c = state 
        return [
            action for action, (dr, dc) in DIRECTIONS.items()
            if 0 <= r + dr < rows and 0 <= c + dc < cols 
            and (r + dr, c + dc) not in walls
        ]

    def transition(state, action): 
        dr, dc = DIRECTIONS[action]
        return (state[0] + dr, state[1] + dc)

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
    
    return start, goal, get_actions, transition, get_inverse_actions, inverse_transition


def print_solution(grid, plan, label):
    if plan is None: 
        print(f"{label}: No plan found.")
        return
    
    path_states = {state for state, _ in plan }
    print(f"\n{label} — {len(plan)} steps:\n")

    for r, row in enumerate(grid):
        line = ""
        for c, ch in enumerate(row):
            if ch in ('S', 'G', '#'):
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
    from collections import deque as _deque

    start, goal, get_actions, transition, get_inv_actions, inv_transition = make_grid_problem(GRID)
    print("Grid: ")
    for row in GRID:
        print(" ", row)
        
    def forward_search(x_init, is_goal, get_actions, transition):
        queue = _deque([x_init])
        visited = {x_init}
        parent = {x_init: (None, None)}
        
        while queue:
            x = queue.popleft() 
            if is_goal(x):
                plan, state = [], x 
                while parent[state][0] is not None: 
                    prev, action = parent[state]
                    plan.append((prev, action))
                    state = prev 
                plan.reverse() 
                return plan 
            for u in get_actions(x):
                x_next = transition(x, u) 
                if x_next not in visited: 
                    visited.add(x_next)
                    parent[x_next] = (x, u)
                    queue.append(x_next)
        return None 
    
    def backward_search(x_init, x_goal, get_inv, inv_trans):
        queue = _deque([x_goal])
        visited = {x_goal}
        parent = {x_goal: (None, None)}
        
        while queue:
            x = queue.popleft()
            if x == x_init: 
                plan, state = [], x_init 
                while parent[state][0] is not None: 
                    ns, action = parent[state]
                    plan.append((ns, action))
                    state = ns 
                return plan
            
            for u in get_inv(x):
                x_prev = inv_trans(x, u)
                if x_prev not in visited:
                    visited.add(x_prev)
                    parent[x_prev] = (x, u)
                    queue.append(x_prev)
                    
        return None 
    
    fwd_plan = forward_search(start, lambda x: x == goal, get_actions, transition)
    bwd_plan = backward_search(start, goal, get_inv_actions, inv_transition)
    
    bid_plan = bidirectional_search(
        start, goal, get_actions, transition, get_inv_actions, inv_transition
    )
    
    print_solution(GRID, fwd_plan, "Forward search ")
    print_solution(GRID, bwd_plan, "Backward search")
    print_solution(GRID, bid_plan, "Bidirectional  ")
    
    
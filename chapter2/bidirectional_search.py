from collections import deque

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
        
    fwd_parent.reverse() 
    
    
    bwd_half = []
    state = x_mid 
    while bwd_parent[state][0] is not None:
        next_state, action = bwd_parent[state]
        bwd_half.append((next_state, action))
        state = next_state

    return fwd_half + bwd_half
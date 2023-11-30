'''Helper functions and classes for trees and regex->nfa conversion'''

from typing import Dict, List, Tuple


class Node():
    def __init__(
        self,
        value = None,
        children=[],
        type: int = None,
        is_symbol: bool = False
    ):
        '''Initialize tree node for abstract syntax tree.'''
        self.value = value
        self.children = children
        # 0: operand, 1: operator
        self.type = type
        # DO NOT SET 'is_symbol' TO TRUE IF THE NODE IS AN OPERATOR
        self.is_symbol = is_symbol

    def add_child(self, child, insert: bool = False):
        if self.children:
            # Allowing for insertion at the start of the list is helpful
            # because the first operand popped off the operator stack is
            # the right operand.
            if insert:
                self.children.insert(0, child)
            else:
                self.children.append(child)
        else:
            self.children = [child]


class SimpleNFA():
    def __init__(
        self,
        transition_function: Dict[int, Dict[str, int]],
        accept_states: List[int],
        start_state: int,
        last_state: int
    ):
        '''Initialize a simple NFA class.'''
        self.transition_function = transition_function
        self.accept_states = accept_states
        self.start_state = start_state
        self.last_state = last_state

def epsilon_node_to_nfa(last_state: int = 0) -> Tuple[SimpleNFA, int]:
    '''Creates an epsilon NFA.'''
    state_1 = last_state+1
    accept_states = [state_1]
    epsilon_nfa = SimpleNFA(
        {},
        accept_states,
        state_1,
        state_1
    )
    return epsilon_nfa


def empty_set_to_nfa(last_state: int = 0) -> Tuple[SimpleNFA, int]:
    '''Creates an empty set NFA.'''
    state_1 = last_state+1
    empty_set_nfa = SimpleNFA(
        {},
        [],
        state_1,
        state_1
    )
    return empty_set_nfa


def union_to_nfa(
    left_nfa: SimpleNFA,
    right_nfa: SimpleNFA,
) -> SimpleNFA:
    '''Creates a union NFA.'''
    transition_function = {}
    transition_function.update(left_nfa.transition_function)
    transition_function.update(right_nfa.transition_function)
    # We just need to connect the two sub-NFAs
    union_epsilon_transitions = {
        'e': {
            left_nfa.start_state: None,
            right_nfa.start_state: None
        }
    }
    new_state = right_nfa.last_state+1
    transition_function[new_state] = union_epsilon_transitions
    union_nfa = SimpleNFA(
        transition_function=transition_function,
        accept_states=(left_nfa.accept_states + right_nfa.accept_states),
        start_state=new_state,
        last_state=new_state
    )
    return union_nfa


def kleene_star_to_nfa(nfa: SimpleNFA) -> SimpleNFA:
    transition_function = {}
    transition_function.update(nfa.transition_function)
    new_state = nfa.last_state+1
    transition_function[new_state] = {
        'e': {nfa.start_state: None}
    }
    # Adding e-transitions from every accept state of the sub-NFA to the start
    # state
    for state in nfa.accept_states:
        transition_function[state] = {
            'e': {nfa.start_state: None}
        }
    accept_states = nfa.accept_states + [new_state]
    kleene_star_nfa = SimpleNFA(
        transition_function=transition_function,
        accept_states=accept_states,
        start_state=new_state,
        last_state=new_state
    )
    return kleene_star_nfa


def concat_to_nfa(
    left_nfa: SimpleNFA,
    right_nfa: SimpleNFA,
) -> SimpleNFA:
    '''Creates a concatenation NFA'''
    left_accept_states = left_nfa.accept_states
    transition_function = {}
    transition_function.update(left_nfa.transition_function)
    transition_function.update(right_nfa.transition_function)
    # We need to connect every accept state of the left NFA to
    # the start state of the right NFA.
    for state in left_accept_states:
        # One of the accept states might already have an epsilon transition, so
        # we need to check for this and update accordingly, otherwise we could
        # replace the existing transition which is not desired.
        if (
            state not in transition_function
            or 'e' not in transition_function[state]
        ):
            transition_function[state] = {
                'e': {right_nfa.start_state: None}
            }
        else:
            transition_function[state]['e'].update(
                {right_nfa.start_state: None}
            )
    accept_states = right_nfa.accept_states
    concat_nfa = SimpleNFA(
        transition_function,
        accept_states,
        left_nfa.start_state,
        # Since we're doing a leftmost depth-first traversal of the syntax tree
        # we are guaranteed that the right subtree has the higher number of
        # states.
        right_nfa.last_state
    )
    return concat_nfa


def base_node_to_nfa(
    node: Node,
    last_state: int = 0
) -> SimpleNFA:
    '''Creating a symbol NFA.'''
    symbol = node.value
    state_1 = last_state+1
    state_2 = last_state+2
    transition_function = {
        state_1: {
            symbol: {state_2: None}
        }
    }
    accept_states = [state_2]
    base_nfa = SimpleNFA(
        transition_function,
        accept_states,
        state_1,
        state_2
    )
    return base_nfa


def depth_first(root: Node) -> SimpleNFA:
    '''Converts an AST root node to an equivalent NFA for the RegEx

    Args:
        root: the root node of the abstract syntax tree.

    Returns:
        the SimpleNFA object constructed from the tree
    '''
    if root:
        return depth_first_recursive(root, 0)


def depth_first_recursive(node: Node, last_state: int) -> SimpleNFA:
    '''Performs depth-first traversal.

    Args:
        node: The current node of the tree
        last_state: The last state created when constructing a sub-NFA.

    Returns:
        the SimpleNFA object constructed from the current node
    '''
    if not node.is_symbol:
        if not node.children:
            # Base cases that are not symbols
            if node.value == 'N':
                empty_set_nfa = empty_set_to_nfa(last_state)
                return empty_set_nfa
            if node.value == 'e':
                epsilon_nfa = epsilon_node_to_nfa(last_state)
                return epsilon_nfa
        else:
            if node.value == '*':
                operand = node.children[0]
                operand_nfa = depth_first_recursive(operand, last_state)
                kleene_star_nfa = kleene_star_to_nfa(operand_nfa)
                return kleene_star_nfa
            else:
                left_operand = node.children[0]
                right_operand = node.children[1]
                left_nfa = depth_first_recursive(left_operand, last_state)
                # We need to create the right sub NFA with states starting
                # at one higher than the last state created when constructing
                # the left sub NFA
                right_nfa = depth_first_recursive(right_operand, left_nfa.last_state)
                
                if node.value == '|':
                    union_nfa = union_to_nfa(left_nfa, right_nfa)
                    return union_nfa
                if node.value == '∘':
                    concat_nfa = concat_to_nfa(left_nfa, right_nfa)
                    return concat_nfa
    # Base case when the node is not of any of the previous types, meaning it
    # doesn't have children and it's a symbol.
    base_nfa = base_node_to_nfa(node, last_state)
    return base_nfa

"""This program implements a DFA simulator. It can read the DFA data from a
specified file and users can run strin gs through the DFA to determine if
they are valid or not.
"""

import sys


class FileFormatError(Exception):
    """
    Exception that is raised if the 
    input file to the DFA constructor
    is incorrectly formatted.
    """
    pass


class DFA:
    def __init__(self, *, filename = None):
        """
        Initializes DFA object from the dfa specification
        in named parameter filename.
        """
        if filename:
            self.alphabet = []
            self.number_of_states = None

            self.transition_function = {}
            self.start_state = None
            self.accept_states = {}
            self._read_dfa_data_from_file(filename)

    @property
    def num_states(self):
        """Returns the number of states of the DFA"""
        return self.number_of_states

    def transition(self, state: int, symbol: str) -> str:
        """
        Returns the state to transition to from 'state' on input 'symbol'.

        Args:
            state: The state to transition from. Must be in the range 
                1,...,num_states
            symbol: The input symbol to transition on from state. Must be in
                the alphabet.

        Returns:
            str: The state to transition to.
        """
        return self.transition_function[state][symbol]

    def _validate_transition(self, state_i, state_o, char) -> bool:
        """Validates the states and character from the transition function.

        Args:
            state_i: The state to transition from,
            state_o: The state to transition to
            char: The character on which transition from state_i to state_o
                occurs.

        Returns:
            bool: Whether the states are valid or not.
        """

        # Makes sure the states are valid and that the character is in the
        # alphabet.
        if (
            not (self._validate_state(state_i) and self._validate_state(state_o))
            or char not in self.alphabet
        ):
            return False
        
        return True

    def _validate_accept_states(self, accept_states) -> bool:
        """Validates accept states and saves them to the class dictionary.

        Args:
            accept_states: List of accept states (strings)

        Returns:
            bool: whether the accept states were validated
        """
        for state in accept_states:
            if not self._validate_state(state):
                return False
            self.accept_states[state] = None

        return True

    def _store_transition(
        self,
        state_from: str,
        state_to: str,
        transition_char: str,
    ) -> None:
        """
        Stores a transition in the class transition function dictionary. 

        Args:
            states_dict: The dictionary containing the transitions.
            state_from: The state to transition out of
            state_to: The state to transition to
            transition_char: The character with which the transition occurs.
        """
        # If there doesn't exist an entry for the source state, create it,
        # otherwise add to the existing one.
        if state_from not in self.transition_function:
            self.transition_function[state_from] = {
                transition_char: state_to,
            }
        else:
            self.transition_function[state_from][transition_char] = (
                state_to
            )

    def _validate_state(self, state: str) -> bool:
        if not state or not state.isnumeric():
            return False
        state = int(state)
        if not 1<=state<=self.number_of_states:
            return False

        return True

    def _read_dfa_data_from_file(self, filename: str) -> None:
        """Reads DFA data from a file into instance variables.

        Args:
            filename: the name of the file.

        Raises:
            FileFormatError if the file does not have a correct format.
        """
        dfa_file = open(filename, 'r')
        num_of_states = dfa_file.readline().strip()
        # Makes sure the line is not empty and that it's a number
        if not num_of_states.isnumeric() or not num_of_states:
            raise FileFormatError
        self.number_of_states = int(num_of_states)

        alphabet_line = dfa_file.readline().strip()
        for ch in alphabet_line:
            self.alphabet.append(ch)

        transition_data = dfa_file.readline().strip().split()

        while(len(transition_data) == 3):
            source_state, character, dest_state = transition_data
            quote_stripped_char = character.replace('\'', '')

            # Validates that each transition is correct
            if not self._validate_transition(
                state_i=source_state,
                state_o=dest_state,
                char=quote_stripped_char,
            ):
                raise FileFormatError

            # Stores the transitions
            self._store_transition(
                state_from=source_state,
                state_to=dest_state,
                transition_char=quote_stripped_char
            )

            transition_data = dfa_file.readline().strip().split()

        # The start state line is immediately after the transition data, so we
        # use the line scanned into 'transition_data' that ended the while loop
        start_state = transition_data[0]
        if not self._validate_state(start_state):
            raise FileFormatError
        self.start_state = start_state

        accept_states = dfa_file.readline().strip().split()
        if not self._validate_accept_states(accept_states):
            raise FileFormatError
        if dfa_file.readline():
            raise FileFormatError

    def simulate(self, str) -> bool:
        """
        Returns True if str is in the language of the DFA,
        and False if not.

        Assumes that all characters in str are in the alphabet 
        of the DFA.
        """
        curr_state = self.start_state
        for ch in str:
            next_state = self.transition_function[curr_state][ch]
            curr_state = next_state
        return curr_state in self.accept_states


if __name__ == "__main__":
    # You can run your dfa.py code directly from a
    # terminal command line:

    # Check for correct number of command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 pa1.py dfa_filename str")
        sys.exit(0)

    dfa = DFA(filename = sys.argv[1])
    str = sys.argv[2]
    ans = dfa.simulate(str)
    if ans:
        print(f"The string {str} is in the language of the DFA")
    else:
        print(f"The string {str} is in the language of the DFA")

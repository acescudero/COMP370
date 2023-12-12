import dfa  # imports your DFA class from pa1

import collections
from typing import Any, Dict, IO, List, Text


class NFA:
	""" Simulates an NFA """

	def __init__(self, nfa_filename = None):
		'''
		Initializes NFA from the file whose name is
		nfa_filename.  (So you should create an internal representation
		of the nfa.)
		'''
		if nfa_filename:
			self.alphabet = []
			self.number_of_states = None
			self.transition_function = {}
			self.start_state = None
			self.accept_states = {}
			self._read_nfa_data_from_file(nfa_filename)

	def _store_transition(
		self,
		state_from: str,
		state_to: str,
		transition_char: str,
		transition_dict: Dict,
	) -> None:
		'''
		Stores a transition in the class transition function dictionary. 

		Args:
			states_dict: The dictionary containing the transitions.
			state_from: The state to transition out of
			state_to: The state to transition to
			transition_char: The character with which the transition occurs.
		'''
		# If there doesn't exist an entry for the source state, create it,
		# otherwise add to the existing one.
		if state_from not in transition_dict:
			transition_dict[state_from] = {
				# It's possible to transition to different states on one symbol
				# so we need to keep a set of states rather than just one state
				# as we would do with NFAs.
				transition_char: {state_to: None},
			}
		else:
			# If there exists an entry for the state, it's possible that there
			# doesn't exist an entry for the transition character, so we must
			# check and create an entry if needed.
			if transition_char not in transition_dict[state_from]:
				transition_dict[state_from][transition_char] = {
					state_to: None
				}
			else:
				transition_dict[state_from][transition_char][state_to] = None

	def _get_transition(self, state: str, symbol: str) -> Dict[str, Any]:
		'''Returns the set of states a state can transition to on a symbol.'''
		return (
			self.transition_function[state].get(symbol, {})
			if state in self.transition_function else {}
		)

	def _extract_alphabet_from_line(self, line: str) -> List[str]:
		'''Extracts individual characters from a string.'''
		alphabet_list = []
		for ch in line:
			alphabet_list.append(ch)
		return alphabet_list

	def _extract_nfa_data_from_file(self, file: IO[Text]) -> Dict[str, Any]:
		'''Reads NFA data from a given file object.'''
		num_of_states = int(file.readline().strip())
		alphabet_line = file.readline().strip()
		alphabet = self._extract_alphabet_from_line(alphabet_line)

		# First line of the transition data
		transition_line = file.readline().strip()
		transition_dictionary = {}
		while (transition_line):
			transition_data = transition_line.split()
			source_state, character, dest_state = transition_data
			quote_stripped_char = character.replace('\'', '')

			# Stores the transitions
			self._store_transition(
				state_from=source_state,
				state_to=dest_state,
				transition_char=quote_stripped_char,
				transition_dict=transition_dictionary
			)

			transition_line = file.readline().strip()

		start_state = file.readline().strip()
		self.start_state = start_state
		accept_states_line = file.readline().strip().split()
		accept_states = (
			{state:None for state in accept_states_line} if accept_states_line else None
		)

		# Returns NFA data in the form of a dictionary for easy use.
		data_dict = {
			'num_of_states': num_of_states,
			'alphabet': alphabet,
			'transition_dict': transition_dictionary,
			'start_state': start_state,
			'accept_states': accept_states,
		}
		return data_dict



	def _read_nfa_data_from_file(self, filename: str) -> None:
		'''Reads data from the file with given filename and update NFA object.'''
		nfa_file = open(filename, 'r')
		data = self._extract_nfa_data_from_file(nfa_file)
		self.number_of_states = data['num_of_states']
		self.alphabet = data['alphabet']
		self.transition_function = data['transition_dict']
		self.start_state = data['start_state']
		self.accept_states = data['accept_states']

	def _get_epsilon_closure(
		self, state: str,
	) -> Dict[str, Any]:
		"""Finds the epsilon closure for a given state.

		Args:
			state: The state for which we wish to find the epsilon closure.
				Must be a valid state.

		Returns:
			dict: A dictionary (set) containing the states that represent the
				epsilon closure of the given state.
    """
		states_seen = {}
		queue = collections.deque()
		queue.append(state)
		while queue:
			curr_state = queue.popleft()
			states_seen[curr_state] = None
			# Handle cases where a state does not go anywhere, meaning it was
			# not added to the transition function when reading from the nfa
			# file.
			epsilon_transitions = (
				self.transition_function[curr_state].get('e', None)
				if curr_state in self.transition_function else None
			)
			if epsilon_transitions:
				for transition_state in epsilon_transitions.keys():
					if transition_state not in states_seen:
						queue.append(transition_state)

		return states_seen

	def _get_transition_for_states_set(
		self,
		set_of_states: Dict[str, Any],
		symbol: str
	) -> Dict[str, Any]:
		'''Gets all transitions on a character for a set of sates.

		Args:
			set_of_states: The set of states to transition from.

		Returns:
			a dictionary containing all the possible states that can be
				transitioned to from every state in the given set of states on
				the given symbol.
		'''
		dest_states = {}
		for state in set_of_states.keys():
			symbol_transition = self._get_transition(state, symbol)
			if symbol_transition:
				dest_states.update(symbol_transition)

		return dest_states

	def _get_epsilon_closure_for_states_set(
		self,
		set_of_states: Dict[str, Any],
	) -> Dict[str, Any]:
		'''Gets the epsilon closure for a set of states.

		Args:
			set_of_states: The set of states to work with.

		Returns:
			A dictionary containing the sets that form the epsilon closure of
				the set of states given.
		'''
		e_states = {}
		for state in set_of_states.keys():
			e_closure = self._get_epsilon_closure(state)
			if e_closure:
				e_states.update(e_closure)

		return e_states

	def _generate_int_mapping(
			self,
			start_state: Dict[str, Any],
			reverse: bool = False
	) -> Dict[Any, Any]:
		'''Generates int mapping for start state and reject state.

		Args:
			start_state: The set of NFA states that represent the DFA start state
				state.
			reverse: Whethe the mapping should be set to integer (False) or
				integer to set (True)

		Returns:
			A dictionary containing the mapping.
		'''
		if reverse:
			# Int to set mapping (reverse)
			mapping = {
				1: frozenset(),
				2: frozenset(start_state),
			}
			return mapping
		# Set to int mapping
		mapping = {
			frozenset(): 1,
			frozenset(start_state): 2,
		}
		return mapping


	def _nfa_conversion(self, start_state: Dict[str, Any], dfa: dfa.DFA):
		'''Performs conversion from NFA to DFA.

		Args:
			start_state: Set of states of the NFA that represent the start
				state of the DFA.
			dfa: The DFA object that will store the conversion.
		'''
		queue = collections.deque()
		queue.append(start_state)
		# Since we're adding the reject state beforehand and its int mapping is
		# 1, the start state, which is the first state we handle will map to 2.
		dfa.start_state = 2
		dfa.transition_function = {}
		states_handled = []
		# will map a set of states, e.g. {1,3} to an integer which will be the
		# corresponding state of the DFA. Originally, it contains the empty set
		# representing the reject state in the DFA and the start state for
		# simplicity in the DFA generation.
		dfa_state_int_mapping = self._generate_int_mapping(start_state)
		# Similarly, will map an integer corresponding to the state of the DFA
		# to a set of states from the NFA.
		dfa_state_int_mapping_reverse = (
			self._generate_int_mapping(start_state, reverse=True)
		)
		# accumulator variable for mapping the states, 1 will be correspond to
		# the empty set, which is the reject state as defined previously.
		next_state_id = 2
		dfa.number_of_states = 1
		found_empty = False

		while queue:
			curr_state_set = queue.popleft()
			# Make sure we're not handling set of states we  have already seen.
			if curr_state_set not in states_handled:
				transitions = {}
				for symbol in self.alphabet:
					dest_states = {}
					transition_on_symbol = (
						self._get_transition_for_states_set(
							curr_state_set, symbol
						)
					)
					transition_e_closure = (
						self._get_epsilon_closure_for_states_set(
							transition_on_symbol
						)
					)
					dest_states.update(transition_on_symbol)
					dest_states.update(transition_e_closure)
					transitions[symbol] = frozenset(dest_states)
					# If the destination state is the empty set, we don't need
					# to handle it, it's already handled in the pre-definition
					# of the empty set as state 1 that goes to itself on every
					# character of the alphabet.
					if dest_states:
						queue.append(dest_states)
					else:
						found_empty = True

				frozen_set = frozenset(curr_state_set)
				# Determines what the value of next_state_id should be. This is
				# used in the transition function, next_state_id will be an int
				# that corresponds to a set of states from the NFA. If we have
				# previously recorded this mapping, we just grab the int value
				# from the mapping dictionary.
				if frozen_set in dfa_state_int_mapping:
					set_id = dfa_state_int_mapping[frozen_set]
				else:
					set_id = next_state_id
					dfa_state_int_mapping[frozen_set] = set_id
					dfa_state_int_mapping_reverse[set_id] = frozen_set

				next_state_id+=1
				states_handled.append(curr_state_set)
				dfa.transition_function[set_id] = transitions
				dfa.number_of_states += 1

		if not found_empty:
			# Since the empty set was added beforehand, it we couldn't find a
			# transition to it when generating the DFA, then it should be
			# removed from the mapping, number of states should be decreased by
			# 1, and the start state as well.
			del dfa_state_int_mapping[frozenset()]
			del dfa_state_int_mapping_reverse[1]
			dfa.number_of_states -= 1
			dfa.start_state -= 1
		else:
			# If we did find a transition to the empty set when generating the
			# DFA, then we add the transitions on every symbol of the alphabet
			# for the empty set, and since it's the reject state it goes to
			# itself on all symbols.
			for symbol in self.alphabet:
				if 1 in dfa.transition_function:
					dfa.transition_function[1][symbol] = 1
				else:
					dfa.transition_function[1] = {symbol: 1}

		return dfa_state_int_mapping, dfa_state_int_mapping_reverse

	def _generate_shifted_transition_value(self, value: Dict[Any, int]) -> Dict[Any, int]:
		'''Shifts a dictionary's integer value down by 1.

		Args:
			value: The dictionary containing Any: int pairs

		Returns:
			Dict[Any, int]: The generated dictionary with shifted values.
		'''
		new_values_dict = {}
		for key in value.keys():
			new_values_dict[key] = value[key]-1
		return new_values_dict

	def _generate_shifted_keys_dict(
		self,
		transition_function: Dict[int, Dict[str, int]],
		should_shift_values: bool = True
	) -> Dict[int, Dict[str, int]]:
		'''Shifts a dictionary's integer keys and/or values down by 1.

		Args:
			transition_function: a dictionary of int, Dict[str, int] pairs. The
				key must be an integer, which will be shifted down by 1.
			should_shift_values: whether the values, i.e the integer in
				Dict[str,int] should be shifted as well. False is useful for
				dictionaries that may not have Dict[str, int] as values.

		Returns:
			Dict[int, Dict[str, int]]: The resulting dicitonary with keys or
				values shifted.
		'''
		new_transition_function = {}
		for state in transition_function.keys():
			new_state = state-1
			new_value = (
				self._generate_shifted_transition_value(transition_function[state])
				if should_shift_values else transition_function[state]
			)
			new_transition_function[new_state] = new_value
		return new_transition_function


	def _finalize_dfa(
		self,
		dfa: dfa.DFA,
		int_mapping: Dict[frozenset, int],
		int_mapping_reverse: Dict[frozenset, int]
	) -> None:
		'''Finalizes the DFA object.

		Args:
			dfa: The DFA to work with.
			int_mapping: The NFA states set (set) to DFA state (int) mapping.
			int_mapping_reverse:  The DFA state (int) to NFA states set (set)
				mapping.
		'''
		dfa.alphabet = self.alphabet
		dfa.accept_states = {}
		for state in dfa.transition_function.keys():
			found_accept_state = False
			# Since the DFA was generated with the transition function being in
			# the following format: {int: {str: frozenset}}, where the int is
			# the value that represents a set of states in the NFA in the
			# mapping, we use the mapping dictionary to get this set of states.
			# This allows us to know which states of the DFA are accept states,
			# i.e. all set of states that contain at least 1 accept state of the
			# NFA.
			corresponding_states_set = int_mapping_reverse[state]
			for nfa_state in corresponding_states_set:
				if nfa_state in self.accept_states:
					dfa.accept_states[state] = None
					found_accept_state = True
					break
			if state != 1:
				for symbol in self.alphabet:
					# Conver the destination states in the transition functions
					# to their corresponding int mapping.
					state_set = dfa.transition_function[state][symbol]
					int_state = int_mapping[state_set]
					dfa.transition_function[state][symbol] = int_state
			if found_accept_state:
				continue
		# Since the reject state is added beforehand and deleted if no state
		# transitioned to it, we need to shift all states by -1 since the
		# reject state is always 1.
		if 1 not in dfa.transition_function:
			shifted_transition_function = self._generate_shifted_keys_dict(dfa.transition_function)
			dfa.transition_function = shifted_transition_function
			shifted_accept_states = self._generate_shifted_keys_dict(dfa.accept_states, False)
			dfa.accept_states = shifted_accept_states

	def to_DFA(self) -> dfa.DFA:
		"""
		Converts the "self" NFA into an equivalent DFA object
		and returns that DFA.  The DFA object should be an
		instance of the DFA class that you defined in pa1. 
		The attributes (instance variables) of the DFA must conform to 
		the requirements laid out in the pa2 problem statement (and that are the same
		as the DFA file requirements specified in the pa1 problem statement).

		This function should not read in the NFA file again.  It should
		create the DFA from the internal representation of the NFA that you 
		created in __init__.
		"""
		new_dfa = dfa.DFA()
		new_dfa.transition_function = {}
		new_dfa.number_of_states = 0
		start_state_e_closure = self._get_epsilon_closure(self.start_state)
		int_mapping, int_mapping_reverse = self._nfa_conversion(start_state_e_closure, new_dfa)
		self._finalize_dfa(new_dfa, int_mapping, int_mapping_reverse)

		return new_dfa

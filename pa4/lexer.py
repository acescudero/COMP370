import regex
import copy

from dfa import DFA
from typing import Dict, List, Tuple


class InvalidToken(Exception):
	""" 
	Raised if while scanning for a token,
	the lexical analyzer cannot identify 
	a valid token, but there are still
	characters remaining in the input file
	"""
	pass


class TokenValue:
	def __init__(self, dfa: DFA, type: str = '', order: int = 0):
		self.dfa = dfa
		self.type = type
		self.order = order


class Lex:
	def __init__(self, regex_file, source_file):
		"""
		Initializes a lexical analyzer.  regex_file
		contains specifications of the types of tokens
		(see problem assignment for format), and source_file
		is the text file that tokens are returned from.
		"""
		self.alphabet = []
		self.generated_dfas = {}
		self.source_file_data = ''
		try:
			self._initialize_from_file(regex_file)
			self.source_file_data = (
				self._read_source_file(source_file)
			)
		except Exception as e:
			print(e)

	def _pre_process_regex(
		self,
		token_type: str,
		regex_str: str,
		last_num_token: int
	) -> None:
		'''Pre-processes a regular expression by constructing its DFA.

		Args:
			token_type: The type of token, i.e. token identifier.
			regex_str: The regular expression string
			last_num_token: How many regex's have been pre-processed prior to
				this one. This is determined by the order in which they appear
				in the definition file.
		'''
		params_for_regex = {
			'alphabet': self.alphabet,
			'regex_string': regex_str
		}
		reg = regex.RegEx(params=params_for_regex, init_from_params_dict=True)
		reg_dfa = reg.nfa.to_DFA()
		token_value = TokenValue(
			dfa=reg_dfa,
			type=token_type,
			order=last_num_token
		)
		self.generated_dfas[token_type] = token_value

	def _read_source_file(self, filename: str) -> str:
		'''Reads a source file into a string removing newline characters.'''
		file = open(filename, 'r')
		# Further in the code spaces are treated as token enders along with
		# the newline characters. We could instead add an additional check
		# to see if the character is '\n' in the mentioned line but this would
		# require replacing '\n' with the empty string in the function
		# next_token() so it's simpler to just turn all newline characters into
		# spaces, that way they're all treated the same way without need for
		# additional string replacing.
		content = file.read().replace('\n', ' ')
		return content


	def _initialize_from_file(self, filename: str) -> None:
		'''Initializes instance variables from definition file.'''
		file = open(filename, 'r')
		alphabet_line = file.readline().strip()
		# Removing quotes
		alphabet_string = alphabet_line[1:-1]
		self.alphabet = [ch for ch in alphabet_string]
		next_line = file.readline().strip()
		last_num_token = 0
		while next_line:
			token_type, token_string = next_line.split()
			# Removing quotes
			token_string = token_string[1:-1]
			# As we read each regex, we convert it to its equivalent DFA and
			# save them to an instance variable.
			self._pre_process_regex(token_type, token_string, last_num_token)
			next_line = file.readline().strip()
			last_num_token += 1

	def _multiple_token_decider(self, tokens: List[TokenValue]) -> str:
		'''Determines the token with the lowest order in the definition file.

		Args:
			tokens: a list of TokenValue objects

		Returns:
			string: the token type with the lowest order. Recall that the
			'order' value in a TokenValue object represents how early in
			the token definition file it appears, with 0 being the very
			first one.'''
		token_val = None
		lowest_order = 10000000
		for token in tokens:
			token_order = token.order
			if token_order < lowest_order:
				lowest_order = token_order
				token_val = token
		return token_val

	def _analyze_input(self, input: str) -> Tuple[TokenValue, str, int]:
		'''Determines the token type, longest matched string, and its length.

		Args:
			input: The input string

		Returns:
			tuple: Contains
				1) the TokenValue object that corresponds to the
				token type that matched the longest substring in the input. 
				2) The substring that was matched
				3) The length of this substring
    '''
		accepting_token_values = []
		final_longest_match_str_len = 0
		dfas = self.generated_dfas

		for _, token_value in dfas.items():
			dfa = token_value.dfa
			curr_state = dfa.start_state
			longest_match_str_len = 0
			reached_accept_state = False
			for i in range(len(input)):
				curr_char = input[i]
				if curr_char == ' ':
					if reached_accept_state:
						break
					else:
						continue
				next_state = dfa.transition(
					state=curr_state,
					symbol=curr_char
				)
				# In the previous PA, if there is a reject state, i.e. a state
				# we never leave, it will always be state 1. We are guaranteed
				# that every DFA generated from the RegEx -> NFA -> DFA
				# conversion will have a reject state. Note that a reject state
				# is different from a non-accepting state. We can exit a non-
				# accepting state, but once we get to a reject state we can't
				# leave.
				if next_state == 1:
					break
				curr_state = next_state
				if next_state in dfa.accept_states:
					# Whenever we reach an accept state, the length of the
					# longest matched substring is equal to i+1. For example,
					# if the input is 'abc' and the computation accepts at b,
					# the length of the current longest accept state is 2, and
					# we're at index i = 1 so the length is i+1.
					longest_match_str_len = i+1
					reached_accept_state = True
			if reached_accept_state:
				# If the current dfa accepts a substring of the input that
				# is shorter than the substring accepted by a previous dfa,
				# then we don't need to do anything with it because we need
				# to return the longest matching substring.
				if longest_match_str_len > final_longest_match_str_len:
					accepting_token_values = [token_value]
					final_longest_match_str_len = longest_match_str_len
				elif longest_match_str_len == final_longest_match_str_len:
					accepting_token_values.append(token_value)
					final_longest_match_str_len = longest_match_str_len
		num_accepting_tokens = len(accepting_token_values)
		result_token = (
			accepting_token_values[0]
			if num_accepting_tokens == 1 else
			self._multiple_token_decider(accepting_token_values)
		)
		# We can assume that if the computation for a DFA entered an accept
		# state at any point, then if it also enters a reject state at some
		# point after it entered an acept staet, the state before the reject
		# state is an accept state, so final_longest_matched_str_len will
		# determine where we need to cut the input, i.e. where the longest
		# matched substring ends.
		matched_str = input[:final_longest_match_str_len]
		return result_token, matched_str, final_longest_match_str_len

	def next_token(self):
		"""
		Returns the next token from the source_file.
		The token is returned as a tuple with 2 item:
		the first item is the name of the token type (a string),
		and the second item is the specific value of the token (also
		as a string).
		Raises EOFError exception if there are not more tokens in the
		file.
		Raises InvalidToken exception if a valid token cannot be identified,
		but there are characters remaining in the source file.
		"""
		if not self.source_file_data:
			raise EOFError
		next_token, matched_str, str_len = self._analyze_input(self.source_file_data)
		self.source_file_data = self.source_file_data[str_len:]
		check_str = self.source_file_data.replace(' ', '')
		if not check_str:
			self.source_file_data = check_str
		if next_token:
			return next_token.type, matched_str.replace(' ', '')
		else:
			raise InvalidToken

if __name__ == "__main__":
	num = 1   # can replace this with any number 1, ... 20.
			  # can also create your own test files.
	reg_ex_filename = f"regex{num}.txt" 
	source_filename = f"src{num}.txt"
	lex = Lex(reg_ex_filename, source_filename)
	try:
		while True:
			token = lex.next_token()
			print(token)

	except EOFError:
		pass
	except InvalidToken:
		print("Invalid token")

from dfa import DFA
from nfa import NFA
from tree import Node, SimpleNFA, depth_first

from helper_functions import *
from typing import List, Tuple


class InvalidExpression(Exception):
	pass


def _check_operator_prescedence(operator1: str, operator2: str):
	'''Compares precedence between two operators.

	Args:
		operator1: the first operator to compare
		operator2: the second operator to compare

	Returns:
		the operator with higher precedence
	'''
	prescedence_mapping = {
		'(': 3,
		')': 3,
		'*': 2,
		'∘': 1,
		'|': 0,
	}
	op1_pres = prescedence_mapping[operator1]
	op2_pres = prescedence_mapping[operator2]
	if op2_pres >= op1_pres:
		return operator2
	else:
		return operator1


class RegEx:
	def __init__(self, filename: str):
		'''
		Initializes regular expression from the file "filename"
		'''
		self.alphabet = []
		self.regex_string = ''
		self.invalid = False
		self.operator_operand_mapping = {
			'∘': 2,
			'*': 1,
			'|': 2,
		}
		try:
			self._initialize_from_file(filename) 
		except IOError as e:
			print(e)
		try:
			operand_stack, operator_stack = self._parse_regex(
				regex=self.regex_string,
				alphabet=self.alphabet
			)
			self.root_node = (
				self._empty_operator_stack(operand_stack, operator_stack)
			)
			self.nfa = self.to_nfa()
		except InvalidExpression:
			self.invalid = True


	def _empty_operator_stack(
		self,
		operand_stack: List[Node],
		operator_stack: List[str]
	) -> Node:
		'''Finalizes the abstract syntax tree by emptying the operator stack.

		Args:
			operand_stack: the stack containing operand nodes.
			operator_stack: the stack containing operators

		Returns:
			Node: the root of the abstract syntax tree.
		'''
		while operator_stack:
			operator = operator_stack.pop()
			if operator == '(':
				raise InvalidExpression
			operator_node = Node(operator, [], 1)
			num_operands = self.operator_operand_mapping[operator]
			if len(operand_stack) < num_operands:
				raise InvalidExpression
			for _ in range(num_operands):
				operand = operand_stack.pop()
				operator_node.add_child(child=operand, insert=True)
			operand_stack.append(operator_node)
		operand_root = operand_stack.pop()
		return operand_root


	def _initialize_from_file(self, filename: str):
		'''Initializes the regular expression class from a definition file.'''
		f = open(filename, 'r')
		alphabet_line = f.readline()
		alph_quote_index_1 = alphabet_line.find('"') + 1
		alph_quote_index_2 = alphabet_line.rfind('"')
		alphabet_str = alphabet_line[alph_quote_index_1: alph_quote_index_2]
		alphabet_list = [ch for ch in alphabet_str]
		self.alphabet = alphabet_list

		regex_line = f.readline()
		regex_quote_index_1 = regex_line.find('"') + 1
		regex_quote_index_2 = regex_line.rfind('"')
		regex_str = regex_line[regex_quote_index_1: regex_quote_index_2]
		self.regex_string = regex_str

		f.close()


	def _parse_regex(
		self,
		regex: str,
		alphabet: List[str]
	) -> Tuple[List[Node], List[str]]:
		'''Parses a regular expression.

		Args:
			regex: The regular expression string
			alphabet: The alphabet for the regular expression

		Returns:
			tuple: the operand stack and the operator stack
		'''
		operand_stack = []
		operator_stack = []
		special_symbols = ['(', ')', '*', '|', 'N']
		tokenized_regex = tokenize(regex, alphabet)
		tokenized_regex_with_concat = insert_concat(tokenized_regex, alphabet)
		for i in range(len(tokenized_regex_with_concat)):
			token = tokenized_regex_with_concat[i]
			# We have a base case:
			#	- token is in alphabet and it's not a special symbol, so we
			#		have a literal symbol
			# 	- length of the token is > 1. This handles special characters
			# 		that are escaped
			# 	- we have a special case with 'e' and 'N' because they are base
			# 		cases for the abstract syntax tree but they are not symbols
			if (
				(token in self.alphabet and token not in special_symbols)
				or len(token)>1 or token == 'e' or token == 'N'
			):
				is_symbol = token != 'e' and token != 'N'
				# An escaped character will be tokenizes with the '\' included
				# so we just grab the last character of the token.
				if len(token) > 1:
					token = token[-1]
				operand_node = Node(value=token, type=0, is_symbol=is_symbol)
				operand_stack.append(operand_node)
			elif token == '(':
				operator_stack.append(token)
			elif token == ')':
				if operator_stack:
					operator = operator_stack.pop()
					while operator != '(':
						operator_node = Node(operator, [], 1)
						num_operands = self.operator_operand_mapping[operator]
						for _ in range(num_operands):
							operand = operand_stack.pop()
							operator_node.add_child(child=operand, insert=True)
						operand_stack.append(operator_node)
						if operator_stack:
							operator = operator_stack.pop()
						else:
							raise InvalidExpression
			elif (
				token == '*'
				or
				token == '|'
				or token == '∘'
			):
				if operator_stack:
					top = operator_stack[-1]
					higher_pres = _check_operator_prescedence(token, top)
					while higher_pres == top and top != '(' and operator_stack:
						operator = operator_stack.pop()
						operator_node = Node(value=operator, type=1)
						num_operands = (
							self.operator_operand_mapping[operator]
						)
						if len(operand_stack) < num_operands:
							raise InvalidExpression
						for _ in range(num_operands):
							operand = operand_stack.pop()
							operator_node.add_child(child=operand, insert=True)
						operand_stack.append(operator_node)
						if operator_stack:
							top = operator_stack[-1]
							higher_pres = _check_operator_prescedence(token, top)
						else:
							break
					operator_stack.append(token)
				else:
					operator_stack.append(token)
		return operand_stack, operator_stack

	def _finalize_simple_nfa(self, simple_nfa: SimpleNFA) -> NFA:
		'''Converts a SimpleNFA class to an NFA class.'''
		final_nfa = NFA()
		final_nfa.alphabet = self.alphabet
		final_nfa.number_of_states = simple_nfa.last_state
		final_nfa.transition_function = simple_nfa.transition_function
		final_nfa.start_state = simple_nfa.start_state
		final_nfa.accept_states = simple_nfa.accept_states
		return final_nfa

	def to_nfa(self) -> NFA:
		"""
		Returns an NFA object that is equivalent to 
		the "self" regular expression
		"""
		new_nfa = NFA()
		new_nfa.accept_states = []
		new_nfa.transition_function = {}
		new_nfa.alphabet = self.alphabet
		# TODO(aescudero): Push code for depth first
		simple_nfa = depth_first(self.root_node)
		final_nfa = self._finalize_simple_nfa(simple_nfa)
		return final_nfa

	def simulate(self, str):
		"""
		Returns True if str is in the languages defined
		by the "self" regular expression
		"""
		if self.invalid:
			return False
		dfa = self.nfa.to_DFA()
		result = dfa.simulate(str)
		return result


if __name__ == '__main__':
	regex_filename = "regex21.txt"

	str_filename = "str21.txt"
	correct_filename = "correct21.txt"


	regex = RegEx(regex_filename)
	correct_file = open(correct_filename)
	correct_list =  [True if result == "true" else False for result in correct_file.read().split()]

	str_file = open(str_filename)

	strings = []
	for str in str_file:
		strings.append(str[str.find('"') + 1:str.rfind('"')])

	for i in range(len(strings)):
		print(f"String is {strings[i]}")
		print(f"Correct = {correct_list[i]}")
		print(f"My ans = {regex.simulate(strings[i])}")

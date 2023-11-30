import re

from typing import List


def insert_concat(tokens: List[str], alphabet: List[str]) -> List[str]:
    '''Inserts the concat symbol '∘' in a tokenized regex when it's implied.

    Args:
        tokens: The tokenized regular expression.
        alphabet: The alphabet for the regular expression.

    Returns:
        list: the tokenized regular expression with the concat symbol inserted
    '''
    special_symbols = ['(', ')', '*', '|']
    tokens_with_concat = []
    # For the type of regular expressions that we are dealing with we have
    # concatenation in the following cases:
    #   - Two symbols (either literal or escaped), e.g. ab or a\e
    #   - A symbol and an operator that works to the opposite direction of
    #       where the symbol is. For example in a( the symbol is at the left
    #       and the operator works to the right so there is concat. Similarly,
    #       in *a the symbol is at the right and the operator works to the left
    #   - Two operators that work in opposite directions, e.g. )( or )*
    # Note that the operators must be unidirectional. For instance, | can never
    # be concatenated with anything (unless escaped) because it works in both
    # directions, the same with ∘ so when we inserted we are guaranteed to not
    # add more implied concatenations than in the original tokenized regex.
    for i in range(len(tokens)):
        token = tokens[i]
        tokens_with_concat.append(token)
        if i + 1 < len(tokens):
            next_token = tokens[i + 1]
            # We find a literal symbol or an escaped symbol
            if (len(token) > 1 or (token in alphabet and token not in special_symbols)):
                # If the next token is also a literal symbol or escaped symbol,
                # or if it's a right parenthesis then we have concat.
                if (
                    len(next_token) > 1
                    or (
                        next_token in alphabet
                        and next_token not in special_symbols
                    )
                    or next_token == '('
                ):
                    tokens_with_concat.append('∘')
            elif token == ')':
                # Check if next token is a literal, an escaped sequence, or an opening parenthesis
                # If the next token is a literal symbol or escaped symbol, or
                # if it's a left parenthesis, we have concat.
                if (
                    len(next_token) > 1
                    or (
                        next_token in alphabet
                        and next_token not in special_symbols
                    )
                    or next_token == '('):
                    tokens_with_concat.append('∘')  # Insert concatenation operator
            elif token == '*':
                # If the next token is a literal symbol or escaped symbol,
                # or a left parenthesis we have concat.
                if (
                    len(next_token) > 1
                    or (
                        next_token in alphabet
                        and next_token not in special_symbols
                    )
                    or next_token == '('
                ):
                    tokens_with_concat.append('∘')
    return tokens_with_concat


def tokenize(expression: str, alphabet: List[str]) -> List[str]:
    '''Tokenizes a regular expression string.

    Args:
        expression: the regular expression string.
        alphabet: the alphabet for the regular expression

    Returns:
        list: the tokenized regular expression
    '''
    token_pattern = (
        r'\\[N\|\(\)\*]|\\\\|['
        + 'eN\|\*\(\)'
        + ']|['
        + ''.join(re.escape(char) for char in alphabet if char not in 'eN|*()')
        + ']'
    )

    token_regex = re.compile(token_pattern)

    tokens = token_regex.findall(expression)

    return tokens

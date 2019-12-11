"""
Returns the most similar word from given input
using given dictionary
"""


class Correctness:
    "Returns the most similar word from given input"

    def __init__(self, vocabulary, length_limit=1, char_limit=2):
        self._vocabulary = []
        self.vocabulary = vocabulary
        self._length_limit = length_limit
        self._char_limit = char_limit

    @property
    def vocabulary(self):
        "returns the vocabulary dictionary"
        return self._vocabulary

    @vocabulary.setter
    def vocabulary(self, value):
        "adds the given input into vocabulary dictionary"
        if isinstance(value, str):
            self._vocabulary.append(value)
        elif isinstance(value, (list, tuple, dict, set)):
            self._vocabulary.extend(list(value))
        else:
            raise ValueError(
                "type {!r} is not supported".format(
                    value.__class__.__name__
                )
            )

    def add_vocabulary(self, value):
        "adds the given input into vocabulary dictionary"
        self.vocabulary = value

    def remove_vocabulary(self, value, ignore_errors=True):
        "removes the given word from vocabulary dictionary"
        try:
            self._vocabulary.pop(self._vocabulary.index(value))
        except ValueError:
            if not ignore_errors:
                raise

    def remove_vocabularys(self, values, ignore_errors=True):
        "removes the given words from vocabulary dictionary"
        for value in values:
            self.remove_vocabulary(value, ignore_errors=ignore_errors)

    def _filter_by_length(self, length):
        for choise in self.vocabulary:
            if length-self._length_limit <= len(choise) <= length+self._length_limit:
                yield choise

    def _filter_by_char(self, text, choises):
        for choise in choises:
            similar_chars = set()
            for char in text:
                if char in choise:
                    similar_chars.add(char)
            similarity = len(similar_chars)
            if len(set(text)) - similarity < self._char_limit:
                yield choise, similarity / len(text)

    def spell_check(self, text):
        "finds the most similar word"
        if text in self.vocabulary:
            return text

        possibles = self._filter_by_length(len(text))
        possibles = self._filter_by_char(text, possibles)
        max_rate = 0
        most_simiar = None
        for possible, rate in possibles:
            if rate > max_rate:
                max_rate = rate
                most_simiar = possible

        return most_simiar

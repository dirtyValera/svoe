from typing import Any


class Record:
    # Data record in data stream

    def __init__(self, value: Any):
        self.value = value
        self.stream = None

    def __repr__(self):
        return "Record({})".format(self.value)

    def __eq__(self, other):
        if type(self) is type(other):
            return (self.stream, self.value) == (other.stream, other.value)
        return False

    def __hash__(self):
        return hash((self.stream, self.value))

    def to_dict(self):
        return {
            'value': self.value
        }

class KeyRecord(Record):
    # Data record in a keyed data stream

    def __init__(self, key: Any, value: Any):
        super().__init__(value)
        self.key = key

    def __eq__(self, other):
        if type(self) is type(other):
            return (self.stream, self.key, self.value) == (
                other.stream,
                other.key,
                other.value,
            )
        return False

    def __hash__(self):
        return hash((self.stream, self.key, self.value))

    def to_dict(self):
        return {
            'key': self.key
            'value': self.value
        }

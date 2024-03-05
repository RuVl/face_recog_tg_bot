from random import random
from typing import Optional


class CancellationToken:
    __slots__ = ('_id', '_canceled', '_completed')

    def __init__(self, *, _canceled=False, _completed=False):
        self._id = random()

        self._canceled = _canceled
        self._completed = _completed

    def cancel(self):
        self._canceled = True

    def complete(self):
        self._completed = True

    @property
    def canceled(self) -> bool:
        return self._canceled

    @property
    def completed(self) -> bool:
        return self._completed

    def __eq__(self, other: Optional['CancellationToken']) -> bool:
        return other is not None and self._id == other._id

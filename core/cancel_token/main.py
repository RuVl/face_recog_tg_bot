class CancellationToken:
    def __init__(self, *, _canceled=False, _completed=False):
        self._canceled = _canceled
        self._completed = _completed

    def cancel(self):
        self._canceled = True
        self._completed = True

    def complete(self):
        self._completed = True

    @property
    def cancelled(self) -> bool:
        return self._canceled

    @property
    def completed(self) -> bool:
        return self._completed

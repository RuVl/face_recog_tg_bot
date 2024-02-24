from pydantic import BaseModel


class CancellationToken(BaseModel):
    is_canceled = False
    is_completed = False

    def cancel(self):
        self.is_canceled = True
        self.is_completed = True

    def complete(self):
        self.is_completed = True

    @property
    def cancelled(self) -> bool:
        return self.is_canceled

    @property
    def completed(self) -> bool:
        return self.is_completed

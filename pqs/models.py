import pendulum
from bloop import BaseModel, Column, String, Engine, ConstraintViolation
from bloop.ext.pendulum import DateTime


class Person(BaseModel):
    class Meta:
        stream = {
            "include": {"new", "old"}
        }
    id = Column(String, hash_key=True)
    name = Column(String)
    enqueued_at = Column(DateTime)
    served_at = Column(DateTime)

    @property
    def is_waiting(self):
        return self.served_at is None

    def enqueue(self, engine: Engine):
        # roll back the change on conditional put failure
        previous = self.enqueued_at
        self.enqueued_at = pendulum.now()
        try:
            engine.save(self, condition=NOT_EXIST & NOT_ENQUEUED)
            return True
        except ConstraintViolation:
            # User already exists
            self.enqueued_at = previous
            return False

    def serve(self, engine):
        previous = self.served_at
        self.served_at = pendulum.now()
        try:
            engine.save(self, condition=NOT_SERVED)
        except ConstraintViolation:
            self.served_at = previous

NOT_EXIST = Person.id.is_(None)
NOT_ENQUEUED = Person.enqueued_at.is_(None)
NOT_SERVED = Person.served_at.is_(None)
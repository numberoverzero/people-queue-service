from typing import Tuple

import pendulum
from bloop import (
    BaseModel,
    BloopException,
    Column,
    ConstraintViolation,
    Engine,
    Integer,
    MissingObjects,
    String,
)
from bloop.ext.pendulum import DateTime


class Person(BaseModel):
    class Meta:
        table_name = "pqs-person-id"
    id = Column(String, hash_key=True)
    position = Column(Integer)
Person.NOT_EXIST = Person.id.is_(None)
Person.NOT_ENQUEUED = Person.position.is_(None)


class QueueEntry(BaseModel):
    LAST_SEEN_ID = None

    class Meta:
        table_name = "pqs-queue-entry"
        stream = {
            "include": {"new", "old"}
        }
    position = Column(Integer, hash_key=True)
    id = Column(String)
    enqueued_at = Column(DateTime)
    served_at = Column(DateTime)
QueueEntry.NOT_EXIST = QueueEntry.position.is_(None)


def bind_all(engine: Engine) -> None:
    engine.bind(Person)
    engine.bind(QueueEntry)


def push(engine: Engine, id: str) -> Tuple[int, int]:
    """Returns (status, position) tuple.

    next_position should be a guess; always guess low, or misordering can occur.

    Position will be the reserved queue position, even if the user already existed."""

    # -1. Non-authoritative check for existing user.
    #     This doesn't guarantee the user doesn't exist, it just saves a lot of empty queue positions
    #     when a malicious actor tries to enqueue themselves many times.
    #     (Mitigation factor depends on )
    try:
        existing = engine.query(Person, key=Person.id==id).first()
        # If we don't hit an exception, person already exists
        return 409, existing.position
    except ConstraintViolation:
        # Probably doesn't exist, keep going
        pass

    # 0. Reserve a row in QueueEntry with the next queue position.
    #    Don't insert the id until we confirm that this user
    #    hasn't already been enqueued.
    entry = QueueEntry(
        position=0,
        enqueued_at=pendulum.now(),
        served_at=None
    )
    while True:
        try:
            engine.save(entry, condition=QueueEntry.NOT_EXIST)
        except ConstraintViolation:
            # TODO | can be much faster:
            # TODO | - use a binary walk from 0 until we hit a missing,
            # TODO | - then binary walk back to an existing,
            # TODO | - then use try save with increment of 1
            entry.position += 1
        else:
            break

    # 1. Now that we've reserved a row, try to build the id -> position mapping.
    #    Note that a failure here means the user is already queued, so we abort.
    #    Can't roll back the QueueEntry though, since another caller may have already
    #    advanced past us.
    person = Person(id=id, position=entry.position)
    try:
        engine.save(person, condition=Person.NOT_ENQUEUED)
    except ConstraintViolation:
        return 409, entry.position

    # 2. Success!  Finally, push the id into the QueueEntry.
    #    It's ok if this fails, because we can always rebuild the id from the Person table.
    entry.id = id
    try:
        engine.save(entry)
    except BloopException:
        # Can't be sure the entry is saved, but it's fine because we'll
        # be able to rebuild from the Person
        return 404, entry.position

    return 200, entry.position


def serve(engine: Engine, id: str) -> int:
    """200 success, 404 missing row, 409 already served"""
    # 0. Find the QueueEntry by Person
    person = Person(id=id)
    try:
        engine.load(person)
    except MissingObjects:
        return 404
    entry = QueueEntry(position=person.position)
    try:
        engine.load(entry)
    except MissingObjects:
        return 404

    # 1. Update the time the entry was served at.
    #    If the entry was already served, don't change the time.
    entry.served_at = pendulum.now()
    try:
        engine.save(entry, condition=QueueEntry.served_at.is_(None))
    except ConstraintViolation:
        # Already served, no change
        return 409
    else:
        return 200

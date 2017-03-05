import click
import sys
from pqs.scripts.config import build_engine, ENQUEUE_PROFILE_NAME
from pqs.models import Person

engine = build_engine(ENQUEUE_PROFILE_NAME)
engine.bind(Person)


def is_authenticated(id, **kwargs):
    # TODO
    return True


def enqueue(id, name, **kwargs):
    if not is_authenticated(id, **kwargs):
        return 401

    person = Person(id=id, name=name, enqueued_at=None, served_at=None)
    if not person.enqueue(engine):
        return 409

    return 200


@click.command("register")
@click.argument("id", required=True)
@click.argument("name", required=True)
def main(id, name):
    status = enqueue(id, name)
    if status != 200:
        sys.exit(str(status))

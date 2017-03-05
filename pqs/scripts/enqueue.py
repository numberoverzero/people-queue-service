import click
import sys
from pqs.scripts.config import build_engine, ENQUEUE_PROFILE_NAME
from pqs.models import Person

engine = build_engine(ENQUEUE_PROFILE_NAME)
engine.bind(Person)


def is_authenticated(id, **kwargs):
    # TODO
    return True


@click.command("register")
@click.argument("id", required=True)
@click.argument("name", required=True)
def main(id, name):
    if not is_authenticated(id): sys.exit("401")
    person = Person(id=id, name=name, enqueued_at=None, served_at=None)
    if not person.enqueue(engine):
        sys.exit("409")

import click
import sys
from pqs.scripts.config import build_engine, ENQUEUE_PROFILE_NAME
from pqs.models import Person

engine = build_engine(ENQUEUE_PROFILE_NAME)
engine.bind(Person)


def is_authenticated(id):
    # TODO
    return True


@click.group()
def main():
    pass


@main.command("push")
@click.argument("id", required=True)
@click.argument("name", required=True)
def push(id, name):
    if not is_authenticated(id): sys.exit("401")
    person = Person(id=id, name=name, enqueued_at=None, served_at=None)
    if not person.enqueue(engine):
        sys.exit("409")


@main.command("pop")
@click.argument("id", required=True)
def pop(id):
    person = Person(id=id)
    if not person.serve(engine):
        sys.exit("400")

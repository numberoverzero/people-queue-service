import click
import sys
from pqs.scripts.config import build_engine, ENQUEUE_PROFILE_NAME
from pqs.models import Person

engine = build_engine(ENQUEUE_PROFILE_NAME)
engine.bind(Person)


@click.command("register")
@click.argument("id", required=True)
def main(id):
    person = Person(id=id)
    if not person.serve(engine):
        sys.exit("400")

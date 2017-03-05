import click
import sys
from pqs.scripts.config import build_engine, ENQUEUE_PROFILE_NAME
from pqs import models

engine = build_engine(ENQUEUE_PROFILE_NAME)
models.bind_all(engine)


def is_authenticated(pid):
    # TODO
    return True


@click.group()
def main():
    pass


@main.command("push")
@click.argument("pid", required=True)
def push(pid):
    if not is_authenticated(id):
        sys.exit("401")
    status, next_position = models.push(engine, pid)
    print(next_position)
    if status != 200:
        sys.exit(1)


@main.command("serve")
@click.argument("pid", required=True)
def serve(pid):
    status = models.serve(engine, pid)
    if status != 200:
        sys.exit(1)

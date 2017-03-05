from pqs.scripts.config import build_engine, WEBSITE_PROFILE_NAME, WEBSITE_PORT
from pqs.models import Person
from pendulum import Pendulum

from flask import Flask, url_for, redirect, render_template

engine = build_engine(WEBSITE_PROFILE_NAME)
engine.bind(Person)
stream = engine.stream(Person, "trim_horizon")

app = Flask(__name__)


class Queue:
    def __init__(self):
        self._people = {}
        self._queue = []
        self._list_view = None
        self._dirty = True

    def __iter__(self):
        return iter(self._queue)

    @property
    def list_view(self):
        self.update()
        if self._dirty:
            self._list_view = render_template("queue.html", people=queue)
            self._dirty = False
        return self._list_view

    def update(self):
        record = next(stream)
        while record:
            self._dirty = True
            event_type = record["meta"]["event"]["type"]
            if event_type == "insert":
                person = record["new"]
                self._insert(person)
            elif event_type == "modify":
                person = record["new"]
                self._remove(person.id)
                if person.is_waiting:
                    self._insert(person)
            elif event_type == "remove":
                person = record["old"]
                self._remove(person.id)
            record = next(stream)

    def _remove(self, id):
        try:
            person = self._people[id]
            del self._people[id]
            self._queue.remove(person)
            self._dirty = True
        except (KeyError, ValueError):
            pass

    def _insert(self, person):
        if person.id in self._people:
            return
        self._queue.append(person)
        self._people[person.id] = person

queue = Queue()
queue.update()


@app.template_filter("humanize")
def humanize(dt: Pendulum) -> str:
    return dt.diff_for_humans(absolute=True)


@app.route("/")
def index():
    return redirect(url_for("display_queue"))


@app.route("/queue")
def display_queue():
    return queue.list_view


def main():
    app.run(debug=True, port=WEBSITE_PORT)


if __name__ == "__main__":
    main()

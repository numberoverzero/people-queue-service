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

    def __iter__(self):
        return iter(sorted(
            self._people.values(),
            key=lambda person: person.enqueued_at
        ))

    def update(self):
        record = next(stream)
        while record:
            event_type = record["meta"]["event"]["type"]
            if event_type == "insert":
                person = record["new"]
                self._people[person.id] = person

            elif event_type == "modify":
                person = record["new"]
                self._people[person.id] = person
                if not person.is_waiting:
                    del self._people[person.id]

            elif event_type == "remove":
                self._people.pop(record["old"].id, None)

            record = next(stream)


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
    queue.update()
    return render_template("queue.html", people=queue)


def main():
    app.run(debug=True, port=WEBSITE_PORT)


if __name__ == "__main__":
    main()

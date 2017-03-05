from pqs.scripts.config import build_engine, WEBSITE_PROFILE_NAME, WEBSITE_PORT
from pqs.models import Person
from pendulum import Pendulum

from flask import Flask, url_for, redirect, render_template

engine = build_engine(WEBSITE_PROFILE_NAME)
engine.bind(Person)
stream = engine.stream(Person, "trim_horizon")

app = Flask(__name__)

people = {}
queue = []


def update_queue():
    updated = False
    record = next(stream)
    while record:
        event_type = record["meta"]["event"]["type"]
        person = record.get("new", None)
        if event_type == "insert" and person.id not in people:
            updated = True
            queue.append(person)
            people[person.id] = person
        elif event_type == "modify":
            updated = True
            queue.remove(person)
            del people[person.id]
        record = next(stream)
    return updated
# Initial load
update_queue()


@app.template_filter("humanize")
def humanize(dt: Pendulum) -> str:
    return dt.diff_for_humans(absolute=True)


@app.route("/")
def index():
    return redirect(url_for("display_queue"))


@app.route("/queue")
def display_queue():
    # Grab any updates since the last time the queue was modified
    update_queue()
    return render_template("queue.html", people=queue)


def main():
    app.run(debug=True, port=WEBSITE_PORT)


if __name__ == "__main__":
    main()

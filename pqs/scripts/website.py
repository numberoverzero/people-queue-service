from pqs.scripts.config import build_engine, WEBSITE_PROFILE_NAME, WEBSITE_PORT
from pqs.models import bind_all, QueueEntry
from pendulum import Pendulum

from flask import Flask, url_for, redirect, render_template

engine = build_engine(WEBSITE_PROFILE_NAME)
bind_all(engine)
stream = engine.stream(QueueEntry, "trim_horizon")

app = Flask(__name__)


class Queue:
    def __init__(self):
        self.served = 0
        self._entries = {}
        self._ordered = []
        self._dirty = True

    def __iter__(self):
        if self._dirty:
            self._ordered = sorted(
                self._entries.values(),
                key=lambda person: person.enqueued_at
            )
            self._dirty = False
        return iter(self._ordered)

    def __nonzero__(self):
        return any(iter(self))

    def update(self):
        record = next(stream)
        while record:
            event_type = record["meta"]["event"]["type"]
            if event_type in {"insert", "modify"}:
                entry = record["new"]
                self._entries[entry.position] = entry
            elif event_type == "remove":
                self._entries.pop(record["old"].position, None)

            self._dirty = True
            record = next(stream)

        # Track served users before we filter them out
        for entry in self._entries.values():
            if entry.served_at:
                self.served += 1

        # Only keep entries with an id that haven't been served
        self._entries = {
            position: entry
            for position, entry in self._entries.items()
            if (
                getattr(entry, "id", None) and
                entry.served_at is None
            )
        }


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
    return render_template("queue.html", queue=queue)


def main():
    app.run(debug=True, port=WEBSITE_PORT)


if __name__ == "__main__":
    main()

from dataclasses import dataclass
from queue import Empty, Queue
from threading import RLock, Thread
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class Event:
    type: str
    data: Any = None


Handler = Callable[[Any], None]


class EventEngine:
    def __init__(self):
        self.queue: Queue[Event] = Queue()
        self.handlers: dict[str, list[Handler]] = {}
        self.active = False
        self._lock = RLock()
        self._thread: Thread | None = None

    def register(self, event_type: str, handler: Handler) -> None:
        if not isinstance(event_type, str) or not event_type:
            raise RuntimeError("invalid event_type", {"event_type": event_type})
        if not callable(handler):
            raise RuntimeError("invalid handler", {"event_type": event_type, "handler": handler})

        with self._lock:
            self.handlers.setdefault(event_type, []).append(handler)

    def unregister(self, event_type: str, handler: Handler) -> bool:
        with self._lock:
            hs = self.handlers.get(event_type)
            if not hs:
                return False
            removed = False
            while True:
                try:
                    hs.remove(handler)
                    removed = True
                except ValueError:
                    break
            if not hs:
                self.handlers.pop(event_type, None)
            return removed

    def put(self, event: Event | Mapping[str, Any]) -> None:
        self.queue.put(self._normalize_event(event))

    def start(self) -> None:
        with self._lock:
            if self.active:
                return
            self.active = True
            t = Thread(target=self._run, daemon=True)
            self._thread = t
            t.start()

    def stop(self) -> None:
        with self._lock:
            self.active = False

    def _normalize_event(self, event: Event | Mapping[str, Any]) -> Event:
        if isinstance(event, Event):
            return event
        if isinstance(event, Mapping):
            event_type = event.get("type")
            if not isinstance(event_type, str) or not event_type:
                raise RuntimeError("event missing type", {"event": dict(event)})
            return Event(type=event_type, data=event.get("data"))
        raise RuntimeError("invalid event", {"event": event})

    def _run(self) -> None:
        while True:
            with self._lock:
                if not self.active:
                    return
            try:
                event = self.queue.get(timeout=0.5)
            except Empty:
                continue
            with self._lock:
                handlers = list(self.handlers.get(event.type, []))
            for handler in handlers:
                handler(event.data)

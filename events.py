import asyncio
from typing import Literal, Any, ContextManager, Callable, Generic, TypeVar, Protocol
from dataclasses import dataclass
import datetime as dt
from collections import defaultdict
from contextlib import contextmanager

EventContent = TypeVar('EventContent')


def _format_template(template: str, **kwargs: Any) -> str:
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f'Missing argument {e.args[0]}')


@dataclass
class EventRecord:
    type: Literal['subscribe', 'publish', 'unsubscribe']
    event: str
    args: tuple[Any]

    def __str__(self) -> str:
        args_str = ', '.join(str(_) for _ in self.args)
        return f'{self.type} {self.event}: ({args_str})'


class Events:
    def __init__(self):
        self._events = defaultdict(list)
        self.records = None  # type: list | None

    def inspect_subscription(self) -> dict:
        return {event: [_.__qualname__ for _ in callbacks] for event, callbacks in self._events.items()}

    def subscribe(self, event: str, callback: callable):
        if self.records is not None:
            record = EventRecord(type='subscribe', event=event, args=(callback.__qualname__,))
            self.records.append(record)
            print(f'{len(self.records)}.{record}')
        self._events[event].append(callback)

    def unsubscribe(self, event: str, callback: callable):
        if self.records is not None:
            record = EventRecord(type='unsubscribe', event=event, args=(callback.__qualname__,))
            self.records.append(record)
            print(f'{len(self.records)}.{record}')
        self._events[event].remove(callback)

    def _append_record(self, event: str, args: tuple, kwargs: dict):
        record = EventRecord(type='publish', event=event, args=tuple(args) + tuple(_ for _ in kwargs.values()))
        self.records.append(record)
        print(f'{len(self.records)}.{record}')

    def publish(self, event: str, *args, **kwargs):
        if self.records is not None:
            self._append_record(event, args, kwargs)
        for callback in self._events[event]:
            assert not asyncio.iscoroutinefunction(callback), f'callback:{callback.__qualname__} cannot be a coroutine'
            callback(*args, **kwargs)


class EventCallback(Protocol[EventContent]):
    def __call__(self, timestamp: dt.datetime, content: EventContent) -> None: ...


class Event(Generic[EventContent]):
    name_template: str

    def __init__(self, events: Events, now: Callable[[], dt.datetime] = dt.datetime.now, **kwargs):
        self._events = events
        self._now = now
        self.name = _format_template(self.name_template, **kwargs)

    def subscribe(self, callback: EventCallback[EventContent]):
        self._events.subscribe(self.name, callback)

    def unsubscribe(self, callback: EventCallback[EventContent]):
        self._events.unsubscribe(self.name, callback)

    def publish(self, content: EventContent):
        self._events.publish(self.name, timestamp=self._now(), content=content)


@contextmanager
def capture_events(events: Events) -> ContextManager[list[EventRecord]]:
    records = []
    events.records = records
    print('\n---captured events---')
    try:
        yield records
    finally:
        events.records = None

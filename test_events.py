import pytest

from events import capture_events, Events, Event, AsyncEvent, _format_template


class DataRecorder:
    def __init__(self):
        self.data = None

    def record(self, *args, **kwargs):
        self.data = {'args': args, 'kwargs': kwargs}

    async def async_record(self, *args, **kwargs):
        self.data = {'args': args, 'kwargs': kwargs}


@pytest.fixture
def events() -> Events:
    return Events()


@pytest.fixture
def data_recorder() -> DataRecorder:
    return DataRecorder()


@pytest.fixture
def dummy_event(events) -> Event[float]:
    class _Event(Event[float]):
        name_template = '{var}_event'
    return _Event(events, var='test')


@pytest.fixture
def dummy_async_event(events) -> AsyncEvent[float]:
    class _Event(AsyncEvent[float]):
        name_template = '{var}_event'
    return _Event(events, var='test')


def test_format_template():
    assert _format_template('{var}_event', var='test') == 'test_event'
    with pytest.raises(ValueError) as excinfo:
        _format_template('{var}_event')
    assert str(excinfo.value) == 'Missing argument var'
    with pytest.raises(ValueError) as excinfo:
        _format_template('{var}_event', invalid_arg='a')
    assert str(excinfo.value) == 'Missing argument var'


def test_events(events, data_recorder):
    with capture_events(events) as records:
        events.subscribe('event_1', data_recorder.record)
        events.publish('event_1', 1, 2, c=None)
    assert events.inspect_subscription() == {'event_1': ['DataRecorder.record']}
    assert [str(_) for _ in records] == [
        'subscribe event_1: (DataRecorder.record)', 'publish event_1: (1, 2, None)']
    assert data_recorder.data == {'args': (1, 2), 'kwargs': {'c': None}}


@pytest.mark.asyncio
async def test_async_events(events):
    async def coro(**kwargs):
        print(kwargs)

    events.subscribe('async_event_1', coro)
    with pytest.raises(AssertionError):
        events.publish('async_event_1', a=123)  # cannot publish when async callback exists
    await events.async_publish('async_event_1', a=123)


def test_event(events, data_recorder, dummy_event):
    with capture_events(events) as records:
        dummy_event.subscribe(callback=data_recorder.record)
        dummy_event.publish(content=1.23)
    assert [str(_) for _ in records] == [
        'subscribe test_event: (DataRecorder.record)', 'publish test_event: (1.23)']
    assert data_recorder.data == {'args': (1.23,), 'kwargs': {}}


@pytest.mark.asyncio
async def test_async_event(events, data_recorder, dummy_async_event):
    with capture_events(events) as records:
        dummy_async_event.subscribe(callback=data_recorder.async_record)
        await dummy_async_event.publish(content=1.23)
    assert [str(_) for _ in records] == [
        'subscribe test_event: (DataRecorder.async_record)', 'publish test_event: (1.23)']
    assert data_recorder.data == {'args': (1.23,), 'kwargs': {}}


if __name__ == '__main__':
    pytest.main()

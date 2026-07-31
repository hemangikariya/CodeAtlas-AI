from typing import Dict, List, Type, Callable, Awaitable
from backend.app.events.event_types import Event
from backend.app.core.logging import logger

# Async subscriber type hint
SubscriberType = Callable[[Event], Awaitable[None]]

class EventDispatcher:
    def __init__(self):
        self._subscribers: Dict[Type[Event], List[SubscriberType]] = {}

    def subscribe(self, event_type: Type[Event], handler: SubscriberType):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to event {event_type.__name__}")

    async def dispatch(self, event: Event):
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        logger.info(f"Dispatching event {event_type.__name__} (ID: {event.event_id}) to {len(handlers)} handlers.")
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error executing event handler {handler.__name__} for event {event_type.__name__}: {str(e)}")

# Global event dispatcher instance
event_dispatcher = EventDispatcher()

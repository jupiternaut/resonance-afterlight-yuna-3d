from __future__ import annotations

from collections.abc import Callable
from typing import Any


RegistryFn = Callable[..., Any]


class ActuatorRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RegistryFn] = {}

    def register(self, name: str, fn: RegistryFn) -> None:
        if name in self._items:
            raise ValueError(f"Actuator already registered: {name}")
        self._items[name] = fn

    def get(self, name: str) -> RegistryFn:
        try:
            return self._items[name]
        except KeyError as exc:
            raise KeyError(f"Unknown actuator: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._items)


registry = ActuatorRegistry()


def register(name: str) -> Callable[[RegistryFn], RegistryFn]:
    def decorator(fn: RegistryFn) -> RegistryFn:
        registry.register(name, fn)
        return fn

    return decorator

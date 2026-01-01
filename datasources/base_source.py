from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Dict

Event = Dict[str, Any]


class DataSourceError(Exception):
    pass


class DataSource(ABC):

    @abstractmethod
    def fetch_raw(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Any) -> List[Any]:
        raise NotImplementedError

    def fetch_and_parse(self) -> List[Any]:
        raw = self.fetch_raw()
        return self.parse(raw)

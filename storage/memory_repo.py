from typing import Dict, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class MemoryRepo(Generic[T]):
    def __init__(self, key_field: str):
        self.key_field = key_field
        self.items: Dict[str, T] = {}

    def upsert(self, item: T) -> T:
        key = getattr(item, self.key_field)
        self.items[str(key)] = item
        return item

    def get(self, key: str) -> Optional[T]:
        return self.items.get(str(key))

    def delete(self, key: str) -> bool:
        return self.items.pop(str(key), None) is not None

    def list(self) -> Dict[str, T]:
        return self.items
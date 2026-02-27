from abc import ABC, abstractmethod


class BaseImageProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, output_path: str) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

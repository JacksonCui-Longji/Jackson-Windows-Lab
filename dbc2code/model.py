
from enum import Enum
from dataclasses import dataclass, field

class ByteOrder(Enum):
    MOTOROLA = 0
    INTEL = 1

@dataclass
class Signal:
    signal_name: str
    start_bit: int
    length: int
    byte_order: ByteOrder
    signed: bool
    factor: float
    offset: float
    min_value: float
    max_value: float
    unit: str
    receiver: list[str]

@dataclass
class Message:
    message_name: str
    message_id: int
    dlc: int
    transmitter: str
    signals: list[Signal]

@dataclass
class DataBase:
    messages: list[Message]
    signal_counts: int = field(init=False, default=0)

    def __post_init__(self):
        self.signal_counts = sum(len(message.signals) for message in self.messages)

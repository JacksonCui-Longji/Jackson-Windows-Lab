from dataclasses import dataclass, field
from enum import Enum

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
    message_index: int = field(init=False, default=-1)

@dataclass
class Message:
    message_name: str
    message_id: int
    dlc: int
    transmitter: str
    signals: list[Signal]
    is_extended: bool = False
    is_canfd: bool = False

@dataclass
class DataBase:
    messages: list[Message]
    signal_counts: int = field(init=False, default=0)
    all_signals: list[Signal] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.signal_counts = sum(len(message.signals) for message in self.messages)
        for msg_idx, message in enumerate(self.messages):
            for signal in message.signals:
                signal.message_index = msg_idx
                self.all_signals.append(signal)
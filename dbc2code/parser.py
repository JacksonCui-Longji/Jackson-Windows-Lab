import model
import re
from pathlib import Path

def ParserCANMessage(line: str) -> model.Message:
    pattern = r'^BO_ (\d+) (\w+): (\d+) (\w+)'
    match = re.match(pattern, line)
    if match:
        message_id = int(match.group(1))
        message_name = match.group(2)
        dlc = int(match.group(3))
        transmitter = match.group(4)
        return model.Message(message_id, message_name, dlc, transmitter, signals=[])
    return None

def ParserCANSignal(line: str) -> model.Signal:
    pattern = r'SG_ (\w+) : (\d+)\|(\d+)@(\d)([+-]) \(([\-\d.]+),([\-\d.]+)\) \[([\-\d.]+)\|([\-\d.]+)\] "(\w*)" (.+)'
    match = re.match(pattern, line.strip())
    if match:
        signal_name = match.group(1)
        start_bit = int(match.group(2))
        length = int(match.group(3))
        byte_order = model.ByteOrder.INTEL if match.group(4) == '1' else model.ByteOrder.MOTOROLA
        signed = (match.group(5) == '-')
        factor = float(match.group(6))
        offset = float(match.group(7))
        min_value = float(match.group(8))
        max_value = float(match.group(9))
        unit = match.group(10)
        receiver = match.group(11).split(',')
        return model.Signal(signal_name, start_bit, length, byte_order, signed, factor, offset, min_value, max_value, unit, receiver)
    return None

def ParserCANDBC(dbc_content: str) -> model.DataBase:
    messages = []
    current_message = None

    for line in dbc_content.splitlines():
        if line.startswith("BO_"):
            if current_message is not None:
                messages.append(current_message)
            current_message = ParserCANMessage(line)
        elif line.strip().startswith("SG_"):
            signal = ParserCANSignal(line)
            if current_message is not None and signal is not None:
                current_message.signals.append(signal)
        elif line.strip() == "":
            if current_message is not None:
                messages.append(current_message)
            current_message = None

    if current_message is not None:      # 文件末尾没空行时的兜底
        messages.append(current_message)

    return model.DataBase(messages)

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    dbc_path = script_dir / "input" / "vehicle.dbc"
    with open(dbc_path, "r") as f:
        dbc_content = f.read()
        database = ParserCANDBC(dbc_content)
        print(database)

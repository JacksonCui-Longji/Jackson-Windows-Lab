import model
import re
from pathlib import Path


def ParserCANMessage(line: str) -> model.Message:
    pattern = r'^BO_\s+(\d+)\s+(\w+):\s*(\d+)\s+(\w+)'
    match = re.match(pattern, line)
    if match:
        raw_id = int(match.group(1))
        is_extended = bool(raw_id & 0x80000000)
        message_id = (raw_id & 0x1FFFFFFF) if is_extended else raw_id

        message_name = match.group(2)
        dlc = int(match.group(3))
        transmitter = match.group(4)

        msg = model.Message(message_name, message_id, dlc, transmitter,
                             signals=[], is_extended=is_extended)
        msg.raw_id = raw_id   # 临时挂一个属性，供后续 BA_ VFrameFormat 匹配用，不属于DBC模型本身
        return msg
    return None


def ParserCANSignal(line: str) -> model.Signal:
    pattern = (
        r'SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@(\d)([+-])\s*'
        r'\(([\-\d.]+),([\-\d.]+)\)\s*'
        r'\[([\-\d.]+)\|([\-\d.]+)\]\s*'
        r'"([^"]*)"\s*(.+)'
    )
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

        receiver_str = match.group(11).rstrip(';').strip()
        receiver = receiver_str.split()

        return model.Signal(signal_name, start_bit, length, byte_order, signed,
                             factor, offset, min_value, max_value, unit, receiver)
    return None


def ParserVFrameFormat(line: str):
    """解析 BA_ "VFrameFormat" BO_ <raw_id> <value>; 这一行
    返回 (raw_id, value)，value: 0=标准CAN 1=扩展CAN 2=标准CANFD 3=扩展CANFD
    """
    pattern = r'^BA_\s+"VFrameFormat"\s+BO_\s+(\d+)\s+(\d+)\s*;'
    match = re.match(pattern, line.strip())
    if match:
        raw_id = int(match.group(1))
        value = int(match.group(2))
        return raw_id, value
    return None


def ParserCANDBC(dbc_content: str) -> model.DataBase:
    messages = []
    current_message = None
    raw_id_lookup = {}   # raw_id -> Message对象，供第二遍扫描VFrameFormat时查找

    lines = dbc_content.splitlines()

    # 第一遍：解析 BO_ / SG_，组装 Message/Signal
    for line in lines:
        if line.startswith("BO_"):
            if current_message is not None:
                messages.append(current_message)
            current_message = ParserCANMessage(line)
            if current_message is not None:
                raw_id_lookup[current_message.raw_id] = current_message
        elif line.strip().startswith("SG_"):
            signal = ParserCANSignal(line)
            if current_message is not None and signal is not None:
                current_message.signals.append(signal)
        elif line.strip() == "":
            if current_message is not None:
                messages.append(current_message)
            current_message = None
    if current_message is not None:
        messages.append(current_message)

    # 第二遍：解析 BA_ "VFrameFormat"，反过来标记对应Message是否是CAN FD
    for line in lines:
        if line.strip().startswith('BA_ "VFrameFormat"'):
            result = ParserVFrameFormat(line)
            if result is not None:
                raw_id, value = result
                msg = raw_id_lookup.get(raw_id)
                if msg is not None:
                    msg.is_canfd = (value in (2, 3))

    return model.DataBase(messages)


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    dbc_path = script_dir / "input" / "vehicle.dbc"
    with open(dbc_path, "r", encoding="utf-8") as f:
        dbc_content = f.read()
        database = ParserCANDBC(dbc_content)
        print(database)
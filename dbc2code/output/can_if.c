#include "can_if.h"
#include <string.h>

static MessageBuffer MessageBufferTable[] = {
    { 0x100, 8, {0} },
    { 0x200, 4, {0} }
};

static const SignalInfo SignalInfoTable[CAN_SIG_ID_MAX_VALUE] = {
    { 0, 0, 16, INTEL, false, 0.25f, 0.0f, 0.0f, 8000.0f },
    { 0, 16, 16, INTEL, false, 0.01f, 0.0f, 0.0f, 250.0f },
    { 0, 32, 8, INTEL, false, 1.0f, 0.0f, 0.0f, 8.0f },
    { 1, 0, 4, INTEL, false, 1.0f, 0.0f, 0.0f, 1.0f },
    { 1, 4, 4, INTEL, false, 1.0f, 0.0f, 0.0f, 1.0f }
};

#define MESSAGE_BUFFER_COUNT (sizeof(MessageBufferTable) / sizeof(MessageBufferTable[0]))

// Fixed-size table indexed directly by CanSignalId, no lookup needed.
// Unsubscribed slots have callback == NULL.
static SubscriberInfo callback_info[CAN_SIG_ID_MAX_VALUE] = {0};

static int FindMessageBufferIndex(uint32_t message_id) {
    for (int i = 0; i < (int)MESSAGE_BUFFER_COUNT; i++) {
        if (MessageBufferTable[i].message_id == message_id) {
            return i;
        }
    }
    return -1;
}

CanIfRet UpdateCanFrame(uint32_t message_id, const uint8_t* data, uint8_t dlc) {
    int idx = FindMessageBufferIndex(message_id);
    if (idx < 0) {
        return CAN_IF_RET_NG;
    }
    if (dlc > CAN_FD_MAX_DLC) {
        return CAN_IF_RET_NG;
    }
    MessageBufferTable[idx].dlc = dlc;
    memcpy(MessageBufferTable[idx].data, data, dlc);
    return CAN_IF_RET_OK;
}

// Note: raw_value uses uint64_t storage, max 64 bits (8 bytes) per signal.
// CAN FD signals could theoretically span more than 64 bits, but in practice
// DBC signals rarely exceed 64 bits, so this is not handled.

static uint64_t ExtractIntel(const uint8_t* can_data, uint16_t start_bit, uint8_t length) {
    uint64_t raw_value = 0;
    for (uint8_t i = 0; i < length; i++) {
        uint16_t global_bit = start_bit + i;
        uint16_t byte_idx = global_bit / 8;
        uint8_t  bit_in_byte = global_bit % 8;
        uint8_t  bit_value = (can_data[byte_idx] >> bit_in_byte) & 0x01;
        raw_value |= ((uint64_t)bit_value) << i;
    }
    return raw_value;
}

static uint64_t ExtractMotorola(const uint8_t* can_data, uint16_t start_bit, uint8_t length) {
    uint64_t raw_value = 0;
    for (uint8_t i = 0; i < length; i++) {
        uint16_t dbc_bit_num = start_bit - i;
        uint16_t byte_idx = dbc_bit_num / 8;
        uint8_t  bit_in_byte = dbc_bit_num % 8;
        uint8_t  real_bit_pos = 7 - bit_in_byte;
        uint8_t  bit_value = (can_data[byte_idx] >> real_bit_pos) & 0x01;
        raw_value |= ((uint64_t)bit_value) << (length - 1 - i);
    }
    return raw_value;
}

static void PackIntel(uint8_t* can_data, uint16_t start_bit, uint8_t length, uint64_t raw_value) {
    for (uint8_t i = 0; i < length; i++) {
        uint16_t global_bit = start_bit + i;
        uint16_t byte_idx = global_bit / 8;
        uint8_t  bit_in_byte = global_bit % 8;
        uint8_t  bit_value = (raw_value >> i) & 0x01;

        can_data[byte_idx] &= ~(1u << bit_in_byte);
        can_data[byte_idx] |= (bit_value << bit_in_byte);
    }
}

static void PackMotorola(uint8_t* can_data, uint16_t start_bit, uint8_t length, uint64_t raw_value) {
    for (uint8_t i = 0; i < length; i++) {
        uint16_t dbc_bit_num = start_bit - i;
        uint16_t byte_idx = dbc_bit_num / 8;
        uint8_t  bit_in_byte = dbc_bit_num % 8;
        uint8_t  real_bit_pos = 7 - bit_in_byte;
        uint8_t  bit_value = (raw_value >> (length - 1 - i)) & 0x01;

        can_data[byte_idx] &= ~(1u << real_bit_pos);
        can_data[byte_idx] |= (bit_value << real_bit_pos);
    }
}

static int64_t SignExtend(uint64_t raw_value, uint8_t length) {
    if (raw_value & (1ULL << (length - 1))) {
        uint64_t sign_mask = ~((1ULL << length) - 1);
        return (int64_t)(raw_value | sign_mask);
    }
    return (int64_t)raw_value;
}

CanIfRet GetSignalValue(CanSignalId sig_id, float* out_value) {
    if ((sig_id < 0) || (sig_id >= CAN_SIG_ID_MAX_VALUE) || (out_value == NULL)) {
        return CAN_IF_RET_NG;
    }

    const SignalInfo* info = &SignalInfoTable[sig_id];
    const uint8_t* can_data = MessageBufferTable[info->message_index].data;

    uint64_t raw_value = (info->byte_order == INTEL)
        ? ExtractIntel(can_data, info->start_bit, info->length)
        : ExtractMotorola(can_data, info->start_bit, info->length);

    if (info->is_signed) {
        int64_t signed_raw = SignExtend(raw_value, info->length);
        *out_value = (float)signed_raw * info->factor + info->offset;
    } else {
        *out_value = (float)raw_value * info->factor + info->offset;
    }

    return CAN_IF_RET_OK;
}

CanIfRet SetSignalValue(CanSignalId sig_id, float physical_value) {
    if ((sig_id < 0) || (sig_id >= CAN_SIG_ID_MAX_VALUE)) {
        return CAN_IF_RET_NG;
    }

    const SignalInfo* info = &SignalInfoTable[sig_id];

    if ((physical_value < info->min_value) || (physical_value > info->max_value)) {
        return CAN_IF_RET_NG;
    }

    uint64_t raw_value = (uint64_t)((physical_value - info->offset) / info->factor);
    uint8_t* can_data = MessageBufferTable[info->message_index].data;

    if (info->byte_order == INTEL) {
        PackIntel(can_data, info->start_bit, info->length, raw_value);
    } else {
        PackMotorola(can_data, info->start_bit, info->length, raw_value);
    }

    return CAN_IF_RET_OK;
}

CanIfRet SubscribeCanSig(SubscriberInfo *info, uint32_t num) {
    if ((NULL == info) || (0 == num)) {
        return CAN_IF_RET_NG;
    }
    for (uint32_t i = 0; i < num; i++) {
        if ((info[i].sig_id < 0) || (info[i].sig_id >= CAN_SIG_ID_MAX_VALUE)) {
            continue;
        }
        callback_info[info[i].sig_id] = info[i];
    }
    return CAN_IF_RET_OK;
}

CanIfRet PublishSignal(CanSignalId sig_id) {
    if ((sig_id < 0) || (sig_id >= CAN_SIG_ID_MAX_VALUE)) {
        return CAN_IF_RET_NG;
    }
    if (callback_info[sig_id].callback == NULL) {
        return CAN_IF_RET_NG;
    }

    float value;
    if (GetSignalValue(sig_id, &value) != CAN_IF_RET_OK) {
        return CAN_IF_RET_NG;
    }

    return callback_info[sig_id].callback(sig_id, value);
}
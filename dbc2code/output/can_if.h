#ifndef CAN_IF_H
#define CAN_IF_H

#include <stdint.h>
#include <stdbool.h>
#include "can_signal_id.h"

#define CAN_FD_MAX_DLC  64

typedef enum ByteOrder_t {
    INTEL,      // LSB
    MOTOROLA    // MSB
} ByteOrder;

typedef enum CanSignalType_t {
    CAN_SIG_TYPE_PERIOD = 0,
    CAN_SIG_TYPE_ONCHANGE,
    CAN_SIG_TYPE_PERIOD_ONCHANGE,
} CanSignalType;

typedef enum CanIfRet_t {
    CAN_IF_RET_OK = 0,
    CAN_IF_RET_NG
} CanIfRet;

typedef struct SignalInfo_t {
    uint8_t  message_index;
    uint16_t start_bit;      // CAN FD max is 511, uint8_t can't hold it, use uint16_t
    uint8_t  length;
    ByteOrder byte_order;
    bool is_signed;
    float factor;
    float offset;
    float min_value;
    float max_value;
} SignalInfo;

typedef struct MessageBuffer_t {
    uint32_t message_id;
    uint8_t  dlc;
    uint8_t  data[CAN_FD_MAX_DLC];
} MessageBuffer;

typedef CanIfRet (*SignalCallback)(CanSignalId sig_id, float value);

typedef struct SubscriberInfo_t {
    CanSignalId sig_id;
    CanSignalType sub_type;
    uint32_t period_ms;
    SignalCallback callback;
} SubscriberInfo;

CanIfRet GetSignalValue(CanSignalId sig_id, float* out_value);
CanIfRet SetSignalValue(CanSignalId sig_id, float physical_value);
CanIfRet SubscribeCanSig(SubscriberInfo *info, uint32_t num);
CanIfRet PublishSignal(CanSignalId sig_id);
CanIfRet UpdateCanFrame(uint32_t message_id, const uint8_t* data, uint8_t dlc);

#endif // CAN_IF_H
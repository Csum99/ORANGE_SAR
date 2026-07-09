#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PulsON 440 message formats."""

__author__ = "Ramamurthy Bhagavatula"
__version__ = "1.0"
__maintainer__ = "Ramamurthy Bhagavatula"
__email__ = "ramamurthy.bhagavatula@ll.mit.edu"

"""References
[1] Monostatic Radar Application Programming Interface (API) Specification
    PulsON (R) 400 Series
    Version: 1.2.2
    Date: January 2015
    https://timedomain.com/wp-content/uploads/2015/12/320-0298E-MRM-API-Specification.pdf
"""

# Import required modules and methods
from collections import OrderedDict
import numpy as np
from constants import REC_ANTENNA_MODE, REC_PERSIST_FLAG, REC_SCAN_RES, RESERVED_VAL, NOT_IMPLEMENTED_VAL

# Formats of various messages between host and radar. Each one is defined by a message type and a 
# packet definition. A packet definition is an order dictionary specifying the order of the packet
# fields. The values in these dictionaries depend on whether the message is for host to radar 
# messages or for radar to host messages.
# 
# For host to radar messages each key's value is a 3 element list where the first element is the 
# data type, second value is the default value, and the third value is the inclusive bounds. If the 
# default value is None then this part of the packet must be user defined otherwise the default 
# value is used. If the bounds value is None then no enforcement is applied.
#
# For radar to host messages each key's value is the 2 element list where the first element is the
# data type and the second value the expected number of values of said type. This difference in 
# format is to ensure the right message format is used for the right direction of communication.

# Set radar configuration request; host to radar
MRM_SET_CONFIG_REQUEST = {'message_type': 4097, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                                  ('message_id', [np.dtype(np.uint16), None, None]), # Message ID
                                  ('node_id', [np.dtype(np.uint32), None, (1, 2**32 - 2)]), # Node ID
                                  ('scan_start', [np.dtype(np.int32), None, (-499998, 499998)]), # Scan start time (ps)
                                  ('scan_stop', [np.dtype(np.int32), None, None]), # Scan stop time (ps)
                                  ('scan_res', [np.dtype(np.uint16), REC_SCAN_RES, (32, 32)]), # Scan resolution (bins); recommended value used
                                  ('pii', [np.dtype(np.uint16), None, (6, 15)]), # Pulse integration index
                                  ('seg_1_samp', [np.dtype(np.uint16), NOT_IMPLEMENTED_VAL, None]), # Segment 1 samples; not used
                                  ('seg_2_samp', [np.dtype(np.uint16), NOT_IMPLEMENTED_VAL, None]), # Segment 2 samples; not used
                                  ('seg_3_samp', [np.dtype(np.uint16), NOT_IMPLEMENTED_VAL, None]), # Segment 3 samples; not used
                                  ('seg_4_samp', [np.dtype(np.uint16), NOT_IMPLEMENTED_VAL, None]), # Segment 4 samples; not used
                                  ('seg_1_int', [np.dtype(np.uint8), NOT_IMPLEMENTED_VAL, None]), # Segment 1 integration; not used
                                  ('seg_2_int', [np.dtype(np.uint8), NOT_IMPLEMENTED_VAL, None]), # Segment 2 integration; not used
                                  ('seg_3_int', [np.dtype(np.uint8), NOT_IMPLEMENTED_VAL, None]), # Segment 3 integration; not used
                                  ('seg_4_int', [np.dtype(np.uint8), NOT_IMPLEMENTED_VAL, None]), # Segment 4 integration; not used
                                  ('ant_mode', [np.dtype(np.uint8), REC_ANTENNA_MODE, (2, 3)]), # Antenna mode; recommended value used
                                  ('tx_gain_ind', [np.dtype(np.uint8), None, (0, 63)]), # Transmit gain index
                                  ('code_channel', [np.dtype(np.uint8), None, (0, 10)]), # Code channel
                                  ('persist_flag', [np.dtype(np.uint8), REC_PERSIST_FLAG, (0, 1)])])} # Persist flag
MRM_SET_CONFIG_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_SET_CONFIG_REQUEST['packet_def'].values()])

# Set radar configuration confirmation; radar to host
MRM_SET_CONFIG_CONFIRM = {'message_type': 4353, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), 1]), # Message type
                                  ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                                  ('status', [np.dtype(np.uint32), 1])])} # Set configuration status
MRM_SET_CONFIG_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_SET_CONFIG_CONFIRM['packet_def'].values()])

# Get radar configuration request; host to radar
MRM_GET_CONFIG_REQUEST = {'message_type': 4098, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                                  ('message_id', [np.dtype(np.uint16), None, None])])} # Message ID
MRM_GET_CONFIG_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_GET_CONFIG_REQUEST['packet_def'].values()])

# Set radar configuration request; radar to host
MRM_GET_CONFIG_CONFIRM = {'message_type': 4354, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), 1]), # Message type
                                  ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                                  ('node_id', [np.dtype(np.uint32), 1]), # Node ID
                                  ('scan_start', [np.dtype(np.int32), 1]), # Scan start time (ps)
                                  ('scan_stop', [np.dtype(np.int32), 1]), # Scan stop time (ps)
                                  ('scan_res', [np.dtype(np.uint16), 1]), # Scan resolution (bins); recommended value used
                                  ('pii', [np.dtype(np.uint16), 1]), # Pulse integration index
                                  ('seg_1_samp', [np.dtype(np.uint16), 1]), # Segment 1 samples; not used
                                  ('seg_2_samp', [np.dtype(np.uint16), 1]), # Segment 2 samples; not used
                                  ('seg_3_samp', [np.dtype(np.uint16), 1]), # Segment 3 samples; not used
                                  ('seg_4_samp', [np.dtype(np.uint16), 1]), # Segment 4 samples; not used
                                  ('seg_1_int', [np.dtype(np.uint8), 1]), # Segment 1 integration; not used
                                  ('seg_2_int', [np.dtype(np.uint8), 1]), # Segment 2 integration; not used
                                  ('seg_3_int', [np.dtype(np.uint8), 1]), # Segment 3 integration; not used
                                  ('seg_4_int', [np.dtype(np.uint8), 1]), # Segment 4 integration; not used
                                  ('ant_mode', [np.dtype(np.uint8), 1]), # Antenna mode; recommended value used
                                  ('tx_gain_ind', [np.dtype(np.uint8), 1]), # Transmit gain index
                                  ('code_channel', [np.dtype(np.uint8), 1]), # Code channel
                                  ('persist_flag', [np.dtype(np.uint8), 1]), # Persist flag
                                  ('timestamp', [np.dtype(np.uint32), 1]), # Time since boot (ms)
                                  ('status', [np.dtype(np.uint32), 1])])} # Status
MRM_GET_CONFIG_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_GET_CONFIG_CONFIRM['packet_def'].values()])

# Radar scan request; host to radar
MRM_CONTROL_REQUEST = {'message_type': 4099, # Message type
                       'packet_def': OrderedDict([
                               ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                               ('message_id', [np.dtype(np.uint16), None, None]), # Message ID
                               ('scan_count', [np.dtype(np.uint16), None, (0, 65535)]), # Scan count
                               ('reserved', [np.dtype(np.uint16), RESERVED_VAL, None]), # Reserved
                               ('scan_interval', [np.dtype(np.uint32), None, None])])} # Scan interval (us)
MRM_CONTROL_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_CONTROL_REQUEST['packet_def'].values()])

# Radar scan confirm; radar to host
MRM_CONTROL_CONFIRM = {'message_type': 4355, # Message type
                       'packet_def': OrderedDict([
                               ('message_type', [np.dtype(np.uint16), 1]), # Message type
                               ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                               ('status', [np.dtype(np.uint32), 1])])} # Status 
MRM_CONTROL_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_CONTROL_CONFIRM['packet_def'].values()])

# Radar reboot request; host to radar
MRM_REBOOT_REQUEST = {'message_type': 61442, # Message type
                      'packet_def': OrderedDict([
                              ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                              ('message_id', [np.dtype(np.uint16), None, None])])} # Message ID
MRM_REBOOT_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_REBOOT_REQUEST['packet_def'].values()])

# Radar reboot confirm; radar to host
MRM_REBOOT_CONFIRM = {'message_type': 61698, # Message type
                      'packet_def': OrderedDict([
                              ('message_type', [np.dtype(np.uint16), 1]), # Message type
                              ('message_id', [np.dtype(np.uint16), 1])])} # Message ID
MRM_REBOOT_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_REBOOT_CONFIRM['packet_def'].values()])

# Scan data; radar to host
MRM_SCAN_INFO = {'message_type': 61953, # Message type
                 'packet_def': OrderedDict([
                         ('message_type', [np.dtype(np.uint16), 1]), # Message type
                         ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                         ('node_id', [np.dtype(np.uint32), 1]), # Node ID
                         ('timestamp', [np.dtype(np.uint32), 1]), # Time since boot (ms)
                         ('reserved0', [np.dtype(np.uint32), 1]), # Reserved
                         ('reserved1', [np.dtype(np.uint32), 1]), # Reserved
                         ('reserved2', [np.dtype(np.uint32), 1]), # Reserved
                         ('reserved3', [np.dtype(np.uint32), 1]), # Reserved
                         ('scan_start', [np.dtype(np.int32), 1]), # Scan start time (ps)
                         ('scan_stop', [np.dtype(np.int32), 1]), # Scan stop time (ps)
                         ('scan_res', [np.dtype(np.int16), 1]), # Scan resolution (bins)
                         ('scan_type', [np.dtype(np.uint8), 1]), # Type of scan data
                         ('reserved4', [np.dtype(np.uint8), 1]), # Reserved
                         ('antenna_id', [np.dtype(np.uint8), 1]), # Receiving antenna designator
                         ('operational_mode', [np.dtype(np.uint8), 1]), # Operational mode
                         ('num_samples_message', [np.dtype(np.uint16), 1]), # Number of samples in this message
                         ('num_samples_total', [np.dtype(np.uint32), 1]), # Number of samples in single scan
                         ('message_index', [np.dtype(np.uint16), 1]), # Index of this message's portion of data in single scan
                         ('num_messages_total', [np.dtype(np.uint16), 1]), # Number of data messages in single scan
                         ('scan_data', [np.dtype(np.int32), 350])])} # Scan data
MRM_SCAN_INFO['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_SCAN_INFO['packet_def'].values()])

# Radar status request; host to radar
MRM_GET_STATUSINFO_REQUEST = {'message_type': 61441, # Message type
                              'packet_def': OrderedDict([
                                      ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                                      ('message_id', [np.dtype(np.uint16), None, None])])} # Message ID
MRM_GET_STATUSINFO_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_GET_STATUSINFO_REQUEST['packet_def'].values()])

# Radar status confirm; radar to host
MRM_GET_STATUSINFO_CONFIRM = {'message_type': 61697, # Message type
                              'packet_def': OrderedDict([
                                      ('message_type', [np.dtype(np.uint16), 1]), # Message type
                                      ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                                      ('mrm_ver_major', [np.dtype(np.uint8), 1]), # MRM embedded major version number
                                      ('mrm_ver_minor', [np.dtype(np.uint8), 1]), # MRM embedded minor version number
                                      ('mrm_ver_build', [np.dtype(np.uint16), 1]), # MRM embedded build version number
                                      ('uwb_kernel_major', [np.dtype(np.uint8), 1]), # Kernel code major version number
                                      ('uwb_kernel_minor', [np.dtype(np.uint8), 1]), # Kernel code minor version number
                                      ('uwb_kernel_build', [np.dtype(np.uint16), 1]), # Kernel code build version number
                                      ('fpga_firmware_ver', [np.dtype(np.uint8), 1]), # Firmware version number in hexadecimal
                                      ('fpga_firmware_year', [np.dtype(np.uint8), 1]), # Firmware year encoded
                                      ('fpga_firmware_month', [np.dtype(np.uint8), 1]), # Firmware month encoded
                                      ('fpga_firmware_day', [np.dtype(np.uint8), 1]), # Firmware day encoded
                                      ('serial_num', [np.dtype(np.uint32), 1]), # Serial number in hexadecimal
                                      ('board_rev', [np.dtype(np.uint8), 1]), # PCB revision as single character
                                      ('bit_result', [np.dtype(np.uint8), 1]), # Built-in-Test result; non-zero indicates failure
                                      ('board_type', [np.dtype(np.uint8), 1]), # 1 - P400, 2 - P410
                                      ('tx_config', [np.dtype(np.uint8), 1]), # 0 - FCC compliant, 1 - FCC compliant w/ amplifiers, 3 - EU compliant
                                      ('temperature', [np.dtype(np.int32), 1]), # Board temperature in 0.25 degrees Celcius
                                      ('pkg_ver', [np.dtype(np.uint8), 32]), # Embedded package release version
                                      ('status', [np.dtype(np.uint32), 1])])} # Status
MRM_GET_STATUSINFO_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_GET_STATUSINFO_CONFIRM['packet_def'].values()])

# Custom radar communication check request that ONLY works w/ emulator; DO NOT USE W/ REAL RADAR; host to radar
MRM_COMM_CHECK_REQUEST = {'message_type': 65534, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), None, None]), # Message type
                                  ('message_id', [np.dtype(np.uint16), None, None]), # Message ID
                                  ('uint8_val', [np.dtype(np.uint8), None, None]), # uint8 test value
                                  ('uint16_val', [np.dtype(np.uint16), None, None]), # uint16 test value
                                  ('uint32_val', [np.dtype(np.uint32), None, None]), # uint32 test value
                                  ('int8_val', [np.dtype(np.int8), None, None]), # int8 test value
                                  ('int16_val', [np.dtype(np.int16), None, None]), # int16 test value
                                  ('int32_val', [np.dtype(np.int32), None, None])])} # int32 test value
MRM_COMM_CHECK_REQUEST['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_COMM_CHECK_REQUEST['packet_def'].values()])

# Radar communication check confirmation that ONLY works w/ emulator; DO NOT USE W/ REAL RADAR; radar to host
MRM_COMM_CHECK_CONFIRM = {'message_type': 65535, # Message type
                          'packet_def': OrderedDict([
                                  ('message_type', [np.dtype(np.uint16), 1]), # Message type
                                  ('message_id', [np.dtype(np.uint16), 1]), # Message ID
                                  ('uint8_val', [np.dtype(np.uint8), 1]), # uint8 test value
                                  ('uint16_val', [np.dtype(np.uint16), 1]), # uint16 test value
                                  ('uint32_val', [np.dtype(np.uint32), 1]), # uint32 test value
                                  ('int8_val', [np.dtype(np.int8), 1]), # int8 test value
                                  ('int16_val', [np.dtype(np.int16), 1]), # int16 test value
                                  ('int32_val', [np.dtype(np.int32), 1]), # int32 test value
                                  ('datetime_str', [np.dtype(np.uint8), 15]), # Datetime string in %Y%m%dT%H%M%S format
                                  ('status', [np.dtype(np.uint32), 1])])} # Status
MRM_COMM_CHECK_CONFIRM['packet_length'] = sum( # Packet length (bytes))
        [value[0].itemsize for value in MRM_COMM_CHECK_CONFIRM['packet_def'].values()])

# Dictionary containing all message formats; useful for iteration and searching
ALL_MRM_MESSAGES = {
        'MRM_SET_CONFIG_REQUEST': MRM_SET_CONFIG_REQUEST,
        'MRM_SET_CONFIG_CONFIRM': MRM_SET_CONFIG_CONFIRM,
        'MRM_GET_CONFIG_REQUEST': MRM_GET_CONFIG_REQUEST,
        'MRM_GET_CONFIG_CONFIRM': MRM_GET_CONFIG_CONFIRM,
        'MRM_CONTROL_REQUEST': MRM_CONTROL_REQUEST,
        'MRM_CONTROL_CONFIRM': MRM_CONTROL_CONFIRM,
        'MRM_REBOOT_REQUEST': MRM_REBOOT_REQUEST,
        'MRM_REBOOT_CONFIRM': MRM_REBOOT_CONFIRM,
        'MRM_SCAN_INFO': MRM_SCAN_INFO,
        'MRM_GET_STATUSINFO_REQUEST': MRM_GET_STATUSINFO_REQUEST,
        'MRM_GET_STATUSINFO_CONFIRM': MRM_GET_STATUSINFO_CONFIRM,
        'MRM_COMM_CHECK_REQUEST': MRM_COMM_CHECK_REQUEST,
        'MRM_COMM_CHECK_CONFIRM': MRM_COMM_CHECK_CONFIRM}
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PulsON 440 constants module."""

__author__ = "Ramamurthy Bhagavatula, Michael Riedl"
__version__ = "1.0"
__maintainer__ = "Ramamurthy Bhagavatula"
__email__ = "ramamurthy.bhagavatula@ll.mit.edu"

# Import required modules and method
from collections import OrderedDict

# Specific recommended radar configurations
REC_SCAN_RES = 32 # Scan resolution (bins)
REC_PERSIST_FLAG = 0 # Persist flag
REC_ANTENNA_MODE = 2 # Transmit/receive configuration of antennas

# Miscellaneous value
RESERVED_VAL = 0 # Value for reserved fields
NOT_IMPLEMENTED_VAL = 0 # Value for not implemented fields

# Byte order to and from radar
BYTE_ORDER = 'big'

# Radar system constants; these are values defined by how the radar system, i.e., radar itself with 
# antennas and so on has been configured
DT_0 = 0 # Path delay through antennas (ns)

# Default values and bounds for settings that can set through radar settings YAML
DEFAULT_SETTINGS = {
        'dT_0': # Path delay through antennas (ns)
            {'default': DT_0, 'bounds': (0, float('inf'))}, 
        'range_start': # Start range (m)
            {'default': 4, 'bounds':(0, float('inf'))},
        'range_stop': # Stop range (m)
            {'default': 14.5, 'bounds': (0, float('inf'))},
        'tx_gain_ind': # Transmit gain index
            {'default': 63, 'bounds': (0, 63)},
        'pii': # Pulse integration index
            {'default': 11, 'bounds': (6, 15)},
        'code_channel': # Code channel
            {'default': 0, 'bounds': (0, 10)},
        'node_id': # Node ID
            {'default': 1, 'bounds': (1, 2**32 - 2)},
        'persist_flag': # Persist flag
            {'default': 0, 'bounds': (0, 1)},
        'quick_look_num_scans': # Number of scans to perform in quick-look
            {'default': 200, 'bounds': (1, float('inf'))},
        'set_config_timeout': # Time (s) allowed to successfully set radar configuration before raising an error
            {'default': 5, 'bounds': (0.1, float('inf'))},
        'get_config_timeout': # Time (s) allowed to successfully get radar configuration before raising an error
            {'default': 1, 'bounds': (0.1, float('inf'))},
        'scan_request_timeout': # Time (s) allowed to successfully send scan request before raising error
            {'default': 1, 'bounds': (0.1, float('inf'))},
        'read_packet_timeout': # Time (s) allowed between consecutive packets before raising error
            {'default': 1, 'bounds': (0.1, float('inf'))},
        'read_residual_timeout': # Time (s) allowed to read residual streaming data before dropping scans
            {'default': 5, 'bounds': (0.1, float('inf'))}}

# Default values for radar configuration; these are generally overwritten by settings
DEFAULT_CONFIG = OrderedDict([
    ('node_id', 1), # Node ID
    ('scan_start', 23342), # Scan start time (ps); corresponds to 4 m
    ('scan_stop', 81935), # Scan stop time (ps); corresponds to 14.5 m
    ('scan_res', REC_SCAN_RES), # Scan resolution (bins); recommended value used
    ('pii', 11), # Pulse integration index
    ('seg_1_samp', NOT_IMPLEMENTED_VAL), # Segment 1 samples; not used
    ('seg_2_samp', NOT_IMPLEMENTED_VAL), # Segment 2 samples; not used
    ('seg_3_samp', NOT_IMPLEMENTED_VAL), # Segment 3 samples; not used
    ('seg_4_samp', NOT_IMPLEMENTED_VAL), # Segment 4 samples; not used
    ('seg_1_int', NOT_IMPLEMENTED_VAL), # Segment 1 integration; not used
    ('seg_2_int', NOT_IMPLEMENTED_VAL), # Segment 2 integration; not used
    ('seg_3_int', NOT_IMPLEMENTED_VAL), # Segment 3 integration; not used
    ('seg_4_int', NOT_IMPLEMENTED_VAL), # Segment 4 integration; not used
    ('ant_mode', REC_ANTENNA_MODE), # Antenna mode; recommended value used
    ('tx_gain_ind', 63), # Transmit gain index
    ('code_channel', 0), # Code channel
    ('persist_flag', REC_PERSIST_FLAG)]) # Persist flag
    
# Default host-radar connection settings
HOST_IP = "192.168.1.1" # Host IP address
HOST_PORT = 10000 # Host port
RADAR_IP = "192.168.1.151" # Radar IP address; [1] states this is the default value but is not always the case
RADAR_PORT = 21210 # Radar port
DISPLAY_IP = "192.168.2.5" # IP for machine to display 
DISPLAY_PORT = 21211

# API constants/special values
MAX_PACKET_SIZE = 1500 # (bytes)
SCAN_INFO_HEADER_SIZE = 52 # (bytes)
MAX_SCAN_INFO_PACKET_SIZE = 1452 # (bytes)
FOREVER_SCAN_COUNT = 65535 # Scan count setting to enable scanning until stopped
STOP_SCAN_COUNT = 0 # Scan count setting to stop scanning
MIN_SCAN_COUNT = 1 # Minimum number of scans that can be made
CONTINUOUS_SCAN_INTERVAL = 0 # Interval (us) between consecutive scans that enables continuous scanning
MAX_MESSAGE_ID = 2**16 - 1 # Maximum message ID

# Radar manufacturer constants; these are values defined by the manufacturer
DT_MIN = 1 / (512 * 1.024) # Time sample resolution/bin size of the radar (ns)
T_BIN = 32 * DT_MIN # Rake receiver time sample/bin size (ns)
DN_BIN = 96 # Radar scan time segment/quanta size
SEG_NUM_BINS = 350 # Number of bins in a scan segment
IMPULSE_RATE = 9.5e6 # Default impulse rate (Hz)
RAKE_SIZE = 732 # Length of 12-finger rake receiver (ps)

# Default logger
DEFAULT_LOGGER_NAME = 'pulson440'
DEFAULT_LOGGER_CONFIG = \
    {
        'version': 1,
        'formatters': {
            'full': {
                'format': '%(asctime)s   %(module)-25s   %(levelname)-8s   %(message)s'
            },
            'brief': {
                'format': '%(asctime)s   %(levelname)-8s   %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'brief'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'full',
                'filename': '{0}.log'.format(DEFAULT_LOGGER_NAME)
            }
        },
        'loggers': {
            DEFAULT_LOGGER_NAME: {
                'handlers': ['console', 'file'],
                'level': 'INFO'
            }
        }
    }

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PulsON 440 radar command and control class."""

__author__ = 'Ramamurthy Bhagavatula, Michael Riedl'
__version__ = '1.0'
__maintainer__ = 'Ramamurthy Bhagavatula'
__email__ = 'ramamurthy.bhagavatula@ll.mit.edu'

"""References
[1] Monostatic Radar Application Programming Interface (API) Specification
    PulsON (R) 400 Series
    Version: 1.2.2
    Date: January 2015
    https://timedomain.com/wp-content/uploads/2015/12/320-0298E-MRM-API-Specification.pdf
"""
# Update path
from formats import MRM_REBOOT_CONFIRM, MRM_REBOOT_REQUEST
from pathlib import Path
import sys
if Path('..//').resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path('..//').resolve().as_posix())
    
# Import required modules and methods
from common.constants import SPEED_OF_LIGHT
from collections import OrderedDict
from copy import deepcopy
import math
import logging
import numpy as np
from pulson440.constants import BYTE_ORDER, DEFAULT_SETTINGS, DEFAULT_CONFIG, MAX_PACKET_SIZE, \
    FOREVER_SCAN_COUNT, STOP_SCAN_COUNT, MIN_SCAN_COUNT, CONTINUOUS_SCAN_INTERVAL, DT_MIN, \
    T_BIN, DN_BIN, SEG_NUM_BINS, HOST_IP, HOST_PORT, RADAR_IP, RADAR_PORT, REC_SCAN_RES, \
    REC_PERSIST_FLAG
from pulson440.formats import MRM_CONTROL_CONFIRM, MRM_CONTROL_REQUEST, MRM_GET_CONFIG_CONFIRM, \
    MRM_GET_CONFIG_REQUEST, MRM_SET_CONFIG_CONFIRM, MRM_SET_CONFIG_REQUEST, \
    MRM_GET_STATUSINFO_REQUEST, MRM_GET_STATUSINFO_CONFIRM, MRM_COMM_CHECK_REQUEST, \
    MRM_COMM_CHECK_CONFIRM, MRM_SCAN_INFO
import socket
import time
import yaml

# Control file
CONTROL_FILENAME = 'control_radar'

class PulsON440:
    """Class for command and control of PulsON 440 radar."""
    
    def __init__(self, logger=None, host_ip=HOST_IP, host_port=HOST_PORT, 
                 radar_ip=RADAR_IP, radar_port=RADAR_PORT):
        """Instance initialization.
        
        Args:
            logger (logging.Logger)
                Configured logger.
                
            host_ip (str)
                IP address of the host. Defaults to HOST_IP.

            host_port (int)
                Port on host. Defaults to HOST_PORT.

            radar_ip (str)
                IP address of the radar that host should target. Defaults to RADAR_IP.
                
            radar_port (int)
                Port on radar that the host should target. Defaults to RADAR_PORT.
        """
        # Radar status indicators
        self.connected = False
        self.collecting = False
        self.stop_collecting = False    # Set to true to stop a running collection
        
        # Radar system parameters
        self.N_bin = [] # Number of bins in scan
        
        # Connection settings
        self.connection = {
                'host_address': (host_ip, host_port), # Host and radar addresses
                'radar_address': (radar_ip, radar_port), 
                'socket': []} # UDP socket
        
        # User settings; partially higher abstraction than the radar's internal configuration;
        self.settings = {key: value['default'] for key, value in DEFAULT_SETTINGS.items()}
        
        # Radar internal status and configuration
        self.status = None
        self.config = DEFAULT_CONFIG
        
        # Logger
        self._logger = None
        self.logger = logger
        
        # Message counter
        self.msg_count = 0

        
    def __del__(self):
        """Clean up actions upon object deletion."""
        self.disconnect()

        
    """logger property decorators. Setter validates logger's types is a valid logger type."""
    @property
    def logger(self):
        return self._logger

    
    @logger.setter
    def logger(self, value):
        if value is None:
            self._logger = logging.getLogger('trash')
            self._logger.propagate = False
        elif not issubclass(type(value), logging.getLoggerClass()):
            raise TypeError("Specified logger of incorrect type; expecting subclass of logging.Logger!")
        else:
            self._logger = value

    
    def read_settings_file(self, settings_file='settings.yml'):
        """Read user specified settings file.
        
        Args:
            settings_file (str)
                Path and name of settings file.
                
        Raises:
            ValueError if setting is out of bounds.
        """
        self.logger.info(f"Reading settings from '{settings_file}'...")
        with open(settings_file, 'r') as f:
            settings = yaml.load(f, Loader=yaml.FullLoader)
        self.logger.info(f"Read following settings --> {settings}")

        # Iterate over each user setting and check bounds if applicable
        for setting, value in settings.items():
            if setting in DEFAULT_SETTINGS:
                if ('bounds' in DEFAULT_SETTINGS[setting] and 
                    DEFAULT_SETTINGS[setting]['bounds'] is not None):
                    bounds = DEFAULT_SETTINGS[setting]['bounds']
                    if not (bounds[0] <= value <= bounds[1]):
                        raise ValueError(f"Radar setting '{setting}' is out of bounds!")
                self.settings[setting] = value
            else:
                self.settings[setting] = value
                
        # Update radar configuration
        self.logger.debug(f"Following settings being used --> {self.settings}")
        self.settings_to_config()

    
    def settings_to_config(self):
        """Translate settings into radar configuration."""
        # Based on the specified start and stop ranges determine the scan start and stop times
        scan_start = (2 * float(self.settings['range_start']) / (SPEED_OF_LIGHT / 1e9) + 
                      self.settings['dT_0'])
        scan_stop = (2 * float(self.settings['range_stop']) / (SPEED_OF_LIGHT / 1e9) + 
                     self.settings['dT_0'])
        N_bin = (scan_stop - scan_start) / T_BIN
        N_bin = DN_BIN * math.ceil(N_bin / DN_BIN)
        scan_start = math.floor(1000 * DT_MIN * math.floor(scan_start / DT_MIN))
        scan_stop = N_bin * T_BIN + scan_start / 1000
        scan_stop = math.floor(1000 * DT_MIN * math.ceil(scan_stop / DT_MIN))
        
        # Update radar configuration
        self.N_bin = N_bin
        self.config['scan_start'] = scan_start
        self.config['scan_stop'] = scan_stop
        self.config['pii'] = self.settings['pii']
        self.config['tx_gain_ind'] = self.settings['tx_gain_ind']
        self.config['code_channel'] = self.settings['code_channel']
        self.config['node_id'] = self.settings['node_id']
        self.config['persist_flag'] = self.settings['persist_flag']
        self.logger.debug(f"Settings parsed into following configuration --> {self.config}")

        
    def config_to_bytes(self):
        """Converts radar configuration to bytes so it can be written to file.

        Returns:
            config_bytes (bytes)
                The current radar configuration (as stored in instance) represented as bytes.
        """
        # Add all configuration fields
        config_bytes = b''
        for config_field, config_value in self.config.items():
            dtype = MRM_GET_CONFIG_CONFIRM['packet_def'][config_field][0]
            config_bytes += (config_value).to_bytes(length=dtype.itemsize, byteorder=BYTE_ORDER,
                    signed=np.issubdtype(dtype, np.signedinteger))
        return config_bytes


    def encode_host_to_radar_message(self, raw_payload, msg_format):
        """Encode host to radar message.
        
        Args:
            raw_payload (dict)
                Specifies the payload to encode. Each key must match exactly a key in packet_def
                contained in 'msg_format'.
            
            msg_format (dict)
                Message format as defined in formats.py. Primary keys are 'message_type' and 
                'packet_def'.
        
        Returns:
            msg (bytes)
                The payload encoded into a byte sequence for transmission to the radar.
                
        Raises:
            KeyError if payload does not contain key that must be user defined.
        """
        # Make a deep copy of payload to avoid malforming original
        payload = deepcopy(raw_payload)

        # Update payload w/ message type and ID
        payload['message_type'] = msg_format['message_type']
        payload['message_id'] = self.msg_count
        self.msg_count += 1
        
        # Add all packet fields to message
        msg = b''
        for packet_field in msg_format['packet_def'].keys():
            dtype = msg_format['packet_def'][packet_field][0]
            default_value = msg_format['packet_def'][packet_field][1]
            
            # Check if current packet field is in payload
            if packet_field not in payload:
                if default_value is None:
                    raise KeyError(f"Payload for message type {msg_format['message_type']} "
                                   f"missing field {packet_field}")
                else:
                    payload[packet_field] = default_value
                    
            # Add current packet field's payload value onto message
            msg += (payload[packet_field]).to_bytes(length=dtype.itemsize, byteorder=BYTE_ORDER, 
                                                    signed=np.issubdtype(dtype, np.signedinteger))
        return msg

        
    @staticmethod
    def decode_radar_to_host_message(msg, msg_format):
        """Decode radar to host message.
        
        Args:
            msg (bytes)
                Message byte sequence received from radar.
                
            msg_format (dict)
                Message format as defined in formats.py. Primary keys are 'message_type' and 
                'packet_def'.
                
        Returns:
            payload (dict)
                Decoded payload.
        """
        # Initialize decoded payload
        payload = OrderedDict.fromkeys(msg_format['packet_def'])
        
        # Iterate over each field in packet definition
        byte_counter = 0
        for packet_field in msg_format['packet_def'].keys():
            dtype = msg_format['packet_def'][packet_field][0]
            count = msg_format['packet_def'][packet_field][1]
            num_bytes = dtype.itemsize
            payload[packet_field] = [None] * count
            # Iterate through expected count
            for entry in range(count):
                payload[packet_field][entry] = int.from_bytes(
                    msg[byte_counter:(byte_counter + num_bytes)], byteorder=BYTE_ORDER, 
                    signed=np.issubdtype(dtype, np.signedinteger))
                byte_counter += num_bytes
            # Remove list if only a single entry
            if len(payload[packet_field]) == 1:
                payload[packet_field] = payload[packet_field][0]
        return payload
    
    
    @staticmethod
    def decode_radar_to_host_message_type(msg):
        """Decode radar to host message type.
        
        Args:
            msg (bytes)
                Message byte sequence received from radar.
                
        Returns:
            msg_type (int)
                Decoded message type.
        """
        return int.from_bytes(msg[0:2], byteorder=BYTE_ORDER, signed=False)
    
        
    def connect(self):
        """Connect to radar and set up control file.
        
        Raises:
            RuntimeError if fails to connect to radar.
        """
        # Try to connect to radar
        self.logger.info("Trying to connect to radar...")
        try:
            self.connection['sock'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connection['sock'].setblocking(False)
            self.connection['sock'].bind(self.connection['host_address'])
            self.connected = True
        except:
            print(self.connection['host_address'])
            raise RuntimeError("Failed to connect to radar!")
            
        self.logger.info("Connected to radar!")

    
    def disconnect(self):
        """Disconnect from radar and close control file.
        
        Raises:
            RuntimeError if fails to disconnect from radar.
        """
        # Try to disconnect from radar if needed
        if not self.connected:
            self.logger.info("Cannot disconnect, no radar connected!")
        else:
            self.logger.info("Trying to disconnect from radar...")
            try:
                if self.collecting:
                    self.scan_request(scan_count=STOP_SCAN_COUNT)
                self.connection['sock'].close()
                self.connected = False
                self.logger.info("Disconnected from radar!")
            except:
                raise RuntimeError("Failed to disconnect from radar!")


    def stop_scan(self):
        """
        Stop an active scan.
        Does nothing if collection is not running now.

        TODO: proper thread safety....
        """
        self.stop_collecting = True

    def request_comm_check(self, test_values):
        """Request communications check from radar. ONLY WORKS W/ EMULATOR.

        Args:
            test_values (list):
                Test values in following format order: uint8, uint16, uint32, int8, int16, int32.

        Raises:
            RuntimeError if radar not already connected.
            RuntimeError if fails to receive communications check confirmation within timeout.
            RuntimeError if test values are not parroted back.
        """
        self.logger.info("Requesting radar reboot...")
        # Make sure radar is connected
        if self.connected:

            # Request communications check
            payload = {'uint8_val': test_values[0], 'uint16_val': test_values[1], 
                       'uint32_val': test_values[2], 'int8_val': test_values[3],
                       'int16_val': test_values[4], 'int32_val': test_values[5]}
            msg = self.encode_host_to_radar_message(payload, MRM_COMM_CHECK_REQUEST)
            self.connection['sock'].sendto(msg, self.connection['radar_address'])

            # Wait for communications check within the timeout
            start = time.time()
            status_flag = -1
            while (time.time() - start) < self.settings['comm_check_timeout']:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                except:
                    continue

                # Decode payload
                payload = self.decode_radar_to_host_message(msg, MRM_COMM_CHECK_CONFIRM)
                payload['datetime_str'] = \
                    ''.join([chr(unicode) for unicode in payload['datetime_str']])

                # Make sure request payload was parroted back correctly
                if (test_values[0] != payload['uint8_val'] or test_values[1] != payload['uint16_val'] or
                    test_values[2] != payload['uint32_val'] or test_values[3] != payload['int8_val'] or
                    test_values[4] != payload['int16_val'] or test_values[5] != payload['int32_val']):
                    raise RuntimeError("Communication check test values not parroted back!")
                else:
                    self.logger.debug(f"Datetime string received was {payload['datetime_str']}")
                    status_flag = 0
                    break
            if status_flag == -1:
                raise RuntimeError("Communications check request timed out!")
            self.logger.info("Communications check request successful!")
            return status_flag
        
        else:
            raise RuntimeError("Radar not connected!")


    def request_reboot(self):
        """Request radar reboot.
        
        Raises:
            RuntimeError if radar not already connected.
            RuntimeError if fails to receive reboot confirmation within timeout.
        """
        self.logger.info("Requesting radar reboot...")
        # Make sure radar is connected
        if self.connected:
            
            # Request the current radar configuration
            payload = {}
            msg = self.encode_host_to_radar_message(payload, MRM_REBOOT_REQUEST)
            self.connection['sock'].sendto(msg, self.connection['radar_address'])
            
            # Wait for radar configuration within the timeout
            start = time.time()
            status_flag = -1
            while (time.time() - start) < self.settings['reboot_request_timeout']:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                except:
                    continue
                
                # Decode payload
                payload = self.decode_radar_to_host_message(msg, MRM_REBOOT_CONFIRM)
                status_flag = 0
                break

            if status_flag == -1:
                raise RuntimeError("Reboot request timed out!")
            self.logger.info("Reboot request successful!")
            return status_flag
        
        else:
            raise RuntimeError("Radar not connected!")


    def get_radar_status(self):
        """Get radar status and health as indicated by the BIT result.
        
        Returns:
            status_flag (int)
                Status flag indicating success/failure of get status request. Any non-zero value is 
                a failure.
            
            healthy (bool)
                Indicates whether or not the radar is healthy as indicated by the power-on BIT 
                result. Only returned if radar is healthy, i.e., power-on BIT passed.
        
        Raises:
            RuntimeError if radar is not already connected.
            RuntimeError if fails to receive radar status within timeout.
            RuntimeError if BIT result returned from radar indicates a failure.
        """
        self.logger.info("Requesting radar status...")
        # Make sure radar is connected
        if self.connected:
            
            # Request the current radar configuration
            payload = {}
            msg = self.encode_host_to_radar_message(payload, MRM_GET_STATUSINFO_REQUEST)
            self.connection['sock'].sendto(msg, self.connection['radar_address'])
            
            # Wait for radar configuration within the timeout
            start = time.time()
            status_flag = -1
            while (time.time() - start) < self.settings['get_health_timeout']:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                except:
                    continue

                # Decode payload
                self.status = self.decode_radar_to_host_message(msg, MRM_GET_STATUSINFO_CONFIRM)
                status_flag = self.status['status']
                break

            if status_flag == -1:
                raise RuntimeError("Get radar status timed out!")
            elif status_flag != 0:
                raise RuntimeError(f"Failed to get radar status with error code {status_flag}!")
            self.logger.info("Get radar status successful!")
            self.logger.debug(f"Radar status received --> {self.config}")
            
            # Check radar health as indicated by power-on BIT result
            healthy = True
            if self.status['bit_result'] != 0:
                raise RuntimeError("Radar reporting power-on BIT failure!")

            # Address fields that are not purely numeric
            self.status['fpga_firmware_year'] = (self.status['fpga_firmware_year'] >> 4) * 10 + \
                                                (self.status['fpga_firmware_year'] % 16)
            self.status['fpga_firmware_month'] = (self.status['fpga_firmware_month'] >> 4) * 10 + \
                                                 (self.status['fpga_firmware_month'] % 16)
            self.status['fpga_firmware_day'] = (self.status['fpga_firmware_day'] >> 4) * 10 + \
                                               (self.status['fpga_firmware_day'] % 16)
            self.status['serial_num'] = f"{self.status['serial_num']:#0{10}x}"
            self.status['board_rev'] = chr(self.status['board_rev'])
            self.status['temperature'] = self.status['temperature'] / 4
            self.status['pkg_ver'] = ''.join([chr(unicode) for unicode in self.status['pkg_ver']])
            
            return status_flag, healthy
        
        else:
            raise RuntimeError("Radar not connected!")

        
    def get_radar_config(self):
        """Get configuration from radar.
        
        Returns:
            status_flag (int)
                Status flag indicating success/failure of get configuration request. Any non-zero 
                value is a failure.
                
        Raises:
            RuntimeError if radar not already connected.
            RuntimeError if fails to receive radar configuration within timeout.
        """
        self.logger.info("Requesting radar configuration...")
        # Make sure radar is connected
        if self.connected:
            
            # Request the current radar configuration
            payload = {}
            msg = self.encode_host_to_radar_message(payload, MRM_GET_CONFIG_REQUEST)
            self.connection['sock'].sendto(msg, self.connection['radar_address'])
            
            # Wait for radar configuration within the timeout
            start = time.time()
            status_flag = -1
            while (time.time() - start) < self.settings['get_config_timeout']:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                except:
                    continue

                # Decode payload
                payload = self.decode_radar_to_host_message(msg, MRM_GET_CONFIG_CONFIRM)
                self.config = OrderedDict([(key, payload[key]) for key in DEFAULT_CONFIG])
                status_flag = payload['status']
                break

            if status_flag == -1:
                raise RuntimeError("Get radar configuration timed out!")
            elif status_flag != 0:
                raise RuntimeError(f"Failed to get radar configuration with error code {status_flag}!")
            self.logger.info("Get radar configuration successful!")
            self.logger.debug(f"Radar configuration received --> {self.config}")
            return status_flag
        
        else:
            raise RuntimeError("Radar not connected!")

        
    def set_radar_config(self):
        """Set radar configuration based on user settings.
        
        Returns:
           status_flag (int)
                Status flag indicating success/failure of get configuration request. Any non-zero 
                value is a failure.
        
        Raises:
            RuntimeError if radar not already connected.
            RuntimeError if fails to send radar configuration within timeout.
        """
        # Make sure radar is connected
        self.logger.info("Setting radar configuration...")
        if self.connected:
            
            # Determine desired configuration from user settings
            self.settings_to_config()
            
            # Scan resolution; API states that any value aside from 32 will likely cause undesired 
            # behavior so overwrite it
            if self.config['scan_res'] != REC_SCAN_RES:
                self.logger.warning("Overriding specified scan resolution of "
                                    f"{self.config['scan_res']} with recommended value of "
                                    f"{REC_SCAN_RES}")
                self.config['scan_res'] = REC_SCAN_RES
            
            # Configuration persistence flag
            if self.config['persist_flag'] != REC_PERSIST_FLAG:
                self.logger.warning(f"Specified persist flag value of {self.config['persist_flag']} "
                                    f"not the recommended value of {REC_PERSIST_FLAG}")
            
            # Encode configuration into message and send
            msg = self.encode_host_to_radar_message(self.config, MRM_SET_CONFIG_REQUEST)
            self.connection['sock'].sendto(msg, self.connection['radar_address'])
            
            # Poll for configuration set confirmation from radar within timeout 
            start = time.time()
            status_flag = -1
            while (time.time() - start) < self.settings['set_config_timeout']:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                except:
                    continue

                # Decode payload
                payload = self.decode_radar_to_host_message(msg, MRM_SET_CONFIG_CONFIRM)
                status_flag = payload['status']
                break

            if status_flag == -1:
                raise RuntimeError("Set radar configuration timed out!")
            elif status_flag != 0:
                raise RuntimeError(f"Failed to set radar configuration with error code {status_flag}!")
            self.logger.info("Set radar configuration successful!")
            self.logger.debug(f"Radar configuration set --> {self.config}")
            return status_flag
        
        else:
            raise RuntimeError("Radar not connected!")

            
    def scan_request(self, scan_count, scan_interval=CONTINUOUS_SCAN_INTERVAL):
        """Initiate a set of scans by the radar.
        
        Args:
            scan_count (int)
                Number of scans to request; refer to [1] for details.
            
            scan_interval (int)
                Interval between sequential scans (us); defaults to CONTINUOUS_SCAN_INTERVAL for 
                continuous scanning.
        
        Returns:
            status_flag (int)
                Status flag indicating success/failure of get configuration request. Any non-zero 
                value is a failure.

            scan_data (bytes)
                Scan data read from the radar prior to scan request confirmation being received. 
                Needs to unpacked to properly access scan information.
        
        Raises:
            RuntimeError if radar not already connected.
            ValueError if scan_count is not between MIN_SCAN and CONTINUOUS_SCAN.
            RuntimeError if fails to send scan request within timeout.
        """
        # Check if radar is connected
        if self.connected:
            
            # Check if scan count is within bounds
            if scan_count < STOP_SCAN_COUNT or scan_count > FOREVER_SCAN_COUNT:
                raise ValueError(f"Requested number of scans {scan_count} is outside valid range "
                                 f"of {STOP_SCAN_COUNT} and {FOREVER_SCAN_COUNT}")
                
            # Check if request conflicts w/ radar already actively collecting
            elif self.collecting and scan_count != STOP_SCAN_COUNT:
                self.logger.warning(
                    "Radar already collecting and new scan request cannot be serviced!")
            
            # Create scan request and send
            else:
                self.logger.info(f"Requesting radar scan with {scan_count} scans with scan "
                                 f"interval of {scan_interval}")
                payload = {'scan_count': scan_count, 'scan_interval': scan_interval}
                msg = self.encode_host_to_radar_message(payload, MRM_CONTROL_REQUEST)
                self.connection['sock'].sendto(msg, self.connection['radar_address'])
                
                # Check if scan request was successful or not within timeout
                start = time.time()
                status_flag = -1
                scan_data = b''
                while (time.time() - start) < self.settings['scan_request_timeout']:
                    try:
                        msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                    except:
                        continue
                    
                    # Decode payload
                    msg_type = self.decode_radar_to_host_message_type(msg)
                    if (self.collecting and scan_count == STOP_SCAN_COUNT and 
                        msg_type == MRM_SCAN_INFO['message_type']):
                        scan_data += msg
                    else:
                        payload = self.decode_radar_to_host_message(msg, MRM_CONTROL_CONFIRM)
                        status_flag = payload['status']
                        break
                    
                if status_flag == -1:
                    raise RuntimeError("Scan request timed out!")
                elif status_flag != 0:
                    raise RuntimeError(f"Failed scan request with error code {status_flag}!")
                self.logger.info("Scan request successful!")
                return status_flag, scan_data
            
        else:
            raise RuntimeError("Radar not connected!")

            
    def read_scan_data(self, scan_data_filename=None, return_data=False, 
                       realtime=False, display_ip=None, display_port=None, 
                       num_scans=None, msg_count=None):
        """Read data returned from radar scans.
        
        Args:
            scan_data_filename (str)
                Path and name of file to save radar scans to. If None then data is not saved. 
                Defaults to None.
                
            return_data (bool)
                Flag indicating whether or not to return read data; flag exists to avoid creating 
                large internal variables when not needed. Defaults to False.
                
            num_scans (int)
                Number of scans to read. Appropriate value depends on the configuration of the 
                last scan request. If None then scans will be read until stop flag is posted to 
                control file. Defaults to None.
                
        Returns:
            scan_data (bytes)
                Scan data read from the radar. Needs to unpacked to properly access scan 
                information. Will only be non-empty if return_data is set to True.

        Raises:
            RuntimeError if radar not connected.
        """
        # Check if radar is connected and not already collecting data
        if self.connected:

            # Default return data
            scan_data = b''

            config_bytes = self.config_to_bytes()
            # Create scan data file if needed 
            if scan_data_filename is not None:
                scan_data_file = open(scan_data_filename, 'wb')
                
                # Add all configuration values to save file
                scan_data_file.write(config_bytes)
            elif realtime:
                print("Realtime collection")
                realtime_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                realtime_socket.sendto(config_bytes, (display_ip, display_port))
            else:
                pass

            # Read fixed length or streaming data off radar
            self.logger.info("Reading data from the radar...")
            msg_count = 0
            start = time.time()
            self.stop_collecting = False
            while True:
                try:
                    msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                    if return_data:
                        scan_data += msg
                    if scan_data_filename is not None:
                        scan_data_file.write(msg)
                    elif scan_data_filename is not None and realtime == False:
                        break
                    elif realtime:
                        realtime_socket.sendto(msg, (display_ip, display_port))
                    msg_count += 1
                    start = time.time()
                    
                    # Determine number of expected number of messages
                    if msg_count == 1:
                        num_msg_per_scan = int.from_bytes(msg[50:52], byteorder=BYTE_ORDER, signed=False)
                        num_msgs = num_scans * num_msg_per_scan

                    # Read the specified number of packets
                    if num_scans is not None:
                        if msg_count == num_msgs:
                            break
                    
                    # Read until stop flag is enabled.
                    if self.stop_collecting:
                        _, residual_scan_data = self.scan_request(scan_count=STOP_SCAN_COUNT)
                        if return_data:
                            scan_data += residual_scan_data
                        if scan_data_filename is not None:
                            scan_data_file.write(residual_scan_data)
                        break
                
                # Check if single message read timeout threshold has been violated
                except:
                    if (time.time() - start) > self.settings['read_scan_data_timeout']:
                        self.logger.warning("Radar scan data message read timed out!")
                        break

            # Read any remaining streaming radar data
            if msg_count is not None:
                start = time.time()
                while (time.time() - start) < self.settings['read_residual_timeout']:
                    try:
                        msg, _ = self.connection['sock'].recvfrom(MAX_PACKET_SIZE)
                        if return_data:
                            scan_data += msg
                        if scan_data_filename is not None:
                            scan_data_file.write(msg)
                        if realtime:
                            realtime_socket.sendto(msg, (display_ip, display_port))
                    except:
                        pass
                self.logger.info("Read all available data.")
            
            # Close scan data file
            if scan_data_filename is not None:
                scan_data_file.close()
            return scan_data
        
        else:
            raise RuntimeError("Radar not connected!")

            
    def quick_look(self, scan_data_filename=None, return_data=False):
        """Executes quick-look with radar to confirm desired operation.
        
        Args:
            scan_data_filename (str)
                Path and name of file to save radar scans to. If None then data is not saved. 
                Defaults to None.
                
            return_data (bool)
                Flag indicating whether or not to return read data; flag exists to avoid creating 
                large internal variables when not needed. Defaults to False.
        
        Returns:
            scan_data (bytes)
                Scan data read from the radar. Needs to unpacked to properly access scan 
                information. Will only be non-empty if return_data is set to True.
        
        Raises:
            RuntimeError if scan data is not being either saved or returned.
            RuntimeError if radar not connected already or already collecting data.
        """
        # Check if data is being saved in some fashion
        if not return_data and not scan_data_filename:
            raise RuntimeError("Scan data not being saved to file or returned!")
        
        # Compute number of expected data packets in quick-look
        num_quick_look_packets = (math.ceil(float(self.N_bin) / float(SEG_NUM_BINS)) *
                                  self.settings['quick_look_num_scans'])
        
        # Check if radar is connected and not already collecting data
        if self.connected and not self.collecting:
            self.logger.info("Starting quick-look mode...")
            
            # Send a scan request
            self.scan_request(self.settings['quick_look_num_scans'])
            self.collecting = True
            
            # Read streaming data from radar and save if desired
            scan_data = self.read_scan_data(scan_data_filename, return_data, num_quick_look_packets)
            self.collecting = False
            self.logger.info("Completed quick-look mode!")
            
        else:
            raise RuntimeError("Radar not connected or is already collecting data!")
        
        return scan_data

        
    def collect(self, scan_count=FOREVER_SCAN_COUNT, scan_interval=CONTINUOUS_SCAN_INTERVAL,
                scan_data_filename=None, return_data=False):
        """Collects radar data continuously until commanded to stop.
        
        Args:
            scan_count (int)
                Number of scans to collect. Defaults to FOREVER_SCAN_COUNT.
            
            scan_interval (int)
                Interval between sequential scans (us). Defaults to CONTINUOUS_SCAN_INTERVAL.
            
            scan_data_filename (str)
                Path and name of file to save radar scans to. If None then data is not saved. 
                Defaults to None.
                
            return_data (bool)
                Flag indicating whether or not to return read data; flag exists to avoid creating 
                large internal variables when not needed. Defaults to False.
                
        Returns:
            scan_data (bytes)
                Scan data read from the radar. Needs to unpacked to properly access scan 
                information. Will only be non-empty if return_data is set to True.
        
        Raises:
            ValueError if number of scans is less than minimum accepted value.
            RuntimeError if scan data is not being either saved or returned.
            RuntimeError if radar not connected already or already collecting data.
        """
        # Check if number of scans is less than minimum
        if scan_count < MIN_SCAN_COUNT:
            raise ValueError(f"Cannot request less than {MIN_SCAN_COUNT} scans!")
        
        # Check if data is being saved in some fashion
        if not return_data and not scan_data_filename:
            raise RuntimeError("Scan data not being saved to file or returned!")
            
        # Check if radar is connected and not already collecting data
        if self.connected and not self.collecting:
            self.logger.info(f"Starting collect mode with {scan_count} scans...")
            
            # Send a scan request
            self.scan_request(scan_count=scan_count, scan_interval=scan_interval)
            self.collecting = True
            
            # Read either undetermined amount of data from continuous scanning or predetermined 
            # amount of scan data based on finite scan count
            num_scans = None if scan_count == FOREVER_SCAN_COUNT else scan_count
            scan_data = self.read_scan_data(scan_data_filename=scan_data_filename, 
                                            return_data=return_data, 
                                            num_scans=num_scans)
            self.collecting = False
            self.logger.info("Stopped collect mode!")
            
        else:
            raise RuntimeError("Radar not connected or is already collecting data!")
            
        return scan_data
        
    def realtime(self, scan_count=FOREVER_SCAN_COUNT, scan_interval=CONTINUOUS_SCAN_INTERVAL,
                 display_ip=None, display_port=None, scan_data_filename=None, return_data=False):
                # Check if radar is connected and not already collecting data
        if self.connected and not self.collecting:
            self.logger.info('Starting collect mode with {0} scans...'.format(scan_count))
            
            # Send a scan request
            self.scan_request(scan_count=scan_count, scan_interval=scan_interval)
            self.collecting = True
            msg_count = None
            if scan_count != FOREVER_SCAN_COUNT:
                msg_count = (math.ceil(float(self.N_bin) / SEG_NUM_BINS) * scan_count)
            self.read_scan_data(scan_data_filename=scan_data_filename, 
                                return_data=return_data, 
                                msg_count=msg_count,
                                display_ip=display_ip, 
                                display_port=display_port,
                                realtime = True)
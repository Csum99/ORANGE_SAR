#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command and control script for PulsON 440 via Pi."""

__author__ = 'Ramamurthy Bhagavatula, Michael Riedl'
__version__ = '1.0'
__maintainer__ = 'Ramamurthy Bhagavatula'
__email__ = 'ramamurthy.bhagavatula@ll.mit.edu'

# Update path
from pathlib import Path
import sys
if Path('..//').resolve().as_posix() not in sys.path:
    sys.path.insert(0, Path('..//').resolve().as_posix())

# Import required modules and methods
import argparse
from common.helper_functions import is_valid_file, yes_or_no, deconflict_file, setup_logger, \
    close_logger
from pulson440.pulson440 import PulsON440
from pulson440.constants import DEFAULT_LOGGER_NAME, DEFAULT_LOGGER_CONFIG, FOREVER_SCAN_COUNT, \
    MIN_SCAN_COUNT, CONTINUOUS_SCAN_INTERVAL, HOST_IP, HOST_PORT, RADAR_IP, RADAR_PORT, \
    DISPLAY_IP, DISPLAY_PORT
import yaml

# Logger setup
try:
    logger_config_filename = (Path(__file__).parent / 'log_config.yml').resolve().as_posix()
    with open(logger_config_filename, 'r') as f:
        logger_config = yaml.load(f, Loader=yaml.FullLoader)
    logger = setup_logger(name=logger_config['name'], config=logger_config['config'])
except Exception:
    logger = setup_logger(name=DEFAULT_LOGGER_NAME, config=DEFAULT_LOGGER_CONFIG)

def parse_args(args, cmd_line):
    """Input argument parser.
    
    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].
        
        cmd_line (bool)
            Indicates whether or not method was called via command line.
    
    Returns:
        parsed_args (namespace)
            Parsed arguments.
            
    Raises:
        ArgumentError if num_scans is not within expected bounds.
        ArgumentError if interval is not within expected bounds.
    """
    parser = argparse.ArgumentParser(
            description=("PulsON 440 command and control script to enable data collection. Users "
                         "specify behavior through arguments that direct the radar to collect " 
                         "either a finite number of scans or until directed to stop via a "
                         "control file. This latter behavior is considered a forever collection " 
                         "mode. To stop a forever collection mode, users should post any "
                         "non-zero value to the control file that was created upon successful "
                         "connection to the radar. On Unix systems it is recommended that users "
                         "run this script as a background process by appending \' &\' to the end "
                         "of the command line call so as to allow single terminal usage of the "
                         "control file."))
    parser.add_argument('scan_data_filename', nargs='?', default=None, 
                        help=("Path and name of file to save radar scans to; default depends on "
                              "mode."))
    parser.add_argument('--host_ip', nargs='?', type=str, const=HOST_IP, default=HOST_IP,
                        help=f"IP address of host. Defaults to '{HOST_IP}'.")
    parser.add_argument('--host_port', type=int, default=HOST_PORT,
                        help=f"Port of host. Defaults to {HOST_PORT}.")
    parser.add_argument('--radar_ip', nargs='?', type=str, const=RADAR_IP, default=RADAR_IP,
                        help=f"IP address of radar. Defaults to '{RADAR_IP}'.")
    parser.add_argument('--radar_port', type=int, default=RADAR_PORT,
                        help=f"Port of radar. Defaults to {RADAR_PORT}.")
    parser.add_argument('--display_ip', nargs='?', type=str, const=DISPLAY_IP, default=DISPLAY_IP, 
                        help=f"IP address of system for displaying the realtime data output. "
                        "Defaults to '{DISPLAY_IP}'.")
    parser.add_argument('--display_port', type=int, default=DISPLAY_PORT,
                        help=f"Port of system for displaying the realtime data output. "
                        "Defaults to {DISPLAY_PORT}.")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-q', '--quick', action='store_true',
                            help=("Perform quick-look mode; saved log file defaults to "
                                  "'quick_look.prd'."))
    mode_group.add_argument('-c', '--collect', action='store_true',
                            help=("Perform collection mode; saved log file defaults to "
                                  "'collect_N.prd' where N ensures uniqueness from any existing "
                                  "files."))
    mode_group.add_argument('-v', '--visual', action='store_true',
                            help=("Output data back to control machine to display output "
                                  "real-time. This does not save the collection "
                                  " data and requires the --display_ip argument"))
    parser.add_argument('-n', '--num_scans', type=int, nargs='?', 
                        const=FOREVER_SCAN_COUNT, default=FOREVER_SCAN_COUNT,
                        help=("Number of scans to collect with '--collect' mode; defaults to "
                              "scanning until directed to stop."))
    parser.add_argument('-i', '--interval', type=int, nargs='?', 
                        const=CONTINUOUS_SCAN_INTERVAL, default=CONTINUOUS_SCAN_INTERVAL,
                        help=("Interval (us) between consecutive scans with '-collect' mode; "
                              "defaults to minimum interval required to enable continuous "
                              "scanning."))
    parser.add_argument('-s', '--settings_file', nargs='?', 
                        const='settings.yml', default='settings.yml',
                        help=("Path and name to radar settings file; defaults to "
                              "'settings.yml'"))
    parser.add_argument('-r', '--return_data', action='store_true',
                        help=("Return collected data; only useful if calling main method in other "
                              "code."))
    parsed_args = parser.parse_args(args)
    
    # Check that number of scans and scan interval are valid values
    if parsed_args.num_scans < MIN_SCAN_COUNT or parsed_args.num_scans > FOREVER_SCAN_COUNT:
        parser.error(f"'--num_scans' argument is not in valid range of {MIN_SCAN_COUNT} and "
                     f"{FOREVER_SCAN_COUNT}!")
    if parsed_args.interval < 0:
        parser.error("--interval cannot have a value less than 0!")
    
    # Set scan data file to default depending on mode if needed
    if parsed_args.scan_data_filename is None:
        if parsed_args.quick:
            parsed_args.scan_data_filename = 'quick_look.prd'
        elif parsed_args.collect:
            parsed_args.scan_data_filename = deconflict_file('collect.prd')
        
    # Avoid overwriting any existing files
    elif Path(parsed_args.scan_data_filename).exists():
        logger.info("Specified scan data file already exists...")
        if cmd_line:
            print("Specified scan data file already exists...")
            yes = yes_or_no("Do you want to overwrite it?")
            if not yes:
                parsed_args.scan_data_filename = deconflict_file(parsed_args.scan_data_filename)
                logger.info(f"Using '{parsed_args.scan_data_filename}' as scan data file.")
        else:
            parsed_args.scan_data_filename = deconflict_file(parsed_args.scan_data_filename)
            logger.info(f"Using {parsed_args.scan_data_filename} as scan data file.")
    
    # Check if files are accessible
    is_valid_file(parser, parsed_args.settings_file, 'r')
    is_valid_file(parser, parsed_args.scan_data_filename, 'w')
    
    return parsed_args

def main(args, cmd_line=False):
    """Main execution method to command radar to collect data.
    
    Args:
        args (list)
            Input arguments as taken from command line execution via sys.argv[1:].
        
        cmd_line (bool)
            Indicates whether or not method was called via command line.
    
    Returns:
        data (str)
            Data read from the radar; needs to unpacked to properly access scan information. Will 
            only be non-empty if return_data input flag is set to True.
    
    Raises:
        ValueError if unrecognized mode is requested.
    """
    logger.info("Starting radar data collection process...")

    # Parse input arguments
    parsed_args = parse_args(args, cmd_line)
    logger.debug(f"Input arguments are --> {parsed_args}")

    # Initialize output
    data = None
    
    try:
        # Initialization
        radar = PulsON440(logger=logger, 
                          host_ip=parsed_args.host_ip, host_port=parsed_args.host_port, 
                          radar_ip=parsed_args.radar_ip, radar_port=parsed_args.radar_port)
        radar.read_settings_file(parsed_args.settings_file)

        # ============================ STUDENT TODO (PIPELINE) ============================
        # Bring the radar session up. The PulsON440 object (created above as `radar`) has
        # methods for each step of the session lifecycle. In order, you must:
        #
        # Step 1: open the connection to the radar        HINT: radar.connect()
        # Step 2: read the radar's current configuration  HINT: radar.get_radar_config()
        # Step 3: push our settings onto the radar        HINT: radar.set_radar_config()
        #
        # (Why both get AND set? The radar's config must be read before it can be safely
        # modified -- discuss with your TA what could go wrong otherwise.)
        # ==================================================================================
        raise NotImplementedError("control.py radar startup: delete once implemented!")

        # Soft kill on ctrl-c
        import signal
        def sigint_handler(sig, frame):
            logger.info("User pressed Ctrl-C; stopping radar data collection")
            radar.stop_scan()
        signal.signal(signal.SIGINT, sigint_handler)

        # Perform specified mode
        if parsed_args.quick:
            data = radar.quick_look(scan_data_filename=parsed_args.scan_data_filename, 
                                    return_data=parsed_args.return_data)
        elif parsed_args.collect:
            data = radar.collect(scan_count=parsed_args.num_scans, 
                                 scan_interval=parsed_args.interval, 
                                 scan_data_filename=parsed_args.scan_data_filename, 
                                 return_data=parsed_args.return_data)
        elif parsed_args.visual:
            data = radar.realtime(scan_count=parsed_args.num_scans, 
                                 scan_interval=parsed_args.interval,
                                 display_ip = parsed_args.display_ip,
                                 display_port = parsed_args.display_port)
        else:
            raise ValueError("Unrecognized mode requested!")
        logger.info("Completed radar data collection process!")

    except Exception:
        logger.exception("Fatal error encountered!")
        
    # Disconnect radar and close logger
    finally:
        radar.disconnect()
        close_logger(logger)
        
    return data
    
if __name__ == '__main__':
    """Standard Python alias for command line execution."""
    main(sys.argv[1:], True)


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helper functions for UAS-SAR."""

__author__ = "Ramamurthy Bhagavatula"
__version__ = "1.0"
__maintainer__ = "Ramamurthy Bhagavatula"
__email__ = "ramamurthy.bhagavatula@ll.mit.edu"

# Import required modules and methods
import logging
import logging.config
import numpy as np
import os
from pathlib import Path
import sys
from warnings import warn

def setup_logger(name, config):
    """Set up logger.
    
    Args:
        name (str)
            Name of logger to configure. Should be consistent w/ config.
            
        config (dict)
            Logger configuration (https://docs.python.org/3.6/library/logging.config.html). If None 
            then no logging is done.
            
    Returns:
        logger (logging.Logger)
            Configured logger.
            
    Raises:
        KeyError if no logger called matching name is present in config.
    """
    if config is None:
        logger = logging.getLogger()
        logger.propagate = False
    else:
        if name not in config['loggers']:
            raise KeyError(('Logger configuration does have entry matching provided name of + '
                            '\'{0}\'').format(name))
        
        for handler in config['handlers']:
            if config['handlers'][handler]['class'] == 'logging.FileHandler':
                filename = Path(config['handlers'][handler]['filename'])
                if filename.suffix.lower() != '.log':
                    config['handlers'][handler]['filename'] = \
                        filename.with_suffix('.log').as_posix()
        
        logging.captureWarnings(True)
        logging.config.dictConfig(config)
        logger = logging.getLogger(name)
    return logger

def close_logger(logger):
    """Close logger.
    
    Args:
        logger (logging.Logger)
            Logger to close.
    """
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)

def progress_bar(step, total, display_fraction=0.05, increment_name='Step', msg='', done=False, 
                 total_len=25, elapsed_time=None):
    """Prints/updates console text progress bar.
    
    Args:
        step (int)
            Current step number out of total.
            
        total (int)
            Total number of steps.
            
        display_fraction (float)
            Fraction of total number of steps which at integer multiples the progress bar will be 
            updated. Defaults to 0.05.
            
        increment_name (str)
            Name of a step. Should stay constant over a given progress bar's lifetime. Defaults to 
            'Step'.
            
        msg (str)
            Message to print after progress bar. Defaults to ''.
        
        done (bool)
            Indicates whether or not to end progress bar on this update.
            
        total_len (int)
            The number of characters to use to show actual progress bar excluding any text. Defaults
            to 25.
            
        elapsed_time (float)
            The amount of time elapsed since the inception of the progress bar. If None then no time
            information will be printed. Defaults to None.
    """
    # Determine how display fraction maps to step and only update progress bar if it is integer 
    # multiple of the display fraction
    display_step = round(display_fraction * total)
    if step % display_step == 0:
        
        # Display constants
        complete_symbol = '='
        current_symbol = '>'
        incomplete_symbol = '.'
        
        # Set fixed maximum width step progress string
        width = len(str(total))
        percent = 100 * step / total
        step_str = '{0} {1:>{2}}/{3}, {4:>5.1f}%'.format(increment_name, step, width, total, 
                    percent)
        
        # Compute current completion
        complete_len = int(round(total_len * step / float(total)))
        incomplete_len = total_len - complete_len
        progress_bar = complete_symbol * complete_len
        progress_bar += (current_symbol * (incomplete_len >= 1) + 
                         incomplete_symbol * (incomplete_len - 1))
        
        # Update message w/ elapsed time if provided
        if elapsed_time is not None:
            msg = '{0}, {1:.1f} seconds elapsed'.format(msg, elapsed_time)
        
        # Print progress bar
        if not done:
            sys.stdout.write('{0} [{1}] {2}\r'.format(step_str, progress_bar, msg))
        else:
            sys.stdout.write('{0} [{1}] {2}\n'.format(step_str, progress_bar, msg))
        sys.stdout.flush()

def deconflict_file(filename):
    """
    Deconflict w/ specified file, if necessary, by extending the name.
    
    Args:
        filename (str)
            File to deconflict with.
        
    Returns:
        new_file (str)
            Path and name of deconflicted file.
    """
    filename = Path(filename)
    if not filename.exists():
        filename.touch()
        return filename.resolve().as_posix()
    else:
        ii = 0
        while filename.with_name('{0}_{1}{2}'.format(filename.stem, ii, filename.suffix)).exists():
            ii += 1
        filename = filename.with_name('{0}_{1}{2}'.format(filename.stem, ii, filename.suffix))
        filename.touch()
        return filename.resolve().as_posix()
    
def yes_or_no(question):
    """Prompts user to answer a "Yes or No" question through keyboard input.
    
    Args:
        question (str)
            Question to ask.
            
    Returns:
        answer (bool)
            True for "Yes" and False for "No".
    """
    # Set of acceptable answer formats
    yes = set(['yes', 'y'])
    no = set(['no', 'n'])
    
    # Iterate till valid answer is given
    while True:
        answer = input(question + " (y/n): ").lower().strip()
        if answer in yes:
            return True
        elif answer in no:
            return False
        else:
            print("Please respond with 'yes' or 'no'")

def is_valid_file(parser, filename, mode):
    """Check if specified argument is a valid file for read or write; meant to be used in the 
    context of argparse.ArgumentParser.
    
    Args:
        parser (arparse.ArgumentParser)
            Instance.
            
        filename (str)
            File to check.
            
        mode (str)
            The read/write mode to check the file for; options are ['r', 'w'].
            
    Raises:
        parser.error if file is not valid for specified mode.
        parser.error if unrecognized mode is specified.
    """
    if filename:
        if mode == 'r':
            try:
                f = open(filename, 'r')
                f.close()
            except:
                parser.error("{0} does not exist or cannot be read!".format(filename))
        elif mode == 'w':
            try:
                f = open(filename, 'w')
                f.close()
                os.remove(filename)
            except:
                parser.error("{0} does not exist or cannot be written to!".format(filename))
        else:
            parser.error("Unrecognized file mode specified!")

def replace_nan(coords, vals):
    """Replace NaN coordinates and values in data using 1-D interpolation. 
    
    Args:
        coords (ndarray) 
            Length M vector containing data coordinates; may have NaNs in it. Assumes that 
            coordinates are uniformly spaced.
            
        vals (ndarray)
            M x N matrix representing data values; may have NaNs in it.
            
    Returns:
        coords_out (ndarray)
            Length M vector of data coordinates with NaNs replaced; should match coords 
            dimensionality.
        
        vals_out (ndarray)
            atrix representing data values with NaNs replaced; 
                   should match input vals dimensionality.
    """
    # Initialize outputs; make a deep copy to ensure that inputs are not directly modified
    coords_out = np.copy(coords)
    vals_out = np.copy(vals)
    
    # Store inputs original shapes
    coords_shape = coords_out.shape
    vals_shape = vals_out.shape
    
    # Remove singleton dimensions from coordinates
    coords_out = np.squeeze(coords_out)
    
    # Check inputs
    if coords_out.ndim != 1:
        raise ValueError('Coordinates are not 1-D!')
        
    if vals_out.ndim > 2:
        raise ValueError('Data must be a 2-D matrix!')
    elif vals_out.ndim == 1:
        vals_out = np.reshape(vals_out, (-1, 1))
        
    dim_match = coords_out.size == np.asarray(vals_shape)
    transpose_flag = False
    if not np.any(dim_match):
        raise IndexError('No apparent dimension agreement between coordinates and data!')
    elif np.all(dim_match):
        warn(('Ambiguous dimensionalities; assuming columns of data are to be interpolated'), 
             Warning)
    elif dim_match[0] != 1:
        vals_out = vals_out.transpose()
        transpose_flag = True
        
    # Determine where NaN coordinates are replace them using linear interpolation assuming uniform 
    # spacing
    uniform_spacing = np.arange(0, coords_out.size)
    coords_nan = np.isnan(coords_out)
    coords_out[coords_nan] = np.interp(uniform_spacing[coords_nan], uniform_spacing[~coords_nan], 
              coords_out[~coords_nan])
    
    # Iterate over each dimension of data
    for ii in range(0, vals_shape[1]):
        
        # Determine where the NaN data and replace them using linear interpolation
        vals_nan = np.isnan(vals_out[:, ii])
        vals_out[vals_nan, ii] = np.interp(coords_out[vals_nan], coords_out[~vals_nan], 
                vals_out[~vals_nan, ii])
        
    # Reshape results to match inputs
    coords_out = np.reshape(coords_out, coords_shape)
    if transpose_flag:
        vals_out = np.transpose(vals_out)
    vals_out = np.reshape(vals_out, vals_shape)
    return coords_out, vals_out
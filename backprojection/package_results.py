#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example code demonstrating how to package backprojection results for submission.

This method and associated command line implementation demonstrates how to package backprojection 
results for submission. This only is guide and if used directly then it should be updated to be
compatible w/ the format of your results.
"""

# Import required modules and methods
import matplotlib.pyplot as plt
import pickle

def display_backprojected_image(backprojected_img, x_axis_bounds, y_axis_bounds, png_filename, 
                                x_label='X (m)', y_label='Y (m)', title='Backprojected Image', 
                                aspect='equal'):
    """Display and save backprojected image with labels.
    
    Args:
        backprojected_img (numpy.ndarray)
            Matrix containing backprojected image. Assumes that rows correspond to y-axis and 
            columns correspond to x-axis.
            
        x_axis_bounds (tuple)
            First element is the minimum/leftmost/first column's x-value while second element is the 
            maximum/rightmost/last column's x-value. These should be in meters.
    
        y_axis_bounds (tuple)
            First element is the minimum/bottom/last row's y-value while second element is the 
            maximum/top/first row's x-value. These should be in meters.
            
        png_filename (str)
            Path and name of PNG file of image to save. Must include PNG extension.
            
        x_label (string)
            X-axis label. Defaults to 'X (m)'.
            
        y_label (string)
            Y-axis label. Defaults to 'Y (m)'
            
        title (string)
            Title of image. Defaults to 'Backprojected Image'.
            
        aspect (string)
            Aspect ratio of displayed image. This should be any of the options supported by
            the 'aspect' keyword argument of matplotlib.pyplot.imshow 
            (https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.imshow.html). Defaults to 
            'equal' so that pixels present their true aspect ratio.
    """
    # Display the backprojected image
    hFig = plt.figure()
    hAx = plt.subplot(111)
    hImg = hAx.imshow(backprojected_img, extent=x_axis_bounds + y_axis_bounds)
    hAx.set_aspect(aspect=aspect)
    hAx.set_xlabel(x_label)
    hAx.set_ylabel(y_label)
    hAx.set_title(title)
    hFig.colorbar(hImg)
    
    # maximzie window before showing and saving
    # TODO: This may need to change depending on you matplotlib backend; refer to this post for 
    # some potential solutions, 
    # https://stackoverflow.com/questions/32428193/saving-matplotlib-graphs-to-image-as-full-screen/32428266
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.show()
    
    # Save the iamge
    hFig.savefig(png_filename)
    
def save_data_pickle(backprojected_img, x_axis, y_axis, pkl_filename):
    """Save data into pickle.
    
    Args:
        backprojected_img (numpy.ndarray)
            Matrix containing backprojected image. Assumes that rows correspond to y-axis and 
            columns correspond to x-axis.
            
        x_axis (numpy.ndarray)
            The x-coordinates of each column in the backprojected image. These should be in meters.
    
        y_axis (tuple)
            The y-coordinates of each row in the backprojected image. These should be in meters.
            
        pkl_filename (str)
            Path and name of pickle file to save.
    """
    # Open and save pickle
    with open(pkl_filename, 'wb') as f:
        data = {'backprojected_img': backprojected_img,
                'x_axis': x_axis,
                'y_axis': y_axis}
        pickle.dump(data, f)

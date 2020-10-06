""" Simple demonstration of the new 3D visualization tool for Madagascar.
The program displays x-, y-, z- slices of a numpy array in 3D, allows user
to interactively drag the slices, includes useful features such as colorbar
and axis legend, and can output the figure to .png file with various resolution.
python seamai_label_demo.py --filepath seamai_data/labels_train.npz
python seamai_label_demo.py --filepath seamai_data/submission.npz

"""
import argparse

import numpy as np
from vispy.color import get_colormap, Colormap, Color

from seismic_canvas import (SeismicCanvas, volume_slices, XYZAxis, Colorbar)

# Create the parser
my_parser = argparse.ArgumentParser(description='file path to viz')

# Add the arguments
my_parser.add_argument('--filepath',
                      # metavar='path',
                       type=str,
                       help='the path to file')

if __name__ == '__main__':

  args = my_parser.parse_args()
 #volume = np.load('./data_train.npz')["data"] 
  if args.filepath ==  "seamai_data/labels_train.npz":
      volume = np.load(args.filepath)["labels"] 
  else:
      volume = np.load(args.filepath)["prediction"].astype(np.int8) 
  volume = volume.transpose(1,2,0)
  print(volume.shape,volume.dtype) #(1006, 782, 590) z,x,y ==> (782,590,1006) ||
  axis_scales = (0.7, 0.5, 1) # anisotropic axes (stretch z-axis)

  # Colormaps.
  cmap=Colormap([[1,0,0], [0,1,0], [0,0,1]]); clim=(1, 6)
  # Get visual nodes ready.
  visual_nodes = volume_slices(volume,
    cmaps=cmap, clims=clim,
    # x_pos=32, y_pos=25, z_pos=93)
    x_pos=volume.shape[0]-1, y_pos=volume.shape[1]-1, z_pos=0)
  xyz_axis = XYZAxis()
  colorbar = Colorbar(cmap=cmap, clim=clim, label_str='Labels',
                      label_size=8, tick_size=6)


  # Run the canvas.
  canvas = SeismicCanvas(title='Labels Interactive Demo',
                         visual_nodes=visual_nodes,
                         xyz_axis=xyz_axis,
                         colorbar=colorbar,
                         # Set the option below=0 will hide the colorbar region
                         # colorbar_region_ratio=0,
                         axis_scales=axis_scales,
                         # Manual camera setting below.
                         # auto_range=False,
                         # scale_factor=972.794,
                         # center=(434.46, 545.63, 10.26),
                         fov=30,
                         elevation=36,
                         azimuth=45,
                         zoom_factor=1.2 # >1: zoom in; <1: zoom out
                         )
  canvas.measure_fps()
  canvas.app.run()

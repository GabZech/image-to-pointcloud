#%%
import os
os.chdir('/Users/nassimzoueini/Documents/GitHub/image-to-pointcloud/')

#%%

### VISUALISE LAS FILE ###

import laspy
import numpy as np

#las_file = "50521070.las" # ok
#las_file = "50521231.las" # noisy
#las_file = "50526618.las" # has an umbrella on the image, check if it is in the point cloud
las_file = "50521231.las" # noisy
folder_files = "data/processed/pcs/"

las = laspy.read(f"{folder_files}{las_file}")
point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))


#%%

### VISUALISE JSON FILE ###

import json
import numpy as np

#ann_path = "datasets/train/annotation/264198353.json"
#ann_path = "data/processed/pcs/50532955.json"
# ann_path = r"data\run2\processed\pcs\saddle_roofs\76227427.json" # PARKING LOT
#ann_path = r"data\run2\processed\pcs\saddle_roofs\11909446.json"
#ann_path = r"data\run2\processed\pcs\clean_saddle_roofs\2521411.json"

#ann_path = r"data\all\processed\pcs\tent_roofs\11909446.json"
#ann_path = r"data\all\processed\pcs\tent_roofs_clean\129092157.json"

#ann_path = 'datasets/4_surfaces/test/annotation/10388590.json'
ann_path = 'datasets/4_surfaces/test_jsons/10388590.json'

f = open(ann_path)
ann = json.load(f)
f.close()

point_data = np.array(ann["lidar"])

#point_data = point_data.transpose((1, 0))

#%%

### VISUALISE RES FILE ###

import torch

key_to_find = 88642079

results = torch.load('datasets/results_300/test.res', map_location=torch.device('cpu'))
for dictionary in results:
    if key_to_find in dictionary:
        result_dict = dictionary[key_to_find]
        break

point_data = result_dict['final_out'].numpy()

#%%

import open3d as o3d

geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom],
                                  width=int(1920/2), height=int(1080/2),
                                  left=10, top=10,
                                  )

# %%

import open3d as o3d

# We create a visualizer object that will contain references to the created window, the 3D objects and will listen to callbacks for key presses, animations, etc.
vis = o3d.visualization.Visualizer()
# New window, where we can set the name, the width and height, as well as the position on the screen
vis.create_window(window_name='Building', width=800, height=600)

# We call add_geometry to add a mesh or point cloud to the visualizer
geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
vis.add_geometry(geom)

ctrl = vis.get_view_control()
# #ctrl.rotate(5, 0)
parameters = o3d.io.read_pinhole_camera_parameters("ScreenCamera_2023-04-20-00-44-38.json")
ctrl.convert_from_pinhole_camera_parameters(parameters)
vis.update_renderer()

vis.run()
# Once the visualizer is closed destroy the window and clean up

vis.destroy_window()
# %%

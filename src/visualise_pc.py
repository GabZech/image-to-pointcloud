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
ann_path = "data/processed/pcs/50532955.json"


f = open(ann_path)
ann = json.load(f)
f.close()

point_data = np.array(ann["lidar"])

#point_data = point_data.transpose((1, 0))

#%%

### VISUALISE RES FILE ###

import torch

results = torch.load('data/results/sat2pc/test.res', map_location=torch.device('cpu'))

point_data = results[0][list(results[0].keys())[0]]['final_out'].numpy()

#%%

import open3d as o3d

geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom],
                                  width=int(1920/2), height=int(1080/2),
                                  left=10, top=10
                                  )

# %%

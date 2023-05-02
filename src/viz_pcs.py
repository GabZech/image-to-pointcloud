#%% VIZ JSON FILE
import json
import numpy as np
import open3d as o3d

building_id = 56149218

ann_path = f'data/all/processed/pcs/saddle_roofs/{building_id}.json'
#ann_path = f'datasets/2_surfaces/test/annotation/{building_id}.json'
#ann_path = f'datasets/2_surfaces/test_jsons/{building_id}.json'

f = open(ann_path)
ann = json.load(f)
f.close()

point_data = np.array(ann["lidar"])

point_data = point_data.astype(np.float32)
point_data -= np.mean(point_data, axis=0).astype(np.float32)

# We create a visualizer object that will contain references to the created window, the 3D objects and will listen to callbacks for key presses, animations, etc.
vis = o3d.visualization.Visualizer()
vis.create_window(width=1920, height=1080)

# We call add_geometry to add a mesh or point cloud to the visualizer
geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
vis.add_geometry(geom)

opt = vis.get_render_option()
opt.background_color = np.asarray([255, 255, 255])

vis.run()
vis.destroy_window()

### ALTERNATIVE DATA FORMATS ###

#%% LOAD LAS FILE

import laspy
import numpy as np

def read_las(las_file_path):
    ''' Read a .las file and return the point cloud data.

    Args:
        las_file_path (str): Path to the .las file.

    Returns:
        point_data (np.ndarray): Point cloud data.
    '''
    las = laspy.read(las_file_path)
    point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))

    return point_data


#%% LOAD RES FILE

import torch

def load_res(res_file_path, building_id):
    ''' Load the results from a .res file and return the point cloud data for the specified building.

    Args:
        res_file_path (str): Path to the .res file.
        building_id (int): ID of the building.

    Returns:
        point_data (np.ndarray): Point cloud data for the specified building.
    '''

    results = torch.load(res_file_path, map_location=torch.device('cpu'))
    for dictionary in results:
        if building_id in dictionary:
            result_dict = dictionary[building_id]
            break

    point_data = result_dict['final_out'].numpy()

    return point_data
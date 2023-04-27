import json
import numpy as np

ann_path = r'data\run2\processed\pcs\saddle_roofs/11914427.json'
#ann_path = 'datasets/2_surfaces/test/annotation/11914427.json'
#ann_path = 'datasets/2_surfaces/test_jsons/11914427.json'

# ann_path = 'data/run2/processed/pcs/saddle_roofs/56149218 .json'
# ann_path = 'data/run2/processed/pcs/clean_saddle_roofs/56149218 .json'

one_surface = 103056863

# import os
# dir = r"C:\Users\zech011\win-repos\hertie\image-to-pointcloud\data\run2\processed\pcs\saddle_roofs"
# file = np.random.choice(os.listdir(dir))
# print(file)
# ann_path = f"{dir}/{file}"

f = open(ann_path)
ann = json.load(f)
f.close()

point_data = np.array(ann["lidar"])

point_data = point_data.astype(np.float32)
point_data -= np.mean(point_data, axis=0).astype(np.float32)


import open3d as o3d

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


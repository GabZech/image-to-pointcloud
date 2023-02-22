las_file = "50521070.las" # ok
#las_file = "50521231.las" # noisy
folder_files = "data/processed/pcs/"

import laspy
import numpy as np
import open3d as o3d

las = laspy.read(f"{folder_files}{las_file}")

point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))

geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom],
                                  width=int(1920/2), height=int(1080/2),
                                  left=10, top=10
                                  )
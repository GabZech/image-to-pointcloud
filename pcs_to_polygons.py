import numpy as np
import laspy as laspy
import pyvista as pv
import json
import open3d as o3d

pointsList=[]
with open('data/processed/pcs/50520652.json') as f:
    for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])

# print(pointsList)
points=np.asarray(pointsList, dtype=np.float32)
#print(points.shape)
points=points[0,:,:]
#print(points.shape)

#pcd_data=points
pcd = o3d.geometry.PointCloud()
pcd.points=o3d.utility.Vector3dVector(points)
#o3d.visualization.draw_geometries([pcd])
                                #   zoom=0.3412,
                                #   front=[0.4257, -0.2125, -0.8795],
                                #   lookat=[2.6172, 2.0475, 1.532],
                                #   up=[-0.0694, -0.9768, 0.2024])
def display_inlier_outlier(cloud, ind):
    inlier_cloud = cloud.select_by_index(ind)
    outlier_cloud = cloud.select_by_index(ind, invert=True)

    
    outlier_cloud.paint_uniform_color([1, 0, 0])
    inlier_cloud.paint_uniform_color([0.8, 0.8, 0.8])
    o3d.visualization.draw_geometries([inlier_cloud, outlier_cloud])
    return inlier_cloud
# cl, ind = pcd.remove_statistical_outlier(nb_neighbors=3,
#                                                     std_ratio=0.02)
cl, ind = pcd.remove_radius_outlier(nb_points=16, radius=0.05)

pcld=display_inlier_outlier(pcd, ind)
pcld_points=np.asarray(pointsList, dtype=np.float32)
pcld_points=pcld_points[0,:,:]
point_cloud=pv.PolyData(pcld_points)
mesh=point_cloud.reconstruct_surface()
# #mesh.save('mesh.stl')
#point_cloud.plot(eye_dome_lighting=True)
mesh.plot(color='green')

# point_cloud=points
# point_cloud[:, 2] *= 0.1
# plane, center, normal = pv.fit_plane_to_points(point_cloud, return_meta=True)
# pl = pv.Plotter()
# _ = pl.add_mesh(plane, color='tan', style='wireframe', line_width=4)
# _ = pl.add_points(point_cloud, render_points_as_spheres=True, color='r', point_size=1)
# pl.show()
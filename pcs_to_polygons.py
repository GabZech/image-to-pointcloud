#%%
import numpy as np
import laspy as laspy
import pyvista as pv
import json
import open3d as o3d
import matplotlib.pyplot as plt
#Always work on 50526389
#Test on this 50520918
pointsList=[]
with open('data/processed/pcs/50521231.json') as f:
    for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])

# print(pointsList)
points=np.asarray(pointsList, dtype=np.float32)
points=points[0,:,:]
pcd = o3d.geometry.PointCloud()
pcd.points=o3d.utility.Vector3dVector(points)


#pcd, ind = pcd.remove_statistical_outlier(nb_neighbors=3,std_ratio=1)
# pcd, ind = pcd.remove_radius_outlier(nb_points=12, radius=50)

# Flipping pointcloud,so it's not upside down.
#pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

## Plane Segmentation and Removal
# inlier_cloud=1
# while inlier_cloud!=pcd:
#      plane_model, inliers = pcd.segment_plane(distance_threshold=10,
#                                              ransac_n=3,
#                                              num_iterations=1000)
#      [a, b, c, d] = plane_model
#      print(f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
#      print("Displaying pointcloud with planar points in red ...")
#      inlier_cloud = pcd.select_by_index(inliers)
#      inlier_cloud.paint_uniform_color([1.0, 0, 0])
#      outlier_cloud = pcd.select_by_index(inliers, invert=True)
#      o3d.visualization.draw([inlier_cloud, outlier_cloud])
#      pcd=outlier_cloud
max_plane_idx=5  

segment_models={}
segments={}
roof = {"id":[],"pts":[],"vector":[],"inclination":[]};

rest=pcd
d_threshold=100

for i in range(max_plane_idx):
    colors = plt.get_cmap("tab20")(i)
    segment_models[i], inliers = rest.segment_plane(distance_threshold=15,ransac_n=3,num_iterations=10000)
    [a, b, c, d] = segment_models[i]
    print("Displaying pointcloud with planar points in",i+1, "th segment",f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
    angle=np.fix(np.arccos(c)*180/np.pi%90)
    print("Inclination=",angle, "°")
    segments[i]=rest.select_by_index(inliers)
    labels = np.array(segments[i].cluster_dbscan(eps=d_threshold*100, min_points=10))
    candidates=[len(np.where(labels==j)[0]) for j in np.unique(labels)]
    best_candidate=int(np.unique(labels)[np.where(candidates== np.max(candidates))[0]])
    segments[i].paint_uniform_color(list(colors[:3]))
    rest = rest.select_by_index(inliers, invert=True) + segments[i].select_by_index(list(np.where(labels!=best_candidate)[0]))
    segments[i]=segments[i].select_by_index(list(np.where(labels== best_candidate)[0]))
    print("pass",i,"/",max_plane_idx,"done.")

    

    roof["id"].append(i)
    roof["pts"].append(np.asarray(segments[i]))
    roof["vector"].append([a,b,c,d])
    roof["inclination"].append(angle)	

roof.get('inclination')

labels = np.array(rest.cluster_dbscan(eps=0.05, min_points=5))
max_label = labels.max()
print(f"point cloud has {max_label + 1} clusters")
colors = plt.get_cmap("tab10")(labels / (max_label if max_label > 0 else 1))
colors[labels < 0] = 0
rest.colors = o3d.utility.Vector3dVector(colors[:, :3])
o3d.visualization.draw([segments[i] for i in range(max_plane_idx)])#+[rest])
#print(roof)

# %%

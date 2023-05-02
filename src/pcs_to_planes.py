#%%
import numpy as np
import laspy as laspy
import pyvista as pv
import json
import open3d as o3d
import matplotlib.pyplot as plt
#Always work on 50526389
#Test on this 50520918
#saddle_331119023
pointsList=[]
with open('data/finetuning_saddle_only/test/annotation/332437499.json') as f:
    name=29206935
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
#
#Reference https://towardsdatascience.com/how-to-automate-3d-point-cloud-segmentation-and-clustering-with-python-343c9039e4f5
max_plane_idx=2

segment_models={}
segments={}
roof={}
keys=['id','pane','points', 'vector', 'inclination']

rest=pcd
d_threshold=100

for i in range(max_plane_idx):
    colors = plt.get_cmap("tab20")(i)
    segment_models[i], inliers = rest.segment_plane(distance_threshold=15,ransac_n=3,num_iterations=1000)
    [a, b, c, d] = segment_models[i]
    print("Displaying pointcloud with planar points in roof segment no.",i+1,f"\n Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
    angle=round(np.arccos(c)*180/np.pi%90,2)
    print("Inclination=",angle, "°")
    segments[i]=rest.select_by_index(inliers)
    labels = np.array(segments[i].cluster_dbscan(eps=d_threshold*100, min_points=10))
    candidates=[len(np.where(labels==j)[0]) for j in np.unique(labels)]
    best_candidate=int(np.unique(labels)[np.where(candidates== np.max(candidates))[0]])
    segments[i].paint_uniform_color(list(colors[:3]))
    rest = rest.select_by_index(inliers, invert=True) + segments[i].select_by_index(list(np.where(labels!=best_candidate)[0]))
    segments[i]=segments[i].select_by_index(list(np.where(labels== best_candidate)[0]))
    print("pass",i,"/",max_plane_idx,"done.")

    
    id= name
    pane= "roof_pane_" + str(i+1)
    pts=np.asarray(segments[i]).tolist()
    vector=[a,b,c,d]
    inclination=angle

    values=[id, pane,points, vector,inclination]
    for k in range(len(keys)):
        roof[keys[k]]=values[k]
    
    #roof[key]={"id":id, "pts":pts, "vector":vector, "inclination":inclination}		

roof.get('inclination')

labels = np.array(rest.cluster_dbscan(eps=0.05, min_points=5))
max_label = labels.max()
print(f"point cloud has {max_label + 1} clusters")
colors = plt.get_cmap("tab10")(labels / (max_label if max_label > 0 else 1))
colors[labels < 0] = 0
rest.colors = o3d.utility.Vector3dVector(colors[:, :3])
o3d.visualization.draw([segments[i] for i in range(max_plane_idx)]+[rest])
#print(roof)


#%%
import numpy as np
import laspy as laspy
import pyvista as pv
import json
import open3d as o3d
import matplotlib.pyplot as plt
import os

pointsList=[]
with open('data/finetuning_tent_only/res_jsons/14993289.json') as f:
    name=29206935
    for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])

# print(pointsList)
points=np.asarray(pointsList, dtype=np.float32)
points=points[0,:,:]
pcd = o3d.geometry.PointCloud()
pcd.points=o3d.utility.Vector3dVector(points)

max_plane_idx=4

segment_models={}
segments={}
roof={}

rest=pcd
d_threshold=100

for i in range(max_plane_idx):
    colors = plt.get_cmap("tab20")(i)
    segment_models[i], inliers = rest.segment_plane(distance_threshold=15,ransac_n=3,num_iterations=1000)
    [a, b, c, d] = segment_models[i]
    print("Displaying pointcloud with planar points in roof segment no.",i+1,f"\n Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
    angle=round(np.arccos(c)*180/np.pi%90,2)
    print("Inclination=",angle, "°")
    segments[i]=rest.select_by_index(inliers)
    labels = np.array(segments[i].cluster_dbscan(eps=d_threshold*100, min_points=10))
    candidates=[len(np.where(labels==j)[0]) for j in np.unique(labels)]
    best_candidate=int(np.unique(labels)[np.where(candidates== np.max(candidates))[0]])
    segments[i].paint_uniform_color(list(colors[:3]))
    rest = rest.select_by_index(inliers, invert=True) + segments[i].select_by_index(list(np.where(labels!=best_candidate)[0]))
    segments[i]=segments[i].select_by_index(list(np.where(labels== best_candidate)[0]))
    print("pass",i,"/",max_plane_idx,"done.")

    
    # key=name
    # pane= "roof_pane_" + str(i+1)
    # pts=np.asarray(segments[i]).tolist()
    # vector=[a,b,c,d]
    # inclination=angle
    # roof.update=({"id":key,"pane":pane, "pts":pts, "vector":vector, "inclination":inclination}	)

# roof.get('inclination')

labels = np.array(rest.cluster_dbscan(eps=0.05, min_points=5))
max_label = labels.max()
print(f"point cloud has {max_label + 1} clusters")
colors = plt.get_cmap("tab10")(labels / (max_label if max_label > 0 else 1))
colors[labels < 0] = 0
rest.colors = o3d.utility.Vector3dVector(colors[:, :3])
o3d.visualization.draw([segments[i] for i in range(max_plane_idx)]+[rest])

# %%
import numpy as np
import json
import open3d as o3d
import os

# input and output folder paths
labels_folder = 'data/finetuning_saddle_only/test/annotation'
predictions_folder='data/finetuning_saddle_only/test_jsons'

#Read the files 
j=0
for filename in os.listdir(labels_folder):
    j=j+1
    if filename.endswith('.json'):
     #Create an array to read the json file into
     pointsList=[]
     # read the input JSON file
     with open(os.path.join(labels_folder, filename), 'r') as f:
         name=os.path.splitext(filename)[0]
         for jsonObj in f:
            pt_coord=json.loads(jsonObj)
            pointsList.append(pt_coord['lidar'])

     # print(pointsList)
    points=np.asarray(pointsList, dtype=np.float32)
    points=points[0,:,:]
    pcd = o3d.geometry.PointCloud()
    pcd.points=o3d.utility.Vector3dVector(points)

    max_plane_idx=2

    segment_models={}
    segments={}
    roof={}
    id= name
    rest=pcd
    d_threshold=100

    for i in range(max_plane_idx):
        #colors = plt.get_cmap("tab20")(i)
        segment_models[i], inliers = rest.segment_plane(distance_threshold=15,ransac_n=3,num_iterations=1000)
        [a, b, c, d] = segment_models[i]
        #print("Displaying pointcloud with planar points in roof segment no.",i+1,f"\n Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
        angle=round(np.arccos(c)*180/np.pi%90,2)
        #print("Inclination=",angle, "°")
        segments[i]=rest.select_by_index(inliers)
        labels = np.array(segments[i].cluster_dbscan(eps=d_threshold*100, min_points=10))
        candidates=[len(np.where(labels==j)[0]) for j in np.unique(labels)]
        best_candidate=int(np.unique(labels)[np.where(candidates== np.max(candidates))[0]])
        #segments[i].paint_uniform_color(list(colors[:3]))
        rest = rest.select_by_index(inliers, invert=True) + segments[i].select_by_index(list(np.where(labels!=best_candidate)[0]))
        segments[i]=segments[i].select_by_index(list(np.where(labels== best_candidate)[0]))
        #print("pass",i,"/",max_plane_idx,"done.")

    
        # pane= "roof_pane_" + str(i+1)
    
        # pts=np.asarray(segments[i]).tolist()
        # vector=[a,b,c,d]
        # inclination=angle
        # roof.update({"id":id,"pane":pane, "pts":pts, "vector":vector, "inclination":inclination})	

    # roof.get('inclination')

    # labels = np.array(rest.cluster_dbscan(eps=0.05, min_points=5))
    # # max_label = labels.max()
    # if j%5==0:
    #     print(j,"buildings done")
 


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
#
#Reference https://towardsdatascience.com/how-to-automate-3d-point-cloud-segmentation-and-clustering-with-python-343c9039e4f5
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
o3d.visualization.draw([segments[i] for i in range(max_plane_idx)]+[rest])
#print(roof)


# %%
import open3d as o3d
import numpy as np

# Load point cloud from file


# Estimate normals for each point
pcd.estimate_normals()

# Set RANSAC parameters
distance_threshold = 10
ransac_n = 3
num_iterations = 1000

# Run RANSAC plane detection
plane_model, inliers = pcd.segment_plane(distance_threshold, ransac_n, num_iterations)

# Extract plane points
plane_points = np.asarray(pcd.points)[inliers]

# Visualize plane points
o3d.visualization.draw_geometries([o3d.geometry.PointCloud(points=o3d.utility.Vector3dVector(plane_points))])

# %%
import itertools
range_probability = np.arange(0.01, 0.9, 0.4)
range_min_points = np.arange(4, 50, 20)
range_epsilon = np.arange(0.25, 10, 3)
range_cluster_epsilon = np.arange(0.25, 10, 3)
range_normal_threshold = np.arange(0.01, 0.9, 0.4)

a=[]
a.append(list(range_probability))
a.append(list(range_min_points))
a.append(list(range_epsilon))
a.append(list(range_cluster_epsilon))
a.append(list(range_normal_threshold))
all_combis = np.array(list(itertools.product(*a)))
sample_combis = all_combis[np.random.randint(0, high=len(all_combis), size=20)]

counter=0
gridsearch_stats=[]
for sample_combi in sample_combis:
    probability, min_points,epsilon, cluster_epsilon, normal_threshold = sample_combi
    created_planes = False
    counter+=1
    if counter==20:
        break
    try:
        print(counter,'trying', probability, min_points,
              epsilon, cluster_epsilon, normal_threshold)
        polyfit_out_surfaces = plydir+'/%s_test_fitted_%s_%s_%s_%s_%s.off' % (
            row.gmlid, probability, min_points, epsilon, cluster_epsilon, normal_threshold)
        polyfit_out_meshes = plydir+'/%s_test_meshes_%s_%s_%s_%s_%s.ply' % (
            row.gmlid, probability, min_points, epsilon, cluster_epsilon, normal_threshold)
        polyfit_call = polyfit_exe+' %s %s %s %s %s %s %s %s' % (curr_plyfile,
                                                                 polyfit_out_surfaces,
                                                                 polyfit_out_meshes,
                                                                 probability, min_points, epsilon,
                                                                 cluster_epsilon, normal_threshold)
        proc1 = subprocess.check_output(polyfit_call, shell=True) 
        created_planes = True
    except Exception as e:
        print(e)
        gridsearch_stats.append([probability, min_points, epsilon,
        cluster_epsilon, normal_threshold,0, 0]) 

    if created_planes:
        currtime=time.asctime(time.localtime(time.time()))
        print(counter, currtime,'worked', probability, min_points,
              epsilon, cluster_epsilon, normal_threshold)
# %%

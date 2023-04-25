import numpy as np
import json
import open3d as o3d
import os
import pandas as pd

def angle_df(file,s):

    filename = file.split(".")[0].split("/")[-1]

    pointsList=[]
    with open(file) as f:
     
     for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])

    # print(pointsList)
    points=np.asarray(pointsList, dtype=np.float32)
    points=points[0,:,:]
    pcd = o3d.geometry.PointCloud()
    pcd.points=o3d.utility.Vector3dVector(points)



    segment_models={}
    segments={}
    

    rest=pcd
    d_threshold=100
    entry=pd.DataFrame()
   
    entry_=pd.DataFrame()
    for i in range(s):
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
        vector=[]
        vector.append([a,b,c])
        
        
        entry_["building_id"] = [filename]
        entry_["pane"]=[i+1]
        entry_["normal_vector"]=vector
        entry_["inclination"]=angle
        
        entry=pd.concat([entry,entry_], axis=0)
    #pts=np.asarray(segments[i]).tolist()
    
    return entry   




labels_folder = 'data/finetuning_saddle_only/test/annotation'
predictions_folder='data/finetuning_saddle_only/test_jsons'
inclination_gt=pd.DataFrame()
inclination_pd=pd.DataFrame()

inclinations_eval=pd.DataFrame()
df=pd.DataFrame()
for filename in os.listdir(labels_folder):
    
    if filename.endswith('.json'):
        df=angle_df(f"{labels_folder}/{filename}",2)
    #if j%5==0:
     #   print(j,"buildings done")
    inclination_gt=pd.concat([inclination_gt,df],axis=0)
inclination_gt.rename(columns={"inclination": "inclination_gt"}, inplace=True)
# import matplotlib.pyplot as plt
# inclination_df["inclination"].hist(bins=20)
# plt.show()
df=pd.DataFrame()
for filename in os.listdir(predictions_folder):
    
    if filename.endswith('.json'):
        df=angle_df(f"{predictions_folder}/{filename}",2)
    #if j%5==0:
     #   print(j,"buildings done")
    inclination_pd=pd.concat([inclination_pd,df],axis=0)
inclination_pd.rename(columns={"inclination": "inclination_pd"}, inplace=True)
inclinations_eval = pd.merge(inclination_gt, inclination_pd, on=['building_id', 'pane'], how='inner').reset_index(drop=True)
inclinations_eval["err"]=abs(inclinations_eval["inclination_gt"]-inclinations_eval["inclination_pd"])
import matplotlib.pyplot as plt
inclinations_eval["err"].hist(bins=20)
plt.show()
count = (inclinations_eval['err'] > 5).sum()
#%%

buildings_to_exclude =[76222797, # not saddle
                        56149218, # weird shape
                        332437499, # 2 dormers
                        103056683, # building badly cut
                        17675858, # flat roof
                        11914427, # two roofs, cropped to 1
                        74606032, # building badly cut
                        131539036, # has big extruding object
                        17681408, # weird shape
                        31244991, # has wall
                        ]

buildings_to_exclude = [str(x) for x in buildings_to_exclude]

#%% Error Evaluation for saddle roofs
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
        #entry_["pane"]=[i+1]
        entry_["normal_vector"+str(i+1)]=vector
        entry_["inclination"+str(i+1)]=angle

    entry=pd.concat([entry,entry_], axis=0)
    #pts=np.asarray(segments[i]).tolist()

    return entry




labels_folder = r'C:\Users\zech011\OneDrive\datasets_thesis/finetuning_saddle_only/test/annotation'
predictions_folder=r'C:\Users\zech011\OneDrive\datasets_thesis/finetuning_saddle_only/test_jsons'
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
inclination_gt.rename(columns={"inclination1": "inclination1_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector1": "normal_vector1_gt"}, inplace=True)
inclination_gt.rename(columns={"inclination2": "inclination2_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector2": "normal_vector2_gt"}, inplace=True)
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
inclination_pd.rename(columns={"inclination1": "inclination1_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector1": "normal_vector1_pd"}, inplace=True)
inclination_pd.rename(columns={"inclination2": "inclination2_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector2": "normal_vector2_pd"}, inplace=True)

inclinations_eval = pd.merge(inclination_gt, inclination_pd, on=['building_id'], how='inner').reset_index(drop=True)
inclinations_eval["normal_array1_gt"]=inclinations_eval["normal_vector1_gt"].apply(np.array)
inclinations_eval["normal_array1_pd"]=inclinations_eval["normal_vector1_pd"].apply(np.array)
inclinations_eval["normal_array2_gt"]=inclinations_eval["normal_vector2_gt"].apply(np.array)
inclinations_eval["normal_array2_pd"]=inclinations_eval["normal_vector2_pd"].apply(np.array)
inclinations_eval = inclinations_eval.drop('normal_vector1_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector2_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector1_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector2_pd', axis=1)

for index,row in inclinations_eval.iterrows():
    # if row["building_id"] == "38747711":
    #     print(row["building_id"])
    s1=[]
    s2=[]

    for i in range(2):
        for j in range(2):

            if i == 0:
                s1.append(np.dot(row['normal_array1_gt'][i],row['normal_array1_pd'][j]))
            elif i == 1:
                s2.append(np.dot(row['normal_array2_gt'][i],row['normal_array2_pd'][j]))


    for k, l in enumerate([s1,s2]):
        k = k + 1
        #print(k)
        # get index of max value
        max_index = l.index(np.asarray(l).max()) + 1
        inclinations_eval.loc[index, f"err_{k}"] = abs(row[f"inclination{max_index}_pd"]-row[f"inclination{k}_gt"])

                # if np.dot(row['t_gt'][i],row['t_pd'][j]):
                #     max=np.dot(row['t_gt'][i],row['t_pd'][j])
            #     inclinations_eval.loc[index, "err"+str(i+1)+"_"+str(j+1)] = abs(row[f"inclination{j+1}_pd"]-row[f"inclination{i+1}_gt"])

mean1 = inclinations_eval["err_1"].mean()
mean2 = inclinations_eval["err_2"].mean()


print(f"Mean with all buildings: {(mean1+mean2)/2}")

# remove buildings in the list above
inclinations_eval = inclinations_eval[~inclinations_eval["building_id"].isin(buildings_to_exclude)]

mean1 = inclinations_eval["err_1"].mean()
mean2 = inclinations_eval["err_2"].mean()


print(f"Mean with removed buildings: {(mean1+mean2)/2}")








#%% Error Evaluation for tent roofs
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
        #entry_["pane"]=[i+1]
        entry_["normal_vector"+str(i+1)]=vector
        entry_["inclination"+str(i+1)]=angle

    entry=pd.concat([entry,entry_], axis=0)
    #pts=np.asarray(segments[i]).tolist()

    return entry




labels_folder = r'C:\Users\zech011\OneDrive\datasets_thesis/finetuning_tent_only/test/annotation'
predictions_folder=r'C:\Users\zech011\OneDrive\datasets_thesis/finetuning_tent_only/test_jsons'
inclination_gt=pd.DataFrame()
inclination_pd=pd.DataFrame()

inclinations_eval=pd.DataFrame()
df=pd.DataFrame()
for filename in os.listdir(labels_folder):

    if filename.endswith('.json'):
        df=angle_df(f"{labels_folder}/{filename}",4)
    #if j%5==0:
     #   print(j,"buildings done")
    inclination_gt=pd.concat([inclination_gt,df],axis=0)
inclination_gt.rename(columns={"inclination1": "inclination1_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector1": "normal_vector1_gt"}, inplace=True)
inclination_gt.rename(columns={"inclination2": "inclination2_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector2": "normal_vector2_gt"}, inplace=True)
inclination_gt.rename(columns={"inclination3": "inclination3_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector3": "normal_vector3_gt"}, inplace=True)
inclination_gt.rename(columns={"inclination4": "inclination4_gt"}, inplace=True)
inclination_gt.rename(columns={"normal_vector4": "normal_vector4_gt"}, inplace=True)
# import matplotlib.pyplot as plt
# inclination_df["inclination"].hist(bins=20)
# plt.show()
df=pd.DataFrame()
for filename in os.listdir(predictions_folder):

    if filename.endswith('.json'):
        df=angle_df(f"{predictions_folder}/{filename}",4)
    #if j%5==0:
     #   print(j,"buildings done")
    inclination_pd=pd.concat([inclination_pd,df],axis=0)
inclination_pd.rename(columns={"inclination1": "inclination1_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector1": "normal_vector1_pd"}, inplace=True)
inclination_pd.rename(columns={"inclination2": "inclination2_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector2": "normal_vector2_pd"}, inplace=True)
inclination_pd.rename(columns={"inclination3": "inclination3_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector3": "normal_vector3_pd"}, inplace=True)
inclination_pd.rename(columns={"inclination4": "inclination4_pd"}, inplace=True)
inclination_pd.rename(columns={"normal_vector4": "normal_vector4_pd"}, inplace=True)

inclinations_eval = pd.merge(inclination_gt, inclination_pd, on=['building_id'], how='inner').reset_index(drop=True)

inclinations_eval["normal_array1_gt"]=inclinations_eval["normal_vector1_gt"].apply(np.array)
inclinations_eval["normal_array2_gt"]=inclinations_eval["normal_vector2_gt"].apply(np.array)
inclinations_eval["normal_array3_gt"]=inclinations_eval["normal_vector3_gt"].apply(np.array)
inclinations_eval["normal_array4_gt"]=inclinations_eval["normal_vector4_gt"].apply(np.array)

inclinations_eval["normal_array1_pd"]=inclinations_eval["normal_vector1_pd"].apply(np.array)
inclinations_eval["normal_array2_pd"]=inclinations_eval["normal_vector2_pd"].apply(np.array)
inclinations_eval["normal_array3_pd"]=inclinations_eval["normal_vector3_pd"].apply(np.array)
inclinations_eval["normal_array4_pd"]=inclinations_eval["normal_vector4_pd"].apply(np.array)

inclinations_eval = inclinations_eval.drop('normal_vector1_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector2_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector1_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector2_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector3_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector3_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector4_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_vector4_pd', axis=1)

inclinations_eval['t_gt'] = inclinations_eval.apply(lambda x: [x['normal_array1_gt'], x['normal_array2_gt'], x['normal_array3_gt'], x['normal_array4_gt']], axis=1)

inclinations_eval['t_pd'] = inclinations_eval.apply(lambda x: [x['normal_array1_pd'], x['normal_array2_pd'], x['normal_array3_pd'], x['normal_array4_pd']], axis=1)

inclinations_eval = inclinations_eval.drop('normal_array1_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array2_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array1_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array2_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array3_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array3_pd', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array4_gt', axis=1)
inclinations_eval = inclinations_eval.drop('normal_array4_pd', axis=1)


# for index,row in inclinations_eval.iterrows():
#     for i in range(4):
#         for j in range(i,4):
#             inclinations_eval["dot_product"+str(i+1)+"_"+str(j+1)]=0


for index,row in inclinations_eval.iterrows():
    # if row["building_id"] == "38747711":
    #     print(row["building_id"])
    s1=[]
    s2=[]
    s3=[]
    s4=[]

    for i in range(4):
        for j in range(4):

            if i == 0:
                s1.append(np.dot(row['t_gt'][i],row['t_pd'][j]))
            elif i == 1:
                s2.append(np.dot(row['t_gt'][i],row['t_pd'][j]))
            elif i == 2:
                s3.append(np.dot(row['t_gt'][i],row['t_pd'][j]))
            elif i == 3:
                s4.append(np.dot(row['t_gt'][i],row['t_pd'][j]))

    for k, l in enumerate([s1,s2,s3,s4]):
        k = k + 1
        #print(k)
        # get index of max value
        max_index = l.index(np.asarray(l).max()) + 1
        inclinations_eval.loc[index, f"err_{k}"] = abs(row[f"inclination{max_index}_pd"]-row[f"inclination{k}_gt"])

                # if np.dot(row['t_gt'][i],row['t_pd'][j]):
                #     max=np.dot(row['t_gt'][i],row['t_pd'][j])
            #     inclinations_eval.loc[index, "err"+str(i+1)+"_"+str(j+1)] = abs(row[f"inclination{j+1}_pd"]-row[f"inclination{i+1}_gt"])

mean1 = inclinations_eval["err_1"].mean()
mean2 = inclinations_eval["err_2"].mean()
mean3 = inclinations_eval["err_3"].mean()
mean4 = inclinations_eval["err_4"].mean()

print(f"Mean with all buildings: {(mean1+mean2+mean3+mean4)/4}")

# remove buildings in the list above
inclinations_eval = inclinations_eval[~inclinations_eval["building_id"].isin(buildings_to_exclude)]

mean1 = inclinations_eval["err_1"].mean()
mean2 = inclinations_eval["err_2"].mean()
mean3 = inclinations_eval["err_3"].mean()
mean4 = inclinations_eval["err_4"].mean()

print(f"Mean with removed buildings: {(mean1+mean2+mean3+mean4)/4}")

# def dot_product(row):
#     return np.dot(row['normal_array1_gt'], row['normal_array1_pd'])

# inclinations_eval["dot_product"]= inclinations_eval.apply(dot_product, axis=1)




# for index,row in inclinations_eval.iterrows():
#     if row["dot_product"]>0.8:
#         inclinations_eval["err1"]=abs(inclinations_eval["inclination1_gt"]-inclinations_eval["inclination1_pd"])

#     else:
#         inclinations_eval["err1"]=abs(inclinations_eval["inclination1_gt"]-inclinations_eval["inclination2_pd"])
#         inclinations_eval["err2"]=abs(inclinations_eval["inclination2_gt"]-inclinations_eval["inclination1_pd"])



# inclination_gt.rename(columns={"inclination": "inclination_gt"}, inplace=True)
# # import matplotlib.pyplot as plt
# # inclination_df["inclination"].hist(bins=20)
# # plt.show()
# df=pd.DataFrame()
# for filename in os.listdir(predictions_folder):

#     if filename.endswith('.json'):
#         df=angle_df(f"{predictions_folder}/{filename}",4)
#     #if j%5==0:
#      #   print(j,"buildings done")
#     inclination_pd=pd.concat([inclination_pd,df],axis=0)
# inclination_pd.rename(columns={"inclination": "inclination_pd"}, inplace=True)
# inclinations_eval = pd.merge(inclination_gt, inclination_pd, on=['building_id', 'pane'], how='inner').reset_index(drop=True)
# inclinations_eval["err"]=abs(inclinations_eval["inclination_gt"]-inclinations_eval["inclination_pd"])
# import matplotlib.pyplot as plt
# inclinations_eval["err"].hist(bins=20)
# plt.show()
# count = (inclinations_eval['err'] > 5).sum()
# print(count)
# %%

# %%

# %%

# %%

# %%

# %%

# %%

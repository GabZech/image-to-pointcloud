import numpy as np
import json
import os
#Exploring pointclouds through number of total points + visualization
#%%
# creation of point count dictionary
count={}
input_folder='data/run2/processed/pcs/saddle_roofs'
for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        #Create an array to read the json file into
        pointsList=[]
        # read the input JSON file
        with open(os.path.join(input_folder, filename), 'r') as f:

         for jsonObj in f:
          pt_coord=json.loads(jsonObj)
          pointsList.append(pt_coord['lidar'])
        name=os.path.splitext(filename)[0]
        #Store point data in x,y,z format
        points=np.asarray(pointsList, dtype=np.float32)
        points=points[0,:,:]
        #count=np.append(count,len(points))
        key = "roof" +"_"+ str(name)
        # Define the values for the item
        id = name
        pts= len(points)
        # Add the item to the dictionary with the two keys
        count[key] = {"id": id, "pts": pts}

#%%
#point count check
threshold = 600
i=0
for key, value in count.items():
   
    # Check if the value of the "price" key is lower than the threshold
    if value["pts"] < threshold:
        # If the value is lower, print the corresponding item information
        print(key, value)
        i=i+1
 
print(i)
#%%
#visualization
import open3d as o3d
import matplotlib.pyplot as plt

pointsList=[]
with open('data/run2/processed/pcs/clean_saddle_roofs/137232683.json') as f:
    for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])

# print(pointsList)
points=np.asarray(pointsList, dtype=np.float32)
points=points[0,:,:]
pcd = o3d.geometry.PointCloud()
pcd.points=o3d.utility.Vector3dVector(points)
o3d.visualization.draw(pcd)
# %%

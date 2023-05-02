#%%

input_dir = "data/all/processed/pcs/tent_roofs"
output_dir = "data/all/processed/pcs/tent_roofs_clean"


import os

import numpy as np
import laspy as laspy
import json
from sklearn.cluster import DBSCAN

from functions_download import create_dirs

# REMOVE OUTLIERS

create_dirs([output_dir])

for filename in os.listdir(input_dir):
    if filename.endswith('.json'):
        #Create an array to read the json file into
        pointsList=[]
        # read the input JSON file
        with open(os.path.join(input_dir, filename), 'r') as f:

            for jsonObj in f:
                pt_coord=json.loads(jsonObj)
                pointsList.append(pt_coord['lidar'])

        #Store point data in x,y,z format
        points=np.asarray(pointsList, dtype=np.float32)
        points=points[0,:,:]

         # initialize the DBSCAN algorithm - Parameters based on trial and error
        dbscan = DBSCAN(eps=75, min_samples=3)

         # perform clustering
        labels = dbscan.fit_predict(points)

         #Detect the largest cluster based on the point count
        unique_labels, counts = np.unique(labels, return_counts=True)
        largest_cluster_label = unique_labels[np.argmax(counts)]

        largest_cluster_mask = labels == largest_cluster_label

         # Get the points belonging to the largest cluster
        largest_cluster_points = points[largest_cluster_mask]

         #Write the jsonfile
        json_string={"building_id":os.path.splitext(filename)[0],
                     "lidar":largest_cluster_points.tolist()}
        with open(f"{output_dir}/{filename}", 'w+') as f:
            json.dump(json_string, f)

print("Finished removing outliers")

# CHECK NUMBER OF POINTCLOUDS WITH LESS THAN A CERTAIN NUMBER OF POINTS

threshold = 600 # number of points

# creation of point count dictionary
print("\nChecking pointclouds with less than {threshold} points")
count={}
for filename in os.listdir(input_dir):
    if filename.endswith('.json'):
        #Create an array to read the json file into
        pointsList=[]
        # read the input JSON file
        with open(os.path.join(input_dir, filename), 'r') as f:

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

#point count check
i=0
for key, value in count.items():

    # Check if the value of the "price" key is lower than the threshold
    if value["pts"] < threshold:
        # If the value is lower, print the corresponding item information
        print(key, value)
        i=i+1

print(i)

import numpy as np
import json
import open3d as o3d
from sklearn.cluster import DBSCAN
import os

# input and output folder paths
input_folder = 'data/run2/processed/pcs/saddle_roofs'
output_folder = 'data/run2/processed/pcs/clean_saddle_roofs'

#Read the files 

for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        #Create an array to read the json file into
        pointsList=[]
        # read the input JSON file
        with open(os.path.join(input_folder, filename), 'r') as f:

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
        with open(os.path.join(output_folder, filename), 'w') as f:
            json.dump(json_string, f)
# pdal_filter_pipeline
def pdal_filter_pipeline(filename):
    filter_pipeline = {
    "pipeline": 
    [
    {
                "type": "readers.las",
                "filename": filename
    },
    {
     "type":"filters.reprojection",
      "out_srs":"EPSG:32632"
     },
     {
       "type":"filters.assign",
       "assignment":"Classification[:]=0"
    },
    {
      "type":"filters.elm"
    },
    {
      "type":"filters.outlier"
    },
    {
      "type":"filters.smrf",
      #
      "ignore":"Classification[7:7]",
      "slope":0.7,
      "window":1,
      "threshold":5,
      "scalar":1.2
    },
    {
      "type":"filters.range",
      "limits":"Classification[2:2]"
    },
         {
          "type": "writers.las",
          #"compression": "true",
          "minor_version": "2",
          "dataformat_id": "0",
          "filename":"data/processed/clean_pcs/clean.las"
          }
      ]
     }
    return filter_pipeline 

import json
import pdal
import numpy as np
import open3d as o3d
import laspy

pipeline_str = pdal_filter_pipeline('data/processed/pcs/50520918.las')
json_str = json.dumps(pipeline_str)
pipeline = pdal.Pipeline(json_str)
pipeline.execute()


las_file = "clean.las"
folder_files = "data/processed/clean_pcs/"

las = laspy.read(f"{folder_files}{las_file}")
point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))



geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom],
                                 
                                  )

las_file = "50520918.las"
folder_files = "data/processed/pcs/"

las = laspy.read(f"{folder_files}{las_file}")
point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))



geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom],
                                 
                                  )
# pointsList=[]
# with open('data/processed/clean_pcs/clean.json') as f:
#     for jsonObj in f:
#         pt_coord=json.loads(jsonObj)
#         pointsList.append(pt_coord['lidar'])

# points=np.asarray(pointsList, dtype=np.float32)
# #print(points.shape)
# points=points[0,:,:]
# #print(points.shape)

# #pcd_data=points
# pcd = o3d.geometry.PointCloud()
# pcd.points=o3d.utility.Vector3dVector(points)


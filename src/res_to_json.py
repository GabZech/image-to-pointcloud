
#%%
import os

import torch
import json
import numpy as np

res = "datasets/2_surfaces/results/test.res"
test_dir = "datasets/2_surfaces/test/annotation"
output_dir = "datasets/2_surfaces/test_jsons"

# create output dir if it does not exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def reverse_lidar_normalization(lidar_gt, lidar_pred):
    lidar_gt = np.array(lidar_gt)
    if lidar_gt.shape[0] == 3:
        lidar_gt = np.transpose(lidar_gt)
    lidar_pred *= np.std(lidar_gt, 0, dtype='float64', keepdims=True)
    lidar_pred += np.mean(lidar_gt, 0, dtype='float64', keepdims=True)

    return lidar_pred

# load and process results
results = torch.load(res, map_location=torch.device('cpu'))

for res in results:

    building_id = list(res.keys())[0]
    lidar_pred = res[building_id]['final_out']

    # load ground truth pointcloud
    lidar_gt_path = f"{test_dir}/{building_id}.json"
    ann = json.load(open(lidar_gt_path))
    lidar_gt = ann["lidar"]

    # reverse normalization for the predicted pointcloud
    lidar_pred = reverse_lidar_normalization(lidar_gt, lidar_pred)

    json_string = {"building_id": str(building_id),
                    "lidar": lidar_pred.tolist()}

    save_path = f"{output_dir}/{building_id}.json"

    with open(save_path, 'w+') as outfile:
        json.dump(json_string, outfile)


# %%

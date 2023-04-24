import os
import pandas as pd
import json
import numpy as np

def calc_angles(directory, df):
    for building in os.listdir(directory):

        # read file
        f = open(f"{directory}/{building}")
        pc = json.load(f)
        pc = np.array(pc["lidar"])
        f.close()

        # CALCULATE ANGLES AND ETC
        # ADD FUNCTION HERE
        surface_ids = []
        surface_angles = []
        surface_vectors = []
        # e.g. for a saddle roof:
        # surface_ids = [1, 2]
        # surface_angles = [27.50, 28.40]

        building_id = building.split(".")[0]

        # add info to df
        for i in range(len(surface_ids)):
            surface_id = surface_ids[i]
            surface_angle = surface_angles[i]

            df_ = pd.DataFrame()
            df_["building_id"] = building_id
            df_["surface_id"] = surface_id
            df_["angle"] = surface_angle

            pd.concat([df, df_], axis=0)

    return df

# RUN
dir_gt = ""
dir_pred = ""

# ground truth
df_gt = pd.DataFrame()
df_gt = calc_angles(dir_gt, df_gt)
df_gt.rename(columns={"angle": "angle_gt"}, inplace=True)

# predictions
df_pred = pd.DataFrame()
df_pred = calc_angles(dir_pred, df_pred)
df_gt.rename(columns={"angle": "angle_pred"}, inplace=True)

# merge
df = pd.merge(df_gt, df_pred, on=["building_id", "surface_id"])
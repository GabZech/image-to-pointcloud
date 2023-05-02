#%% MOVE IMAGES TO FOLDERS
import os
import shutil
import numpy as np

input_dir = "datasets/2_surfaces"
dirs = ["train", "val", "test"]
subdirs = ["annotation", "image_filtered"]

output_dir = "datasets/2and4_balanced"

for dir in dirs:
    print(f"Processing {dir}...")
    files = []
    for file in os.listdir(f"{input_dir}/{dir}/image_filtered"):
        files.append(file[:-4])

    print(f"Found {len(files)} files")

    if dir == "train":
        # select files randomly
        files = np.random.choice(files, 178, replace=False)
    elif dir == "val":
        files = np.random.choice(files, 38, replace=False)
    elif dir == "test":
        files = np.random.choice(files, 39, replace=False)

    for subdir in subdirs:
        for file in files:
            if subdir == "annotation":
                try:
                    shutil.copy(f"{input_dir}/{dir}/{subdir}/{file}.json", f"{output_dir}/{dir}/{subdir}/{file}.json")
                except: continue

            elif subdir == "image_filtered":
                try:
                    shutil.copy(f"{input_dir}/{dir}/{subdir}/{file}.png", f"{output_dir}/{dir}/{subdir}/{file}.png")
                except: continue

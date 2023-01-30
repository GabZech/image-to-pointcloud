#%%
# GOBAL VARIABLES
number_of_imgs = 2 # number of 1kx1k image tiles to download. use "all" to download all available images
raw_images_folder = "data/raw/images/"
processed_images_folder = "data/processed/images/"
base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/"

# imports
import os
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import rasterio

#%%

### READ METADATA ###

metadata_filename = "dop_nw.csv"

# Download metadata if not already in data/raw/images
if metadata_filename not in raw_images_folder:
    print("File not found. Downloading...")
    url_metadata = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip"

    response = urllib.request.urlopen(url_metadata)
    zipfile = ZipFile(BytesIO(response.read()))

    metadata = pd.read_csv(zipfile.open(metadata_filename),
                        sep=';',
                        skiprows=5) # skip first 5 rows with irrelevant metadata

    metadata.to_csv(raw_images_folder + metadata_filename, index=False)

# import metadata
metadata = pd.read_csv(raw_images_folder + metadata_filename)
metadata

#%%

### READ, CONVERT AND SAVE IMAGES AS TIFF ###

# get list of filenames
if number_of_imgs == "all":
    imgs = list(metadata['Kachelname'].values)
else:
    imgs = list(metadata['Kachelname'].values[:number_of_imgs])

def read_convert_save_images(imgs, base_url, save_folder, rewrite=False):
    for img in imgs:
        img_url = f"{base_url}{img}.jp2"
        save_path = f"{save_folder}{img}.tiff"

        # read image
        if not os.path.exists(save_path) or rewrite:
            with rasterio.open(img_url, "r") as src:

                profile = src.profile
                profile.update(count=3, driver='GTiff')

                # keep only RGB channels
                img_rgb = src.read([1,2,3])

                # save image as tiff
                with rasterio.open(save_path, 'w', **profile) as dst:
                    dst.write(img_rgb)
                    print(f"Saved {save_path}")
        else:
            print(f"File {save_path} already exists.")

read_convert_save_images(imgs, base_url, raw_images_folder, rewrite=True)

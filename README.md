# Image to Pointcloud

## About

This repository contains scripts related to the collection and processing of image and pointcloud data from Geobasis NRW's open data portal. This data is used to fine-tune [Sat2PC](https://github.com/pittcps/sat2pc), a supervised, deep learning model that generates 3D pointclouds from 2D images of roofs developed by Yoones Rezaei & Stephen Lee. The generated pointclouds are then used to extract the angles of each roof surface for each individual roof.

The aim of this work is thus to train a deep learning model capable of generating 3D pointclouds of buildings’ roofs **based solely on images of their rooftops**. Such an approach allows for a more accurate estimation of the solar production potential of photovoltaic panels installed on top of buildings for areas in which no pointcloud data is available.

This work is part of the master thesis of [Nassim Zuoeini](https://github.com/nassimzoueini) and [Gabriel Zech](https://github.com/GabZech) for the Master of Data Science for Public Policy at the Hertie School of Governance in Berlin.


## Installation

1. Install Anaconda or Miniconda

2. Install environment using:

    `conda env create -f environment.yml`

    Or to replicate the exact same dependency versions used during development:

    `conda env create -f environment-versions.yml`

3. Activate environment

    `conda activate img2pc`


## Usage

All of the scripts are located in the `src` folder. We recommend opening and running the scripts in an IDE such as Visual Studio Code.

### Pre model training
1. [get_tiles.py](src/get_tiles.py) - Downloads the metadata for all available image and pointcloud tiles from Geobasis NRW's servers, matches both datasets and saves the metadata to a pre-defined csv file. In addition, it also plots the time differences between collection dates of image and pointcloud tiles for the same location.
2. [etl_img_data.py](src/etl_img_data.py) - Reads image tiles from Geobasis NRW's servers, extracts and selects buildings based on conditions and filters defined in the global variables section, enriches metadata with further information from additional APIs, extracts and processes the images for each individual building, and saves them to a desired folder.
3. [etl_pc_data.py](src/etl_pc_data.py) - Identifies buildings to download based on the image data, reads pointcloud tiles from Geobasis NRW's servers, extracts and processes the pointclouds for each individual building, and saves them to a desired folder.
4. [clean_pcs.py](src/clean_pcs.py) - Reads and cleans pointclouds based on a DBSCAN clustering algorithm and saves them to a desired folder.

### Post model training
5. [viz_losses.py](src/viz_losses.py) - Plots the losses for all model training and evaluation runs.
6. [res_to_json.py](src/res_to_json.py) - Reads the results of the model predictions and converts them to json files.
7. [pcs_to_planes.py](src/pcs_to_planes.py) - Performs iterative RANSAC and DBSCAN for plane detection and inclination calculation
8. [angle_evaluation.py](src/angle_evaluation.py) - Reads the results of the model predictions and calculates the angles of each roof surface for each individual roof.
9. [viz_pcs](src/viz_pcs.py) - Visualizes the pointcloud for a desired building.

#%%
import laspy

#%%
#Tranforming las file into array
las_file = "50520652.las" # noisy
folder_files = "data/processed/pcs/"

las = laspy.read(f"{folder_files}{las_file}")
las_content = las.arrays
xs_clip = las_content[0]['X']
ys_clip = las_content[0]['Y']
zs_clip = las_content[0]['Z']
num_orig_pts=len(xs_clip)
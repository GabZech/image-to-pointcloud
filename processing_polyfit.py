#%%
import numpy as np
import json
import matplotlib.pyplot as plt
import pandas as pd
import pdal
import fileinput
import sys, subprocess
#Reading and transforming json file into array
pointsList=[]
with open('data/processed/pcs/50526389.json') as f:
    for jsonObj in f:
        pt_coord=json.loads(jsonObj)
        pointsList.append(pt_coord['lidar'])


points=np.asarray(pointsList, dtype=np.float32)
points=points[0,:,:]
#storing points
xs=[]
ys=[]
zs=[]
for j in range (len(points)):
    for i in range(3):
        if i%3==0:
            xs.append(points[j,i])
        if i%3==1:
            ys.append(points[j,i])
        if i%3==2:
            zs.append(points[j,i])

# xs_clip = points['X']
# ys_clip = points['Y']
# zs_clip = points['Z']
# num_orig_pts=len(xs_clip)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(xs, ys, zs, s=4,
           c=zs, cmap='turbo', alpha=1.0)
ax.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))

plt.show()

# %%
# Ready for Polyfit
## preprocess data for input into polyfit:

df = pd.DataFrame({'X': xs, 'Y': ys, 'Z': zs}, dtype=float)
df = df[df.Z > -9999]  # remove no data from roof densification raster

## we subtract constant on Y values, as they get truncated in OFF and PLY format when outputting through CGAL
#y_offset = 5700000
df.Y = df.Y #-y_offset

## write to structured array for further processing in PDAL:
struct_arr = [df.to_records(index=False)]

## caclulate unoriented normals, a requirement for RANSAC plane fitting, write to PLY file:
pipeline_calc_normals_write_array_ply = """{
  "pipeline": [    
    {
        "type":"filters.normal",
        "knn":8,
        "refine":true
    },
    {
        "type":"writers.ply",
        "sized_types":false,
        "precision":2,
        "faces":true,
        "filename":"PLYFILE"
    }
  ]
}"""
plydir="data/processed/plyfiles"
curr_plyfile = plydir+'/%s_mod.ply'
write_pipeline = pdal.Pipeline(pipeline_calc_normals_write_array_ply.replace(
    'PLYFILE', curr_plyfile), struct_arr)
write_pipeline.execute()

## important. the polyfit exe only detects planes if normal vectors are called nx,ny,nz and NOT normalx,normaly,normalz!
# for now we do this modification in the PLY ascii file:
for line in fileinput.input(curr_plyfile, inplace=1):
    print(line.replace('normalx', 'nx').replace('normaly', 'ny').replace('normalz', 'nz').rstrip())
fileinput.close()

print('created %s' %curr_plyfile)


# %%
## run polyfit, which will create a watertight 3d object from our pointcloud:
polyfit_exe = '/Users/nassimzoueini/Downloads/PolyFit'
polyoutdir='/Users/nassimzoueini/Documents/PolyfitDirectory'
## RANSAC parameters:
probability = 0.8
min_points = 10#40
epsilon = 0.25
cluster_epsilon = 6.25
normal_threshold = 0.01

polyfit_out_surfaces = polyoutdir+'/%s_fitted.off' 
polyfit_out_meshes = plydir+'/%s_meshes.ply'
polyfit_call = polyfit_exe+' %s %s %s %s %s %s %s %s' % (curr_plyfile,
                                                         polyfit_out_surfaces,
                                                         polyfit_out_meshes,
                                                         probability, min_points, epsilon,
                                                         cluster_epsilon, normal_threshold)
print(polyfit_call)

try:
    response = subprocess.check_output(polyfit_call, shell=True)
    print('success')
except:
    sys.exit(0)
    #failed.append(row.gmlid)
    
print('polyfit output written to file: %s' %polyfit_out_surfaces)

# visualize the polyfit output: throws error due to OpenGL issue!
#pcd = o3d.io.read_triangle_mesh(polyfit_out_surfaces)
#vis = o3d.visualization.Visualizer()
#vis.create_window()
#vis.add_geometry(pcd)
#vis.update_renderer()
# %%

import pandas as pd

# read json file to dataframe
image_df = pd.read_json("figures/images_dataset.json")
image_df = pd.json_normalize(image_df['files'])
image_df['size'] = image_df['size'].astype('int64') / 1e6
images_size = image_df['size'].sum()

pcs_df = pd.read_json("figures/pcs_dataset.json")
pcs_df = pd.json_normalize(pcs_df['files'])
pcs_df['size'] = pcs_df['size'].astype('int64') / 1e6
pcs_size = pcs_df['size'].sum()


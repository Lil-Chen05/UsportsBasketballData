import os
import pandas as pd

input_dir = "/Users/jerryc/Desktop/Basketball copy/UsportsBasketballData/Basketball/PlayerDataProcessed"
output_dir = "BaseData"
output_file = os.path.join(output_dir, "playerGameDataAll.csv")

# Create output dir if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# List all CSVs in input_dir (excluding the output file if it's in the same folder)
csv_files = [
    os.path.join(input_dir, f)
    for f in os.listdir(input_dir)
    if f.endswith(".csv") and "playerGameDataAll.csv" not in f
]

# Combine all CSVs
df_list = [pd.read_csv(file) for file in csv_files]
combined_df = pd.concat(df_list, ignore_index=True)

# Write to output
combined_df.to_csv(output_file, index=False)
print(f"Saved combined data to {output_file}")

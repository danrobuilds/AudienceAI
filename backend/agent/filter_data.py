# This script is used to filter the data to only include posts with 300+ reactions and <50k followers

import pandas as pd
import os

# Read the original CSV from parent directory
csv_path = "../influencers_data.csv"
print(f"Loading {csv_path}...")
df = pd.read_csv(csv_path, low_memory=False)

print(f"Original dataset: {len(df)} rows")

# Filter for posts with 300+ reactions
# Handle NaN values by filling with 0 first
df['reactions'] = df['reactions'].fillna(0)

# Convert to numeric in case there are any string values
df['reactions'] = pd.to_numeric(df['reactions'], errors='coerce').fillna(0)

# Handle followers column - convert to numeric
df['followers'] = df['followers'].fillna(0)
df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)

# Apply both filters: 300+ reactions AND <50k followers
filtered_df = df[(df['reactions'] >= 300) & (df['followers'] < 50000)]

print(f"Posts with 300+ reactions AND <50k followers: {len(filtered_df)} rows")
print(f"Removed: {len(df) - len(filtered_df)} rows")

if len(filtered_df) > 0:
    # Save the filtered dataset to parent directory
    output_path = "../influencers_data_filtered.csv"
    filtered_df.to_csv(output_path, index=False)
    print(f"Filtered dataset saved as '{output_path}'")
    
    # Show some stats
    print(f"\nReaction stats for filtered data:")
    print(f"Min reactions: {filtered_df['reactions'].min()}")
    print(f"Max reactions: {filtered_df['reactions'].max()}")
    print(f"Average reactions: {filtered_df['reactions'].mean():.1f}")
    
    print(f"\nFollower stats for filtered data:")
    print(f"Min followers: {filtered_df['followers'].min()}")
    print(f"Max followers: {filtered_df['followers'].max()}")
    print(f"Average followers: {filtered_df['followers'].mean():.1f}")
else:
    print("No posts found with 300+ reactions and <50k followers!")
    print(f"Max reactions in dataset: {df['reactions'].max()}")
    print(f"Min followers in dataset: {df['followers'].min()}")
    print(f"Max followers in dataset: {df['followers'].max()}") 
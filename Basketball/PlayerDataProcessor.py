import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

def process_basketball_data(csv_file_path):
    """
    Process basketball CSV data by:
    1. Converting Date column to datetime
    2. Splitting X-Y columns into separate Made and Attempted columns
    3. Converting numeric columns to appropriate types
    4. Adding calculated columns like shooting percentages
    """
    
    # Load the data
    print(f"Loading data from: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    print(f"Original shape: {df.shape}")
    
    # 1. Convert Date column to datetime
    print("\n1. Converting Date column to datetime...")
    df['Date'] = pd.to_datetime(df['Date'], format='%a %b %d, %Y')
    print(f"Date column converted. Sample: {df['Date'].iloc[0]}")
    
    # 2. Split X-Y columns into separate Made and Attempted columns
    print("\n2. Splitting X-Y columns...")
    
    # Define columns to split
    columns_to_split = {
        'ThreePt_Made_Att': ['3PTM', '3PTA'],
        'FG_Made_Att': ['FGM', 'FGA'], 
        'FT_Made_Att': ['FTM', 'FTA']
    }
    
    for col, new_cols in columns_to_split.items():
        if col in df.columns:
            print(f"  Splitting {col} into {new_cols[0]} and {new_cols[1]}")
            
            # Split the X-Y format
            split_data = df[col].str.split('-', expand=True)
            
            # Convert to numeric, handling any non-numeric values
            df[new_cols[0]] = pd.to_numeric(split_data[0], errors='coerce').fillna(0).astype(int)
            df[new_cols[1]] = pd.to_numeric(split_data[1], errors='coerce').fillna(0).astype(int)
            
            # Drop the original column
            df = df.drop(columns=[col])
    
    # 3. Convert percentage columns to numeric (remove % sign)
    print("\n3. Converting percentage columns...")
    percentage_cols = ['ThreePtPct', 'FGPct', 'FTPct']
    for col in percentage_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            print(f"  Converted {col}")
    
    # 4. Convert other numeric columns
    print("\n4. Converting other numeric columns...")
    numeric_cols = ['Jersey', 'Mins', 'Reb_Off', 'Reb_Def', 'Reb_Tot', 
                   'PF', 'AST', 'TO', 'BLK', 'STL', 'Pts']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convert StarterFlag to boolean
    if 'StarterFlag' in df.columns:
        df['StarterFlag'] = df['StarterFlag'].astype(bool)
        print("  Converted StarterFlag to boolean")
    
    # 5. Calculate additional useful columns
    print("\n5. Adding calculated columns...")
    
    # True shooting percentage: TS% = PTS / (2 * (FGA + 0.44 * FTA))
    df['TS_Pct'] = np.where(
        (df['FGA'] + 0.44 * df['FTA']) > 0,
        df['Pts'] / (2 * (df['FGA'] + 0.44 * df['FTA'])) * 100,
        0
    )
    df['TS_Pct'] = df['TS_Pct'].round(2)
    
    # Effective field goal percentage: eFG% = (FGM + 0.5 * 3PTM) / FGA
    df['eFG_Pct'] = np.where(
        df['FGA'] > 0,
        (df['FGM'] + 0.5 * df['3PTM']) / df['FGA'] * 100,
        0
    )
    df['eFG_Pct'] = df['eFG_Pct'].round(2)

    # Minutes played as float
    df['Mins'] = pd.to_numeric(df['Mins'], errors='coerce').fillna(0)
    
    print(f"\nFinal shape: {df.shape}")
    print(f"Added columns: TS_Pct, eFG_Pct")

    # 6. Add Team Abbrevitions
     # Read team data
    team_data = pd.read_csv('TeamData.csv')
    # Create a dictionary of team names to abbreviations
    team_abbr_dict = dict(zip(team_data['team'], team_data['abbr']))

     # Add abbreviation column
    df['Abbr'] = df['Team'].map(team_abbr_dict)
    
    # Reorder columns to put Abbr before Jersey
    cols = list(df.columns)
    jersey_idx = cols.index('Jersey')
    cols.remove('Abbr')
    cols.insert(jersey_idx, 'Abbr')
    df = df[cols]

    # 7. Remove Exhibition Games
    valid_teams = set(team_data['team'])
    df = df[
        df['Team'].isin(valid_teams) & 
        df['Opponent'].isin(valid_teams)
        ]


    # 8. Rename columns to preferred format
    print("\n6. Renaming columns...")
    column_mapping = {
        'ThreePtPct': '3PT_Pct',
        'FGPct': 'FG_Pct',
        'FTPct': 'FT_Pct',
        'Reb_Off': 'Reb_O',
        'Reb_Def': 'Reb_D',
        'Reb_Tot': 'Reb_T'
    }
    
    df = df.rename(columns=column_mapping)
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            print(f"  Renamed {old_name} to {new_name}")
    
    return df

def save_processed_data(df, original_file_path):
    """Save the processed data with a new filename"""
    # Create PlayerData directory if it doesn't exist
    player_data_dir = "PlayerDataProcessed"
    os.makedirs(player_data_dir, exist_ok=True)

    # Create new filename
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]
    new_file_path = os.path.join(player_data_dir, f"{base_name}_processed.csv")
    
    # Save processed data
    df.to_csv(new_file_path, index=False)
    print(f"\nProcessed data saved to: {new_file_path}")
    
    return new_file_path

def display_data_info(df):
    """Display information about the processed data"""
    
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Number of unique players: {df['PlayerName'].nunique()}")
    print(f"Number of unique teams: {df['Team'].nunique()}")
    
    print("\nColumn types:")
    print(df.dtypes)
    
    print(f"\nSample of processed data:")
    print(df.head(3).to_string())
    
    print(f"\nBasic statistics:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    print(df[numeric_cols].describe())

def process_all_csv_files(directory_path="PlayerData"):
    """Process all CSV files in the PlayerData directory"""
    
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist!")
        return
    
    csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv') and not f.endswith('_processed.csv')]
    
    if not csv_files:
        print(f"No CSV files found in {directory_path}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    processed_files = []
    
    for csv_file in csv_files:
        file_path = os.path.join(directory_path, csv_file)
        print(f"\n{'='*80}")
        print(f"PROCESSING: {csv_file}")
        print(f"{'='*80}")
        
        try:
            # Process the data
            df_processed = process_basketball_data(file_path)
            
            # Save processed data
            new_file_path = save_processed_data(df_processed, file_path)
            processed_files.append(new_file_path)
            
            # Display info
            display_data_info(df_processed)
            
        except Exception as e:
            print(f"ERROR processing {csv_file}: {str(e)}")
    
    print(f"\n{'='*80}")
    print("PROCESSING COMPLETE!")
    print(f"{'='*80}")
    print("Processed files created:")
    for file in processed_files:
        print(f"  ✓ {file}")

if __name__ == "__main__":
    # Process all CSV files in PlayerData directory
    process_all_csv_files()
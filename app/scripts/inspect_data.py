# Import libraries needed for reading the CSV file and handling file paths
import pandas as pd
from pathlib import Path

# Set the file path for the raw FEMA disaster data
csv_path = "data/raw/DisasterDeclarationsSummaries.csv"

# Read the FEMA CSV file into a pandas DataFrame
df = pd.read_csv(csv_path)

# Display the number of rows and columns in the dataset
print("Rows and columns:", df.shape)

# Display all column names from the FEMA dataset
print("\nColumn names:")
print(df.columns.tolist())

# Display the first 5 rows of the dataset
print("\nFirst 5 rows:")
print(df.head())

# Display the number of missing values in each column
print("\nMissing values:")
print(df.isnull().sum())

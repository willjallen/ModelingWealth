import pandas as pd
import numpy as np
import re

import copy



# https://www.federalreserve.gov/releases/z1/dataviz/dfa/distribute/chart/#range:1989.3,2023.2;quarter:135;series:Net%20worth;demographic:networth;population:all;units:levels
class FedData():
	'''
	Category       Bottom50          Next40           Next9   RemainingTop1          TopPt1\n
	Date\n
	1989Q3     777847000000   7408899000000   7635884000000   2838759000000   1762391000000\n       
	1989Q4     773147000000   7543056000000   7770202000000   2905496000000   1812715000000\n       
	1990Q1     802257000000   7632482000000   7768099000000   2897829000000   1805996000000\n       
	1990Q2     795586000000   7725807000000   7852815000000   2940394000000   1850643000000\n       
	1990Q3     816101000000   7768646000000   7767485000000   2864036000000   1802020000000\n       
	...                 ...             ...             ...             ...             ...\n       
	2022Q2    3693290000000  40597799000000  52360285000000  25245660000000  17152653000000\n       
	2022Q3    3465458000000  39752441000000  51432675000000  24701285000000  16895448000000\n       
	2022Q4    3312041000000  39762499000000  52023687000000  25240065000000  17304315000000\n       
	2023Q1    3357428000000  40226341000000  53029835000000  26054016000000  17918414000000\n       
	2023Q2    3638332000000  41741148000000  54808044000000  27145640000000  18625162000000\n       

	[136 rows x 5 columns] 
	'''  
   # Define population sizes for each category
	POPULATION_SIZES = {
		'TopPt1': 0.001,
		'RemainingTop1': 0.009,
		'Next9': 0.09,
		'Next40': 0.4,
		'Bottom50': 0.5
	}

	# Define the population percentiles for each category
	PERCENTILES = {
		'TopPt1': (99.99, 100),
		'RemainingTop1': (99, 99.99),
		'Next9': (90, 99),
		'Next40': (50, 90),
		'Bottom50': (0, 50)
	}

	PERCENTILES_STR = {
		'TopPt1': '99.99-100',
		'RemainingTop1': '99-99.99',
		'Next9': '90-99',
		'Next40': '50-90',
		'Bottom50': '0-50'
	}

	PERCENTILES_STR_LIST = ['99.99-100', '99-99.99', '90-99', '50-90', '0-50'] 
 
	def __init__(self):
		self.loaded = False
	
	def load(self):
		print("Loading FED net worth data...")
		self.df = pd.read_csv("data/FED/dfa-networth-levels.csv")
		# Adjust the date format and convert to datetime
		self.df['Date'] = self.df['Date'].str.replace(':', '-').astype('period[Q]')

		# Pivot the dataframe
		self.df_net_worth = self.df.pivot(index='Date', columns='Category', values='Net worth')
		self.df_net_worth *= 1_000_000 

		self.loaded = True
		print("FED net worth data loaded")
	
	def get_net_worth_data(self):
		if not self.loaded:
			print("Load the data first with .load()")
			return 
		return self.df_net_worth.copy()


class PSIDData():
	def __init__(self):
		self.loaded = False
  
	def load(self):
		print("Loading PSID household wealth data...")

		# Load the data labels
		with open("data/PSID/data_labels.txt", 'r') as file:
			contents = file.readlines()	
   
		# Convert the data labels to a dictionary
		self.variables_dict = self.parse_to_dict(contents)
  
		# Extract the years from the data labels
		self.year_dict = {var: self.extract_year(var, label) for var, label in self.variables_dict.items() if self.extract_year(var, label)}
 
		# Load the main data
		self.household_wealth_data_df = pd.read_csv("data/PSID/household-wealth-data.csv")

		# Initialize an empty dictionary to hold the dataframes for each year
		self.household_wealth_year_dfs = {}

		# Iterate over each year and create a dataframe
		for year in set(self.year_dict.values()):
			# Find all columns for this year
			columns_for_year = [var for var, yr in self.year_dict.items() if yr == year]

			# Identify the index column and the wealth columns
			index_column = next((col for col in columns_for_year if 'INTERVIEW' in self.variables_dict[col]), None)
			imp_wealth_column = next((col for col in columns_for_year if 'IMP WEALTH' in self.variables_dict[col]), None)
			acc_wealth_column = next((col for col in columns_for_year if 'ACC WEALTH' in self.variables_dict[col]), None)

			# Create a dataframe with the relevant columns
			if index_column and imp_wealth_column and acc_wealth_column:
				year_df = self.household_wealth_data_df[[index_column, imp_wealth_column, acc_wealth_column]].copy()
				year_df.set_index(index_column, inplace=True)
				year_df.index.name = 'FAMILY ID'
				year_df.columns = ['IMP WEALTH W/ EQUITY', 'ACC WEALTH W/ EQUITY']
    
				# Remove empty rows (NaN)
				year_df = year_df.dropna(axis=0, how='any')	
    
				# TODO: Adjust for inflation
    
				self.household_wealth_year_dfs[year] = year_df

		self.loaded = True
		print("PSID household wealth data loaded")
  
	def get_household_wealth_data(self):
		return copy.deepcopy(self.household_wealth_year_dfs)

		# sample_year = next(iter(self.household_wealth_year_dfs))  # Get a sample year
		# print(self.household_wealth_year_dfs[sample_year].head())  # Display the dataframe for this year 
		
  
	# Function to parse the labels and convert it to a dictionary
	def parse_to_dict(self, lines):
		variable_dict = {}
		for line in lines:
			# Skip lines that don't contain variable information
			if not line.strip() or "Variable" in line or "****" in line:
				continue
			# Split the line into variable and label
			parts = line.split(maxsplit=1)
			if len(parts) == 2:
				var, label = parts
				variable_dict[var.strip()] = label.strip()
		return variable_dict

	# Function to extract year from the label
	def extract_year(self, var, label):
		# Try to find a 4-digit year in the label 
		label_year_match = re.search(r'\b(19|20)\d{2}\b', label)
		if label_year_match:
			return label_year_match.group()
		# Return None if no year found
		return None


fed_data = FedData()
fed_data.load()
print(fed_data.get_net_worth_data())

psid_data = PSIDData()
psid_data.load()
print(psid_data.get_household_wealth_data())
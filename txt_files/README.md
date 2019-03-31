# File Caching

Files in here are cached and used incase of Python crashing mid web scrap.

They feed into each other like follows:

all_makes_file => all_models_file

all_models_file => all_years_file

all_years_file => all_specs_file

all_specs_file => all_trims_file

all_trims_file => all_data_file

all_data_file => final_data

final_data => csv_files/the_big_data.csv (The final result of running scraping.py)
import pandas as pd


def get_average_difference_in_seasons(year):
    file_path = '../data/ProvincialProduction.csv'
    solar_data_cleaned = pd.read_csv(file_path, skiprows=13)

    solar_data_cleaned['Local'] = pd.to_datetime(solar_data_cleaned['Local'])

    summer_months = [6, 7, 8]
    winter_months = [12, 1, 2]

    solar_data_year = solar_data_cleaned[solar_data_cleaned['Local'].dt.year == year]

    summer_data_year = solar_data_year[solar_data_year['Local'].dt.month.isin(summer_months)]
    winter_data_year = solar_data_year[solar_data_year['Local'].dt.month.isin(winter_months)]

    summer_data_filtered_year = summer_data_year[summer_data_year['Groningen'] > 0]
    winter_data_filtered_year = winter_data_year[winter_data_year['Groningen'] > 0]

    if not summer_data_filtered_year.empty and not winter_data_filtered_year.empty:
        summer_avg_production_filtered_year = summer_data_filtered_year['Groningen'].mean()
        winter_avg_production_filtered_year = winter_data_filtered_year['Groningen'].mean()

        # Calculate the percentage difference
        percentage_difference_filtered_year = ((summer_avg_production_filtered_year - winter_avg_production_filtered_year) / winter_avg_production_filtered_year) * 100
        return summer_avg_production_filtered_year, winter_avg_production_filtered_year, percentage_difference_filtered_year
    else:
        return None, None, None
    
    
if __name__ == '__main__':
    get_average_difference_in_seasons(2022)
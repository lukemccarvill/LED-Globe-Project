import pandas as pd
import matplotlib.pyplot as plt
from config import not_countries, countries_by_continent
import os

# Color palette for continents
continent_colors = {
    'Africa': '#E74C3C',      # Red
    'Asia': '#F39C12',        # Orange
    'Europe': '#3498DB',      # Blue
    'North America': '#2ECC71',  # Green
    'South America': '#9B59B6',  # Purple
    'Oceania': '#1ABC9C',     # Teal
    'Antarctica': '#95A5A6'   # Gray
}

# Create reverse mapping: country -> continent
country_to_continent = {}
for continent, countries in countries_by_continent.items():
    for country in countries:
        country_to_continent[country] = continent

# Function to get color for a country
def get_country_color(country):
    continent = country_to_continent.get(country, 'Other')
    return continent_colors.get(continent, '#34495E')  # Default dark gray

#Index(['Entity', 'Code', 'Year', 'primary_energy_consumption__twh'], dtype='object')
energy_cons = pd.read_csv('../data/API/global_energy_consumption.csv')
energy_cons = energy_cons[~energy_cons['Entity'].isin(not_countries)]

# Create the figures directory if it doesn't exist
os.makedirs('../images/figures', exist_ok=True)
print("Directory '../images/figures' created or already exists")

## ------------------------------------------ FIGURE 1: BAR CHART (TOP 30 COUNTRIES, MOST RECENT YEAR) ------------------------------------------

# Get the most recent year
max_year = energy_cons['Year'].max()
energy_cons_recent = energy_cons[energy_cons['Year'] == max_year]

# Get top 30 entities by primary energy consumption
top_30 = energy_cons_recent.nlargest(30, 'primary_energy_consumption__twh')

# Create colors for each bar based on continent
bar_colors = [get_country_color(entity) for entity in top_30['Entity']]

# Create the bar chart
plt.figure(figsize=(16, 6))
plt.bar(range(len(top_30)), top_30['primary_energy_consumption__twh'],
        color=bar_colors, edgecolor='black', linewidth=0.5)

plt.title(f'Primary Energy Consumption (Top 30 Countries, {max_year})',
          fontsize=16, fontweight='bold', pad=20)
plt.ylabel('Energy Consumption (TWh)', fontsize=12)
plt.xticks(range(len(top_30)), top_30['Entity'], rotation=45, ha='right', fontsize=10)
plt.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)

# Add legend for continents
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color, edgecolor='black', label=continent)
                   for continent, color in continent_colors.items()]
plt.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.tight_layout()

# Save figure 1
plt.savefig('../images/figures/energy_consumption_top30.png', dpi=300, bbox_inches='tight')
plt.show()

## ------------------------------------------ FIGURE 2: LINE CHART (ALL COUNTRIES OVER TIME) ------------------------------------------

# Create line chart for each entity
plt.figure(figsize=(16, 10))

# Plot a line for each entity with continent-based colors
for entity in energy_cons['Entity'].unique():
    entity_data = energy_cons[energy_cons['Entity'] == entity].sort_values('Year')
    color = get_country_color(entity)
    plt.plot(entity_data['Year'], entity_data['primary_energy_consumption__twh'],
             color=color, linewidth=1.5, alpha=0.7)

plt.title('Primary Energy Consumption Over Time by Country',
          fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Energy Consumption (TWh)', fontsize=12)
plt.grid(False)

# Add legend for continents (not individual countries)
legend_elements = [Patch(facecolor=color, edgecolor='black', label=continent)
                   for continent, color in continent_colors.items()]
plt.legend(handles=legend_elements, loc='upper left', fontsize=10)

plt.tight_layout()

# Save figure 2
plt.savefig('../images/figures/energy_consumption_timeline.png', dpi=300, bbox_inches='tight')
plt.show()
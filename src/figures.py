import pandas as pd
import matplotlib.pyplot as plt
from config import not_countries, countries_by_continent
import os
from matplotlib.patches import Patch
import numpy as np

# ============================================================
# CONFIGURATION: Energy Unit and Aggregation Settings
# ============================================================
# Options: 'TWh' (terawatt-hours) or 'PWh' (petawatt-hours)
ENERGY_UNIT = 'PWh'

# Figure 1 & 3: Aggregation method for remaining countries
# Options: 'continent_median', 'continent_sum', 'all_median', 'all_sum'
AGGREGATION_METHOD_FIG1 = 'continent_median'
AGGREGATION_METHOD_FIG3 = 'continent_median'

# Figure 2 & 4: Number of top countries to plot individually
TOP_N_COUNTRIES_FIG2 = 6
TOP_N_COUNTRIES_FIG4 = 6

# Figure 2 & 4: Aggregation method for remaining countries
# Options: 'continent_median', 'continent_sum', 'all_median', 'all_sum'
AGGREGATION_METHOD_FIG2 = 'continent_median'
AGGREGATION_METHOD_FIG4 = 'continent_median'

# Figure 2 & 4: Y-axis scale
# Options: 'linear' or 'log'
Y_AXIS_SCALE_FIG2 = 'linear'
Y_AXIS_SCALE_FIG4 = 'linear'
# ============================================================

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

# Load data
energy_cons_country = pd.read_csv('../data/API/global_energy_consumption.csv')
energy_cons_country = energy_cons_country[~energy_cons_country['Entity'].isin(not_countries)]

energy_cons_percap = pd.read_csv('../data/API/per_capita_energy_consumption.csv')
energy_cons_percap = energy_cons_percap[~energy_cons_percap['Entity'].isin(not_countries)]

# Add continent column to both dataframes
energy_cons_country['Continent'] = energy_cons_country['Entity'].map(country_to_continent)
energy_cons_percap['Continent'] = energy_cons_percap['Entity'].map(country_to_continent)

# Convert energy units based on setting for country data
if ENERGY_UNIT == 'PWh':
    energy_cons_country['energy_consumption'] = energy_cons_country['primary_energy_consumption__twh'] / 1000
    unit_label = 'PWh'
else:  # Default to TWh
    energy_cons_country['energy_consumption'] = energy_cons_country['primary_energy_consumption__twh']
    unit_label = 'TWh'

# For per capita data, use the column as-is (already in kWh per person)
energy_cons_percap['energy_consumption_per_capita'] = energy_cons_percap['primary_energy_consumption_per_capita__kwh']
percap_unit_label = 'kWh/person'

# Create the figures directory if it doesn't exist
os.makedirs('../images/figures', exist_ok=True)
print("Directory '../images/figures' created or already exists")
print(f"Using energy unit: {unit_label}")
print(f"Per capita unit: {percap_unit_label}")
print(f"Figure 1 - Aggregation method: {AGGREGATION_METHOD_FIG1}")
print(f"Figure 2 - Top {TOP_N_COUNTRIES_FIG2} countries, Aggregation: {AGGREGATION_METHOD_FIG2}, Scale: {Y_AXIS_SCALE_FIG2}")
print(f"Figure 3 - Aggregation method: {AGGREGATION_METHOD_FIG3}")
print(f"Figure 4 - Top {TOP_N_COUNTRIES_FIG4} countries, Aggregation: {AGGREGATION_METHOD_FIG4}, Scale: {Y_AXIS_SCALE_FIG4}")

## ------------------------------------------ FIGURE 1: BAR CHART (TOTAL CONSUMPTION) ------------------------------------------

# Get the most recent year
max_year = energy_cons_country['Year'].max()
energy_cons_country_recent = energy_cons_country[energy_cons_country['Year'] == max_year]

# Calculate global total for percentage calculation
global_total = energy_cons_country_recent['energy_consumption'].sum()

# Get top 10 entities by primary energy consumption
top_10 = energy_cons_country_recent.nlargest(10, 'energy_consumption')
top_10_entities = top_10['Entity'].tolist()

# Get all remaining countries (not in top 10)
remaining_countries_fig1 = energy_cons_country_recent[~energy_cons_country_recent['Entity'].isin(top_10_entities)]

# Create list to store aggregated data
aggregated_data_list = []

if AGGREGATION_METHOD_FIG1.startswith('continent_'):
    # Group by continent
    agg_method = 'sum' if AGGREGATION_METHOD_FIG1 == 'continent_sum' else 'median'
    agg_label = agg_method.capitalize()

    for continent in sorted(continent_colors.keys()):
        continent_data = remaining_countries_fig1[remaining_countries_fig1['Continent'] == continent]

        if len(continent_data) == 0:
            continue

        if agg_method == 'sum':
            aggregated_value = continent_data['energy_consumption'].sum()
        else:
            aggregated_value = continent_data['energy_consumption'].median()

        label_text = f'Other {continent} ({agg_label})'
        aggregated_data_list.append(
            {'Entity': label_text, 'energy_consumption': aggregated_value, 'Continent': continent})

else:  # all_median or all_sum
    agg_method = 'sum' if AGGREGATION_METHOD_FIG1 == 'all_sum' else 'median'
    agg_label = agg_method.capitalize()

    if agg_method == 'sum':
        aggregated_value = remaining_countries_fig1['energy_consumption'].sum()
    else:
        aggregated_value = remaining_countries_fig1['energy_consumption'].median()

    label_text = f'All Others ({agg_label})'
    aggregated_data_list.append({'Entity': label_text, 'energy_consumption': aggregated_value, 'Continent': None})

# Create dataframe with top 10 + aggregated data
plot_data = pd.concat([
    top_10[['Entity', 'energy_consumption']],
    pd.DataFrame(aggregated_data_list)
], ignore_index=True)

# Create colors for each bar
bar_colors = []
for idx, row in plot_data.iterrows():
    entity = row['Entity']
    if entity.startswith('Other') or entity.startswith('All'):
        if row.get('Continent'):
            bar_colors.append(continent_colors.get(row['Continent'], '#95A5A6'))
        else:
            bar_colors.append('#95A5A6')
    else:
        bar_colors.append(get_country_color(entity))

# Create the bar chart
fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.bar(range(len(plot_data)), plot_data['energy_consumption'],
              color=bar_colors, edgecolor='black', linewidth=0.5)

# Add hatch pattern to aggregated bars
for idx, entity in enumerate(plot_data['Entity']):
    if entity.startswith('Other') or entity.startswith('All'):
        bars[idx].set_hatch('//')

# Add percentage labels above each bar
for idx, (bar, value) in enumerate(zip(bars, plot_data['energy_consumption'])):
    percentage = (value / global_total) * 100
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height,
            f'{percentage:.1f}%',
            ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_ylabel(f'Energy Consumption ({unit_label})', fontsize=12)
ax.set_xticks(range(len(plot_data)))
ax.set_xticklabels(plot_data['Entity'], rotation=45, ha='right', fontsize=10)
ax.set_xlim(-0.5, len(plot_data) - 0.5)
ax.set_ylim(0, None)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.grid(False)

# Add legend only for continents that appear in the chart
continents_in_chart = set()
for idx, row in plot_data.iterrows():
    entity = row['Entity']
    if entity.startswith('Other') and row.get('Continent'):
        continents_in_chart.add(row['Continent'])
    elif not (entity.startswith('Other') or entity.startswith('All')):
        continent = country_to_continent.get(entity)
        if continent:
            continents_in_chart.add(continent)

legend_elements = [Patch(facecolor=continent_colors[continent], edgecolor='black', label=continent)
                   for continent in sorted(continents_in_chart)]

if AGGREGATION_METHOD_FIG1.startswith('all_'):
    legend_elements.append(Patch(facecolor='#95A5A6', edgecolor='black', hatch='//', label='All Others'))

ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.tight_layout()

# Save figure 1
plt.savefig('../images/figures/energy_consumption_total_bar.png', dpi=300, bbox_inches='tight')
plt.show()

## ------------------------------------------ FIGURE 2: LINE CHART (TOTAL CONSUMPTION) ------------------------------------------

# Get top N countries by most recent year consumption
top_n_entities = energy_cons_country_recent.nlargest(TOP_N_COUNTRIES_FIG2, 'energy_consumption')['Entity'].tolist()

# Create line chart with increased height
fig, ax = plt.subplots(figsize=(16, 14))

# Plot top N countries individually with thicker lines
for entity in top_n_entities:
    entity_data = energy_cons_country[energy_cons_country['Entity'] == entity].sort_values('Year')
    color = get_country_color(entity)
    line = ax.plot(entity_data['Year'], entity_data['energy_consumption'],
                   color=color, linewidth=3.5, alpha=0.8)

    # Add label at the end of the line with larger text
    last_year = entity_data['Year'].iloc[-1]
    last_value = entity_data['energy_consumption'].iloc[-1]
    ax.text(last_year + 0.5, last_value, entity, fontsize=12, va='center', color=color, fontweight='bold')

# Get all remaining countries (not in top N)
remaining_countries = energy_cons_country[~energy_cons_country['Entity'].isin(top_n_entities)]

if AGGREGATION_METHOD_FIG2.startswith('continent_'):
    # Group by continent
    agg_method = 'sum' if AGGREGATION_METHOD_FIG2 == 'continent_sum' else 'median'
    agg_label = agg_method.capitalize()

    for continent in sorted(continent_colors.keys()):
        continent_data = remaining_countries[remaining_countries['Continent'] == continent]

        if len(continent_data) == 0:
            continue

        # Aggregate by year
        if agg_method == 'sum':
            aggregated_data = continent_data.groupby('Year')['energy_consumption'].sum().reset_index()
        else:
            aggregated_data = continent_data.groupby('Year')['energy_consumption'].median().reset_index()

        if len(aggregated_data) > 0 and not aggregated_data['energy_consumption'].isna().all():
            color = continent_colors[continent]
            ax.plot(aggregated_data['Year'], aggregated_data['energy_consumption'],
                    color=color, linewidth=3.5, alpha=0.5, linestyle='--')

            last_year_agg = aggregated_data['Year'].iloc[-1]
            last_value_agg = aggregated_data['energy_consumption'].iloc[-1]
            label_text = f'Other {continent} ({agg_label})'
            ax.text(last_year_agg + 0.5, last_value_agg, label_text,
                    fontsize=12, va='center', color=color, fontweight='bold', alpha=0.7)

else:  # all_median or all_sum
    agg_method = 'sum' if AGGREGATION_METHOD_FIG2 == 'all_sum' else 'median'
    agg_label = agg_method.capitalize()

    # Aggregate all remaining countries by year
    if agg_method == 'sum':
        aggregated_data = remaining_countries.groupby('Year')['energy_consumption'].sum().reset_index()
    else:
        aggregated_data = remaining_countries.groupby('Year')['energy_consumption'].median().reset_index()

    if len(aggregated_data) > 0 and not aggregated_data['energy_consumption'].isna().all():
        color = '#95A5A6'
        ax.plot(aggregated_data['Year'], aggregated_data['energy_consumption'],
                color=color, linewidth=3.5, alpha=0.7, linestyle='--')

        last_year_agg = aggregated_data['Year'].iloc[-1]
        last_value_agg = aggregated_data['energy_consumption'].iloc[-1]
        label_text = f'All Others ({agg_label})'
        ax.text(last_year_agg + 0.5, last_value_agg, label_text,
                fontsize=12, va='center', color=color, fontweight='bold')

ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel(f'Energy Consumption ({unit_label})', fontsize=14)

# Set y-axis scale
if Y_AXIS_SCALE_FIG2 == 'log':
    ax.set_yscale('log')
    ax.set_ylim(bottom=0.001)  # Set small positive lower limit for log scale
else:
    ax.set_ylim(0, None)

# Increase tick label sizes
ax.tick_params(axis='both', which='major', labelsize=12)

# Remove extra white space and adjust x-axis limits
min_year = energy_cons_country['Year'].min()
max_year = energy_cons_country['Year'].max()
ax.set_xlim(min_year, max_year + 10)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.grid(False)

plt.tight_layout()

# Save figure 2
plt.savefig('../images/figures/energy_consumption_total_timeline.png', dpi=300, bbox_inches='tight')
plt.show()

## ------------------------------------------ FIGURE 3: BAR CHART (PER CAPITA CONSUMPTION) ------------------------------------------

# Get the most recent year for per capita data
max_year_percap = energy_cons_percap['Year'].max()
energy_cons_percap_recent = energy_cons_percap[energy_cons_percap['Year'] == max_year_percap]

# Calculate global total for percentage calculation (note: percentage less meaningful for per capita, but included)
global_total_percap = energy_cons_percap_recent['energy_consumption_per_capita'].sum()

# Get top 10 entities by per capita energy consumption
top_10_percap = energy_cons_percap_recent.nlargest(10, 'energy_consumption_per_capita')
top_10_entities_percap = top_10_percap['Entity'].tolist()

# Get all remaining countries (not in top 10)
remaining_countries_fig3 = energy_cons_percap_recent[~energy_cons_percap_recent['Entity'].isin(top_10_entities_percap)]

# Create list to store aggregated data
aggregated_data_list_percap = []

if AGGREGATION_METHOD_FIG3.startswith('continent_'):
    # Group by continent
    agg_method = 'sum' if AGGREGATION_METHOD_FIG3 == 'continent_sum' else 'median'
    agg_label = agg_method.capitalize()

    for continent in sorted(continent_colors.keys()):
        continent_data = remaining_countries_fig3[remaining_countries_fig3['Continent'] == continent]

        if len(continent_data) == 0:
            continue

        if agg_method == 'sum':
            aggregated_value = continent_data['energy_consumption_per_capita'].sum()
        else:
            aggregated_value = continent_data['energy_consumption_per_capita'].median()

        label_text = f'Other {continent} ({agg_label})'
        aggregated_data_list_percap.append(
            {'Entity': label_text, 'energy_consumption_per_capita': aggregated_value, 'Continent': continent})

else:  # all_median or all_sum
    agg_method = 'sum' if AGGREGATION_METHOD_FIG3 == 'all_sum' else 'median'
    agg_label = agg_method.capitalize()

    if agg_method == 'sum':
        aggregated_value = remaining_countries_fig3['energy_consumption_per_capita'].sum()
    else:
        aggregated_value = remaining_countries_fig3['energy_consumption_per_capita'].median()

    label_text = f'All Others ({agg_label})'
    aggregated_data_list_percap.append({'Entity': label_text, 'energy_consumption_per_capita': aggregated_value, 'Continent': None})

# Create dataframe with top 10 + aggregated data
plot_data_percap = pd.concat([
    top_10_percap[['Entity', 'energy_consumption_per_capita']],
    pd.DataFrame(aggregated_data_list_percap)
], ignore_index=True)

# Create colors for each bar
bar_colors_percap = []
for idx, row in plot_data_percap.iterrows():
    entity = row['Entity']
    if entity.startswith('Other') or entity.startswith('All'):
        if row.get('Continent'):
            bar_colors_percap.append(continent_colors.get(row['Continent'], '#95A5A6'))
        else:
            bar_colors_percap.append('#95A5A6')
    else:
        bar_colors_percap.append(get_country_color(entity))

# Create the bar chart
fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.bar(range(len(plot_data_percap)), plot_data_percap['energy_consumption_per_capita'],
              color=bar_colors_percap, edgecolor='black', linewidth=0.5)

# Add hatch pattern to aggregated bars
for idx, entity in enumerate(plot_data_percap['Entity']):
    if entity.startswith('Other') or entity.startswith('All'):
        bars[idx].set_hatch('//')

# Add percentage labels above each bar
for idx, (bar, value) in enumerate(zip(bars, plot_data_percap['energy_consumption_per_capita'])):
    percentage = (value / global_total_percap) * 100
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height,
            f'{percentage:.1f}%',
            ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_ylabel(f'Energy Consumption Per Capita ({percap_unit_label})', fontsize=12)
ax.set_xticks(range(len(plot_data_percap)))
ax.set_xticklabels(plot_data_percap['Entity'], rotation=45, ha='right', fontsize=10)
ax.set_xlim(-0.5, len(plot_data_percap) - 0.5)
ax.set_ylim(0, None)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.grid(False)

# Add legend only for continents that appear in the chart
continents_in_chart_percap = set()
for idx, row in plot_data_percap.iterrows():
    entity = row['Entity']
    if entity.startswith('Other') and row.get('Continent'):
        continents_in_chart_percap.add(row['Continent'])
    elif not (entity.startswith('Other') or entity.startswith('All')):
        continent = country_to_continent.get(entity)
        if continent:
            continents_in_chart_percap.add(continent)

legend_elements_percap = [Patch(facecolor=continent_colors[continent], edgecolor='black', label=continent)
                          for continent in sorted(continents_in_chart_percap)]

if AGGREGATION_METHOD_FIG3.startswith('all_'):
    legend_elements_percap.append(Patch(facecolor='#95A5A6', edgecolor='black', hatch='//', label='All Others'))

ax.legend(handles=legend_elements_percap, loc='upper right', fontsize=9)

plt.tight_layout()

# Save figure 3
plt.savefig('../images/figures/energy_consumption_percapita_bar.png', dpi=300, bbox_inches='tight')
plt.show()

## ------------------------------------------ FIGURE 4: LINE CHART (PER CAPITA CONSUMPTION) ------------------------------------------

# Get top N countries by most recent year per capita consumption
top_n_entities_percap = energy_cons_percap_recent.nlargest(TOP_N_COUNTRIES_FIG4, 'energy_consumption_per_capita')['Entity'].tolist()

# Create line chart with increased height
fig, ax = plt.subplots(figsize=(16, 14))

# Plot top N countries individually with thicker lines
for entity in top_n_entities_percap:
    entity_data = energy_cons_percap[energy_cons_percap['Entity'] == entity].sort_values('Year')
    color = get_country_color(entity)
    line = ax.plot(entity_data['Year'], entity_data['energy_consumption_per_capita'],
                   color=color, linewidth=3.5, alpha=0.8)

    # Add label at the end of the line with larger text
    last_year = entity_data['Year'].iloc[-1]
    last_value = entity_data['energy_consumption_per_capita'].iloc[-1]
    ax.text(last_year + 0.5, last_value, entity, fontsize=12, va='center', color=color, fontweight='bold')

# Get all remaining countries (not in top N)
remaining_countries_percap = energy_cons_percap[~energy_cons_percap['Entity'].isin(top_n_entities_percap)]

if AGGREGATION_METHOD_FIG4.startswith('continent_'):
    # Group by continent
    agg_method = 'sum' if AGGREGATION_METHOD_FIG4 == 'continent_sum' else 'median'
    agg_label = agg_method.capitalize()

    for continent in sorted(continent_colors.keys()):
        continent_data = remaining_countries_percap[remaining_countries_percap['Continent'] == continent]

        if len(continent_data) == 0:
            continue

        # Aggregate by year
        if agg_method == 'sum':
            aggregated_data = continent_data.groupby('Year')['energy_consumption_per_capita'].sum().reset_index()
        else:
            aggregated_data = continent_data.groupby('Year')['energy_consumption_per_capita'].median().reset_index()

        if len(aggregated_data) > 0 and not aggregated_data['energy_consumption_per_capita'].isna().all():
            color = continent_colors[continent]
            ax.plot(aggregated_data['Year'], aggregated_data['energy_consumption_per_capita'],
                    color=color, linewidth=3.5, alpha=0.5, linestyle='--')

            last_year_agg = aggregated_data['Year'].iloc[-1]
            last_value_agg = aggregated_data['energy_consumption_per_capita'].iloc[-1]
            label_text = f'Other {continent} ({agg_label})'
            ax.text(last_year_agg + 0.5, last_value_agg, label_text,
                    fontsize=12, va='center', color=color, fontweight='bold', alpha=0.7)

else:  # all_median or all_sum
    agg_method = 'sum' if AGGREGATION_METHOD_FIG4 == 'all_sum' else 'median'
    agg_label = agg_method.capitalize()

    # Aggregate all remaining countries by year
    if agg_method == 'sum':
        aggregated_data = remaining_countries_percap.groupby('Year')['energy_consumption_per_capita'].sum().reset_index()
    else:
        aggregated_data = remaining_countries_percap.groupby('Year')['energy_consumption_per_capita'].median().reset_index()

    if len(aggregated_data) > 0 and not aggregated_data['energy_consumption_per_capita'].isna().all():
        color = '#95A5A6'
        ax.plot(aggregated_data['Year'], aggregated_data['energy_consumption_per_capita'],
                color=color, linewidth=3.5, alpha=0.7, linestyle='--')

        last_year_agg = aggregated_data['Year'].iloc[-1]
        last_value_agg = aggregated_data['energy_consumption_per_capita'].iloc[-1]
        label_text = f'All Others ({agg_label})'
        ax.text(last_year_agg + 0.5, last_value_agg, label_text,
                fontsize=12, va='center', color=color, fontweight='bold')

ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel(f'Energy Consumption Per Capita ({percap_unit_label})', fontsize=14)

# Set y-axis scale
if Y_AXIS_SCALE_FIG4 == 'log':
    ax.set_yscale('log')
    ax.set_ylim(bottom=0.001)  # Set small positive lower limit for log scale
else:
    ax.set_ylim(0, None)

# Increase tick label sizes
ax.tick_params(axis='both', which='major', labelsize=12)

# Remove extra white space and adjust x-axis limits
min_year_percap = energy_cons_percap['Year'].min()
max_year_percap = energy_cons_percap['Year'].max()
ax.set_xlim(min_year_percap, max_year_percap + 10)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.grid(False)

plt.tight_layout()

# Save figure 4
plt.savefig('../images/figures/energy_consumption_percapita_timeline.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n" + "="*60)
print("All figures saved successfully!")
print("="*60)
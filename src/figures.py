"""

Creates bar charts and line charts for global energy consumption analysis, showing both
total country-level consumption and per capita consumption patterns over time.

Inputs:
    - ../data/API/global_energy_consumption.csv: Country-level energy consumption data
      Required columns: 'Entity', 'Year', energy consumption column (TWh)
    - ../data/API/per_capita_energy_consumption.csv: Per capita energy consumption data
      Required columns: 'Entity', 'Year', per capita consumption column (kWh)
    - config.py: Contains not_countries list and countries_by_continent dictionary

Outputs:
    - Bar charts: Top N countries + aggregated remaining countries for most recent year
    - Line charts: Historical trends for top N countries + aggregated remaining countries
    - All figures saved to ../images/figures/

"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from config import *

# ============================================================
# CONFIGURATION
# ============================================================
ENERGY_UNIT_COUNTRY = 'PWh'
ENERGY_UNIT_PERCAPITA = 'kWh'

# Unified configuration for all figures
FIGURE_CONFIG = {
    'fig1': {'top_n': 10, 'agg_method': 'continent_median', 'scale': 'linear'},
    'fig2': {'top_n': 6, 'agg_method': 'continent_median', 'scale': 'linear'},
    'fig3': {'top_n': 10, 'agg_method': 'continent_median', 'scale': 'linear'},
    'fig4': {'top_n': 6, 'agg_method': 'continent_median', 'scale': 'linear'}
}

# Color palette for continents
continent_colors = {
    'Africa': '#E74C3C', 'Asia': '#F39C12', 'Europe': '#3498DB',
    'North America': '#2ECC71', 'South America': '#9B59B6',
    'Oceania': '#1ABC9C', 'Antarctica': '#95A5A6'
}

not_countries = ['Africa', 'Africa (EI)', 'Africa (EIA)', 'Antarctica', 'Asia', 'Asia Pacific (EI)',
                 'Asia and Oceania (EIA)', 'Australia and New Zealand (EIA)', 'CIS (EI)', 'Central America (EI)',
                 'Central and South America (EIA)', 'Eastern Africa (EI)', 'Eastern Europe and Eurasia (EIA)',
                 'Eurasia (EIA)', 'Europe', 'Europe (EI)', 'Europe (EIA)', 'European Union (27)',
                 'High-income countries', 'Low-income countries', 'Lower-middle-income countries', 'Middle Africa (EI)',
                 'Middle East (EI)', 'Middle East (EIA)', 'Non-OECD (EI)', 'Non-OECD (EIA)', 'Non-OPEC (EIA)',
                 'North America', 'North America (EI)', 'OECD (EI)', 'OECD (EIA)', 'OPEC (EIA)', 'Oceania',
                 'Other Americas (EIA)', 'Other Asia Pacific (EI)', 'Other Asia-Pacific (EIA)', 'Other CIS (EI)',
                 'Other Caribbean (EI)', 'Other Europe (EI)', 'Other Middle East (EI)', 'Other Northern Africa (EI)',
                 'Other South America (EI)', 'Other Southern Africa (EI)', 'Persian Gulf (EIA)', 'South America',
                 'South and Central America (EI)', 'U.S. Pacific Islands (EIA)', 'U.S. Territories (EIA)',
                 'Upper-middle-income countries', 'Western Africa (EI)', 'Western Europe (EIA)', 'World']

countries_by_continent = {
    'Africa': [
        'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
        'Cameroon', 'Cape Verde', 'Central African Republic', 'Chad', 'Comoros',
        'Congo', "Cote d'Ivoire", 'Democratic Republic of Congo', 'Djibouti',
        'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon',
        'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya', 'Lesotho',
        'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
        'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria',
        'Reunion', 'Rwanda', 'Saint Helena', 'Sao Tome and Principe', 'Senegal',
        'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan',
        'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Western Sahara',
        'Zambia', 'Zimbabwe'
    ],
    'Asia': [
        'Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Bhutan',
        'Brunei', 'Cambodia', 'China', 'East Timor', 'Georgia', 'Hong Kong',
        'India', 'Indonesia', 'Iran', 'Iraq', 'Israel', 'Japan', 'Jordan',
        'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Macao',
        'Malaysia', 'Maldives', 'Mongolia', 'Myanmar', 'Nepal', 'North Korea',
        'Oman', 'Pakistan', 'Palestine', 'Philippines', 'Qatar',
        'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syria',
        'Taiwan', 'Tajikistan', 'Thailand', 'Turkey', 'Turkmenistan',
        'United Arab Emirates', 'Uzbekistan', 'Vietnam', 'Yemen'
    ],
    'Europe': [
        'Albania', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina',
        'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Czechoslovakia', 'Denmark',
        'East Germany', 'Estonia', 'Faroe Islands', 'Finland', 'France',
        'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kosovo',
        'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Montenegro',
        'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal',
        'Romania', 'Serbia', 'Serbia and Montenegro', 'Slovakia', 'Slovenia',
        'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom',
        'USSR', 'West Germany', 'Yugoslavia', 'Russia'
    ],
    'North America': [
        'Antigua and Barbuda', 'Aruba', 'Bahamas', 'Barbados', 'Belize',
        'Bermuda', 'British Virgin Islands', 'Canada', 'Cayman Islands',
        'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador',
        'Greenland', 'Grenada', 'Guadeloupe', 'Guatemala', 'Haiti', 'Honduras',
        'Jamaica', 'Martinique', 'Mexico', 'Montserrat', 'Nicaragua', 'Panama',
        'Puerto Rico', 'Saint Kitts and Nevis', 'Saint Lucia',
        'Saint Pierre and Miquelon', 'Saint Vincent and the Grenadines',
        'Trinidad and Tobago', 'Turks and Caicos Islands', 'United States',
        'United States Virgin Islands'
    ],
    'South America': [
        'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador',
        'French Guiana', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay',
        'Venezuela'
    ],
    'Oceania': [
        'American Samoa', 'Australia', 'Cook Islands', 'Fiji',
        'French Polynesia', 'Guam', 'Kiribati', 'Micronesia (country)',
        'Nauru', 'New Caledonia', 'New Zealand', 'Niue',
        'Northern Mariana Islands', 'Papua New Guinea', 'Samoa',
        'Solomon Islands', 'Tonga', 'Tuvalu', 'Vanuatu', 'Wake Island (EIA)'
    ],
    'Antarctica': [
        'Falkland Islands'
    ]
}

# HELPER FUNCTIONS

def create_country_to_continent_map(countries_by_continent):
    """Create reverse mapping: country -> continent"""
    return {country: continent
            for continent, countries in countries_by_continent.items()
            for country in countries}


def get_country_color(country, country_to_continent, continent_colors):
    """Get color for a country based on its continent"""
    continent = country_to_continent.get(country, 'Other')
    return continent_colors.get(continent, '#34495E')


def find_column(df, possible_names, exclude_cols=['Entity', 'Code', 'Year', 'Continent']):
    """Find the first matching column from a list of possibilities"""
    # Try exact matches first
    for col in possible_names:
        if col in df.columns:
            return col

    # Fall back to first numeric column not in exclude list
    for col in df.columns:
        if col not in exclude_cols:
            return col

    raise ValueError(f"Could not find column. Available: {df.columns.tolist()}")


def convert_units(df, column, from_unit, to_unit):
    """Convert energy units"""
    conversions = {
        ('TWh', 'PWh'): lambda x: x / 1000,
        ('TWh', 'TWh'): lambda x: x,
        ('kWh', 'kWh'): lambda x: x,
        ('kWh', 'PWh'): lambda x: x / 1e12,
        ('kWh', 'TWh'): lambda x: x / 1e9,
    }

    conversion_func = conversions.get((from_unit, to_unit))
    if conversion_func is None:
        raise ValueError(f"No conversion from {from_unit} to {to_unit}")

    return conversion_func(df[column])


def aggregate_data(remaining_df, value_col, method, continent_col='Continent'):
    """Aggregate remaining countries by continent or all together"""
    aggregated_list = []

    if method.startswith('continent_'):
        agg_func = 'sum' if method == 'continent_sum' else 'median'
        agg_label = agg_func.capitalize()

        for continent in sorted(continent_colors.keys()):
            continent_data = remaining_df[remaining_df[continent_col] == continent]
            if len(continent_data) == 0:
                continue

            aggregated_value = continent_data[value_col].agg(agg_func)
            label = f'Other {continent} ({agg_label})'
            aggregated_list.append({
                'Entity': label,
                value_col: aggregated_value,
                'Continent': continent
            })

    else:  # all_median or all_sum
        agg_func = 'sum' if method == 'all_sum' else 'median'
        agg_label = agg_func.capitalize()

        aggregated_value = remaining_df[value_col].agg(agg_func)
        label = f'All Others ({agg_label})'
        aggregated_list.append({
            'Entity': label,
            value_col: aggregated_value,
            'Continent': None
        })

    return aggregated_list


def create_bar_chart(plot_data, value_col, country_to_continent, continent_colors,
                     global_total, unit_label, agg_method, filename):
    """Create a bar chart for energy consumption"""

    # Assign colors to bars
    bar_colors = []
    for _, row in plot_data.iterrows():
        entity = row['Entity']
        if entity.startswith('Other') or entity.startswith('All'):
            color = continent_colors.get(row.get('Continent'), '#95A5A6')
        else:
            color = get_country_color(entity, country_to_continent, continent_colors)
        bar_colors.append(color)

    # Create chart
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(plot_data)), plot_data[value_col],
                  color=bar_colors, edgecolor='black', linewidth=0.5)

    # Add hatch pattern to aggregated bars
    for idx, entity in enumerate(plot_data['Entity']):
        if entity.startswith('Other') or entity.startswith('All'):
            bars[idx].set_hatch('//')

    # Add percentage labels
    for bar, value in zip(bars, plot_data[value_col]):
        percentage = (value / global_total) * 100
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height,
                f'{percentage:.1f}%', ha='center', va='bottom',
                fontsize=9, fontweight='bold')

    # Formatting
    ax.set_ylabel(f'Energy Consumption ({unit_label})', fontsize=12)
    ax.set_xticks(range(len(plot_data)))
    ax.set_xticklabels(plot_data['Entity'], rotation=45, ha='right', fontsize=10)
    ax.set_xlim(-0.5, len(plot_data) - 0.5)
    ax.set_ylim(0, None)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(False)

    # Add legend
    continents_in_chart = set()
    for _, row in plot_data.iterrows():
        entity = row['Entity']
        if entity.startswith('Other') and row.get('Continent'):
            continents_in_chart.add(row['Continent'])
        elif not (entity.startswith('Other') or entity.startswith('All')):
            continent = country_to_continent.get(entity)
            if continent:
                continents_in_chart.add(continent)

    legend_elements = [Patch(facecolor=continent_colors[c], edgecolor='black', label=c)
                       for c in sorted(continents_in_chart)]

    if agg_method.startswith('all_'):
        legend_elements.append(Patch(facecolor='#95A5A6', edgecolor='black',
                                     hatch='//', label='All Others'))

    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def create_line_chart(df, value_col, top_n, country_to_continent, continent_colors,
                      agg_method, unit_label, y_scale, filename):
    """Create a line chart for energy consumption over time"""

    # Get most recent year and top N countries
    max_year = df['Year'].max()
    recent_data = df[df['Year'] == max_year]
    top_entities = recent_data.nlargest(top_n, value_col)['Entity'].tolist()

    # Create chart
    fig, ax = plt.subplots(figsize=(16, 14))

    # Plot top N countries
    for entity in top_entities:
        entity_data = df[df['Entity'] == entity].sort_values('Year')
        color = get_country_color(entity, country_to_continent, continent_colors)
        ax.plot(entity_data['Year'], entity_data[value_col],
                color=color, linewidth=3.5, alpha=0.8)

        # Add label at end
        last_year = entity_data['Year'].iloc[-1]
        last_value = entity_data[value_col].iloc[-1]
        ax.text(last_year + 0.5, last_value, entity,
                fontsize=12, va='center', color=color, fontweight='bold')

    # Aggregate remaining countries
    remaining = df[~df['Entity'].isin(top_entities)]

    if agg_method.startswith('continent_'):
        agg_func = 'sum' if agg_method == 'continent_sum' else 'median'
        agg_label = agg_func.capitalize()

        for continent in sorted(continent_colors.keys()):
            continent_data = remaining[remaining['Continent'] == continent]
            if len(continent_data) == 0:
                continue

            aggregated = continent_data.groupby('Year')[value_col].agg(agg_func).reset_index()

            if len(aggregated) > 0 and not aggregated[value_col].isna().all():
                color = continent_colors[continent]
                ax.plot(aggregated['Year'], aggregated[value_col],
                        color=color, linewidth=3.5, alpha=0.5, linestyle='--')

                last_year = aggregated['Year'].iloc[-1]
                last_value = aggregated[value_col].iloc[-1]
                label = f'Other {continent} ({agg_label})'
                ax.text(last_year + 0.5, last_value, label,
                        fontsize=12, va='center', color=color,
                        fontweight='bold', alpha=0.7)

    else:  # all_median or all_sum
        agg_func = 'sum' if agg_method == 'all_sum' else 'median'
        agg_label = agg_func.capitalize()

        aggregated = remaining.groupby('Year')[value_col].agg(agg_func).reset_index()

        if len(aggregated) > 0 and not aggregated[value_col].isna().all():
            ax.plot(aggregated['Year'], aggregated[value_col],
                    color='#95A5A6', linewidth=3.5, alpha=0.7, linestyle='--')

            last_year = aggregated['Year'].iloc[-1]
            last_value = aggregated[value_col].iloc[-1]
            ax.text(last_year + 0.5, last_value, f'All Others ({agg_label})',
                    fontsize=12, va='center', color='#95A5A6', fontweight='bold')

    # Formatting
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel(f'Energy Consumption ({unit_label})', fontsize=14)

    if y_scale == 'log':
        ax.set_yscale('log')
        ax.set_ylim(bottom=0.001)
    else:
        ax.set_ylim(0, None)

    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_xlim(df['Year'].min(), df['Year'].max() + 10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


# ============================================================
# MAIN EXECUTION
# ============================================================

# Setup
country_to_continent = create_country_to_continent_map(countries_by_continent)
os.makedirs('../images/figures', exist_ok=True)

# Load and clean data
energy_cons_country = pd.read_csv('../data/API/global_energy_consumption.csv')
energy_cons_country = energy_cons_country[~energy_cons_country['Entity'].isin(not_countries)]
energy_cons_country['Continent'] = energy_cons_country['Entity'].map(country_to_continent)

energy_cons_percap = pd.read_csv('../data/API/per_capita_energy_consumption.csv')
energy_cons_percap = energy_cons_percap[~energy_cons_percap['Entity'].isin(not_countries)]
energy_cons_percap['Continent'] = energy_cons_percap['Entity'].map(country_to_continent)

# Find and convert country consumption column
country_col = find_column(energy_cons_country, [
    'primary_energy_consumption__twh',
    'energy_consumption__twh',
    'primary_energy_consumption_twh'
])
print(f"Using country consumption column: {country_col}")

energy_cons_country['energy_consumption'] = convert_units(
    energy_cons_country, country_col, 'TWh', ENERGY_UNIT_COUNTRY
)
unit_label_country = ENERGY_UNIT_COUNTRY

# Find and convert per capita column
percap_col = find_column(energy_cons_percap, [
    'per_capita_electricity_kwh',
    'primary_energy_consumption_per_capita__kwh',
    'energy_per_capita',
    'per_capita_energy_consumption__kwh'
])
print(f"Using per capita column: {percap_col}")

energy_cons_percap['energy_consumption_per_capita'] = convert_units(
    energy_cons_percap, percap_col, 'kWh', ENERGY_UNIT_PERCAPITA
)
percap_unit_label = f'{ENERGY_UNIT_PERCAPITA}/person'

# Print configuration
print(f"\nCountry energy unit: {unit_label_country}")
print(f"Per capita energy unit: {percap_unit_label}")
for fig_name, config in FIGURE_CONFIG.items():
    print(f"{fig_name.upper()}: Top {config['top_n']}, {config['agg_method']}, {config['scale']}")

# ============================================================
# FIGURE 1: BAR CHART (TOTAL CONSUMPTION)
# ============================================================
max_year = energy_cons_country['Year'].max()
recent_country = energy_cons_country[energy_cons_country['Year'] == max_year]
global_total_country = recent_country['energy_consumption'].sum()

top_n = FIGURE_CONFIG['fig1']['top_n']
top_entities = recent_country.nlargest(top_n, 'energy_consumption')
remaining = recent_country[~recent_country['Entity'].isin(top_entities['Entity'])]

aggregated = aggregate_data(remaining, 'energy_consumption', FIGURE_CONFIG['fig1']['agg_method'])
plot_data = pd.concat([
    top_entities[['Entity', 'energy_consumption']],
    pd.DataFrame(aggregated)
], ignore_index=True)

create_bar_chart(plot_data, 'energy_consumption', country_to_continent, continent_colors,
                 global_total_country, unit_label_country, FIGURE_CONFIG['fig1']['agg_method'],
                 '../images/figures/energy_consumption_country_bar.png')

# ============================================================
# FIGURE 2: LINE CHART (TOTAL CONSUMPTION)
# ============================================================
create_line_chart(energy_cons_country, 'energy_consumption',
                  FIGURE_CONFIG['fig2']['top_n'], country_to_continent,
                  continent_colors, FIGURE_CONFIG['fig2']['agg_method'],
                  unit_label_country, FIGURE_CONFIG['fig2']['scale'],
                  '../images/figures/energy_consumption_country_timeline.png')

# ============================================================
# FIGURE 3: BAR CHART (PER CAPITA CONSUMPTION)
# ============================================================
recent_percap = energy_cons_percap[energy_cons_percap['Year'] == max_year]
global_total_percap = recent_percap['energy_consumption_per_capita'].sum()

top_n = FIGURE_CONFIG['fig3']['top_n']
top_entities_percap = recent_percap.nlargest(top_n, 'energy_consumption_per_capita')
remaining_percap = recent_percap[~recent_percap['Entity'].isin(top_entities_percap['Entity'])]

aggregated_percap = aggregate_data(remaining_percap, 'energy_consumption_per_capita',
                                   FIGURE_CONFIG['fig3']['agg_method'])
plot_data_percap = pd.concat([
    top_entities_percap[['Entity', 'energy_consumption_per_capita']],
    pd.DataFrame(aggregated_percap)
], ignore_index=True)

create_bar_chart(plot_data_percap, 'energy_consumption_per_capita', country_to_continent,
                 continent_colors, global_total_percap, percap_unit_label,
                 FIGURE_CONFIG['fig3']['agg_method'],
                 '../images/figures/energy_consumption_percapita_bar.png')

# ============================================================
# FIGURE 4: LINE CHART (PER CAPITA CONSUMPTION)
# ============================================================
create_line_chart(energy_cons_percap, 'energy_consumption_per_capita',
                  FIGURE_CONFIG['fig4']['top_n'], country_to_continent,
                  continent_colors, FIGURE_CONFIG['fig4']['agg_method'],
                  percap_unit_label, FIGURE_CONFIG['fig4']['scale'],
                  '../images/figures/energy_consumption_percapita_timeline.png')

print("\n" + "=" * 60)
print("All figures saved successfully!")
print("=" * 60)
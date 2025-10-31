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
        'Zambia', 'Zimbabwe', 'Seychelles', 'Saint Helena', 'Mauritius',
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
        'United Arab Emirates', 'Uzbekistan', 'Vietnam', 'Yemen',  'British Indian Ocean Territory'
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
        'United States Virgin Islands', 'Clipperton Island'
    ],
    'South America': [
        'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador',
        'French Guiana', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay',
        'Venezuela', 'South Georgia and the Islands'
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

# Color palette for continents
continent_colors = {
    'Africa': '#E74C3C',
    'Asia': '#F39C12',
    'Europe': '#3498DB',
    'North America': '#2ECC71',
    'South America': '#9B59B6',
    'Oceania': '#1ABC9C',
    'Antarctica': '#95A5A6'
}
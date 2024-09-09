import pandas as pd
import os


def translate_coords(x, y, gore_section):
    # Define width and height of each gore half
    gore_width = 4000 / 12  # mm # THIS SHOULD BE CHANGED TO TAKE THE ACTUAL VARIABLE FROM MAIN IN THE FUTURE
    gore_height = 1000  # mm

    # Get the gore number and hemisphere from the section
    gore_num = int(gore_section[:-1])  # Get gore number (1-12)
    hemisphere = gore_section[-1]      # Get hemisphere (N/S)

    # Translate x-coordinates: Shift each gore section to its own 0 to 333.33 range
    x_translated = x - ((gore_num - 1) * 333.33 - 2000)

    # Translate y-coordinates: Shift northern and southern hemisphere
    if hemisphere == "N":
        y_translated = y  # Northern hemisphere coordinates stay in the range 0-1000
    else:
        y_translated = y + 1000  # Southern hemisphere is below, so shift by +1000

    return x_translated, y_translated

def create_gorehalf_coords(csv_input_path="led_coordinates_global.csv"):
    # Get the root directory of the project (assumes script is run from 'src')
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, 'outputs')

    # Ensure the 'outputs' directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define the path for the xlsx output
    xlsx_output_path = os.path.join(output_dir, "gorehalf_coordinates_with_sheets.xlsx")

    # Read the CSV file generated from the previous script
    df = pd.read_csv(csv_input_path)

    # Translate the coordinates and store them in new columns
    df[['Mid X (mm)', 'Mid Y (mm)']] = df.apply(lambda row: translate_coords(row['X (mm)'], row['Y (mm)'], row['Gore Section']), axis=1, result_type='expand')

    # Reorder the data to follow the gore half order: 1N, 1S, 2N, 2S, ..., 12N, 12S
    df['Sort_Key'] = df['Gore Section'].map(lambda x: (int(x[:-1]), x[-1]))
    df = df.sort_values('Sort_Key')

    # Drop the Sort_Key column since it's no longer needed
    df.drop(columns=['Sort_Key'], inplace=True)

    # Create summary of totals per gore section
    gore_sections = [f"{i}{h}" for i in range(1, 13) for h in ['N', 'S']]
    summary_data = [(section, len(df[df['Gore Section'] == section])) for section in gore_sections]
    summary_df = pd.DataFrame(summary_data, columns=['Gore Section', 'Total LEDs'])

    # Create a new Excel writer object
    with pd.ExcelWriter(xlsx_output_path, engine='openpyxl') as writer:
        # Write the summary starting in row 1
        summary_df.to_excel(writer, sheet_name='Master', startrow=0, startcol=5, index=False)

        # Write the full data starting immediately after the summary, at row 1
        df[['Mid X (mm)', 'Mid Y (mm)', 'Gore Section']].to_excel(writer, sheet_name='Master', startrow=0, index=False)

        # Loop through each gore section, create individual sheets for each
        for gore_section in gore_sections:
            section_df = df[df['Gore Section'] == gore_section]
            if not section_df.empty:
                section_df[['Mid X (mm)', 'Mid Y (mm)']].to_excel(writer, sheet_name=gore_section, index=False)

    print(f"Translated coordinates and sheets saved to {xlsx_output_path}.")


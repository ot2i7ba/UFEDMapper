# Copyright (c) 2024 ot2i7ba
# https://github.com/ot2i7ba/
# This code is licensed under the MIT License (see LICENSE for details).

"""
Processes a KML file to generate an interactive map using Plotly.
"""

import os
import pandas as pd
from lxml import etree
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import logging
import pytz
import numpy as np
import time

# Global Constants
LOG_FILE = 'UFEDMapper.log'
DEFAULT_KML_FILE = 'Locations.kml'

# Configure logging
def configure_logging():
    """Configure logging to log to both console and file."""
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'w') as f:
                f.write("")
            print(f"Log file created: {LOG_FILE}")
        except IOError as e:
            print(f"Failed to create log file: {e}")
    
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(LOG_FILE)
    
    formatter = CustomFormatter('%(asctime)s - %(levelname)s - %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logging.basicConfig(level=logging.INFO,
                        handlers=[file_handler, console_handler])
    
    logging.info("Logging configured successfully")

class CustomFormatter(logging.Formatter):
    """Custom formatter to output log messages in a specific format."""

    def format(self, record):
        log_message = super().format(record)
        return log_message.replace(" - ", "\n", 1)

# Helper functions
def clear_screen():
    """Clear the screen depending on the operating system."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_blank_line():
    """Print a blank line for better readability."""
    print("\n")

def print_header():
    """Print the header for the script."""
    print(" UFEDMapper v0.1.2 by ot2i7ba ")
    print("===============================")
    print_blank_line()

def clean_html(html_text):
    """
    Remove HTML tags from a string.

    Args:
        html_text (str): The HTML string to clean.

    Returns:
        str: The cleaned text.
    """
    if html_text is None:
        return None
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text()

# User interaction functions
def get_kml_filename():
    """
    Prompt the user to input the KML filename or choose from available KML files in the script's directory.

    Returns:
        str: The selected KML file name.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kml_files = sorted([f for f in os.listdir(script_dir) if f.endswith('.kml')], key=lambda x: x.lower())
    
    if (kml_files):
        print("Available KML files:")
        for idx, file in enumerate(kml_files, 1):
            print(f"{idx}. {file}")
        print("e. Exit")
        print_blank_line()
        
        while True:
            choice = input(f"Enter the number of the desired KML file (Enter to use '{DEFAULT_KML_FILE}' or 'e' to exit): ").strip().lower()
            if choice == 'e':
                print("Exiting the script. Goodbye!")
                logging.info("User chose to exit the script.")
                exit(0)
            elif not choice:
                kml_file = DEFAULT_KML_FILE
                break
            else:
                try:
                    choice = int(choice)
                    if 1 <= choice <= len(kml_files):
                        kml_file = kml_files[choice - 1]
                        break
                    else:
                        raise ValueError
                except ValueError:
                    print("Invalid input. Please enter a valid number or 'e' to exit.")
    else:
        print("No KML files found in the directory.")
        kml_file = input(f"Input KML filename (enter for '{DEFAULT_KML_FILE}'): ")
        print_blank_line()
        if not kml_file:
            kml_file = DEFAULT_KML_FILE
        elif not kml_file.endswith('.kml'):
            kml_file += '.kml'

    logging.info(f"KML file chosen: {kml_file}")
    return kml_file

def get_html_filename(default_name):
    """
    Prompt the user to input the output HTML filename.

    Args:
        default_name (str): The default name for the HTML file.

    Returns:
        str: The chosen HTML file name.
    """
    print_blank_line()
    html_file = input(f"Output html filename (enter for '{default_name}'): ")
    print_blank_line()

    if not html_file:
        html_file = default_name
    elif not html_file.endswith('.html'):
        html_file += '.html'
    logging.info(f"HTML filename chosen: {html_file}")
    return html_file

def choose_plot_types():
    """
    Prompt the user to choose one or more plot types.

    Returns:
        list: List of chosen plot types.
    """
    print_blank_line()
    print("Choose one or more plot types (e.g., 1,2,5):")
    plot_types = {
        "1": "Scatter Plot",
        "2": "Heatmap",
        "3": "Lines Plot",
        "4": "Circle Markers",
        "5": "Polygon",
    }
    for key, value in plot_types.items():
        print(f"{key}. {value}")
    
    print_blank_line()
    choices = input("Enter the numbers of the plot types: ")
    chosen_plot_types = [plot_types.get(choice.strip(), "Scatter Plot") for choice in choices.split(',')]
    logging.info(f"Plot types chosen: {chosen_plot_types}")
    return chosen_plot_types

def get_date_range(df):
    """
    Prompt the user to input a date range.

    Args:
        df (pd.DataFrame): The DataFrame containing timestamp data.

    Returns:
        tuple: The start and end dates as datetime objects.
    """
    if df['timestamp'].notnull().any():
        min_date = df['timestamp'].min().strftime("%d.%m.%Y")
        max_date = df['timestamp'].max().strftime("%d.%m.%Y")
        print(f"Available date range: {min_date} to {max_date}")
    
    def valid_date_input(prompt):
        while True:
            date_str = input(prompt)
            if not date_str:
                return None
            try:
                date = datetime.strptime(date_str, "%d.%m.%Y").replace(tzinfo=pytz.UTC)
                if date < df['timestamp'].min() or date > df['timestamp'].max():
                    print(f"Error: Date must be between {min_date} and {max_date}.")
                else:
                    return date
            except ValueError:
                print("Invalid date format. Please use DD.MM.YYYY.")
    
    print_blank_line()
    start_date = valid_date_input("Enter start date (DD.MM.YYYY) or press Enter to skip: ")
    end_date = valid_date_input("Enter end date (DD.MM.YYYY) or press Enter to skip: ")

    if start_date and end_date and start_date > end_date:
        print("Error: Start date cannot be after end date.")
        return get_date_range(df)
    
    if not start_date and end_date:
        start_date = df['timestamp'].min()
    if start_date and not end_date:
        end_date = df['timestamp'].max()
    
    return start_date, end_date

# File operations and parsing functions
def validate_kml_file(kml_file):
    """
    Validate if the file exists and is a KML file.

    Args:
        kml_file (str): The KML file name.

    Returns:
        str: The validated KML file name.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a KML file.
    """
    if not os.path.isfile(kml_file):
        logging.error(f"Error: The file '{kml_file}' could not be found.")
        raise FileNotFoundError(f"Error: The file '{kml_file}' could not be found.")
    if not kml_file.endswith('.kml'):
        logging.error(f"Error: The file '{kml_file}' is not a KML file.")
        raise ValueError(f"Error: The file '{kml_file}' is not a KML file.")
    logging.info(f"Validated KML file: {kml_file}")
    return kml_file

def parse_kml(file_path):
    """
    Parse the KML file and extract relevant data using parallel processing.

    Args:
        file_path (str): Path to the KML file.

    Returns:
        tuple: DataFrame containing the parsed data, count of valid timestamps, count of invalid timestamps.
    
    Raises:
        ValueError: If there is an error parsing the KML file.
    """
    def process_placemark(elem):
        try:
            placemark_data = {}
            placemark_data['name'] = elem.find('.//{http://www.opengis.net/kml/2.2}name').text
            coordinates = elem.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip()
            coord_parts = coordinates.split(',')
            placemark_data['longitude'], placemark_data['latitude'] = map(float, coord_parts[:2])

            timestamp_elem = elem.find('.//{http://www.opengis.net/kml/2.2}TimeStamp')
            if timestamp_elem is not None:
                when = timestamp_elem.find('{http://www.opengis.net/kml/2.2}when').text
                try:
                    placemark_data['timestamp'] = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(pytz.UTC)
                except ValueError:
                    placemark_data['timestamp'] = None
            else:
                placemark_data['timestamp'] = None

            description_elem = elem.find('.//{http://www.opengis.net/kml/2.2}description')
            placemark_data['description'] = clean_html(description_elem.text) if description_elem is not None else None

            extended_data = elem.findall('.//{http://www.opengis.net/kml/2.2}Data')
            for data_elem in extended_data:
                key = data_elem.get('name')
                value = data_elem.find('{http://www.opengis.net/kml/2.2}value').text
                placemark_data[key] = value

            return placemark_data
        except (etree.XMLSyntaxError, AttributeError) as e:
            logging.error(f"Error parsing placemark: {e}")
            return None

    try:
        context = etree.iterparse(file_path, events=('end',), tag='{http://www.opengis.net/kml/2.2}Placemark')
        placemarks = []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_placemark, elem): elem for event, elem in context}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Parsing KML file", unit=" placemarks"):
                placemark_data = future.result()
                if placemark_data:
                    placemarks.append(placemark_data)
                futures[future].clear()

        df = pd.DataFrame(placemarks)
        valid_timestamp_count = df['timestamp'].notna().sum()
        invalid_timestamp_count = df['timestamp'].isna().sum()

        logging.info(f"KML file parsed successfully with {len(placemarks)} placemarks, {valid_timestamp_count} valid timestamps, {invalid_timestamp_count} invalid timestamps")
        return df, valid_timestamp_count, invalid_timestamp_count

    except (etree.XMLSyntaxError, AttributeError) as e:
        logging.error(f"Error parsing KML file: {e}")
        raise ValueError(f"Error parsing KML file: {e}")

def save_dataframe(df, output_file):
    """
    Save the DataFrame to a feather file and export a CSV for user reference.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_file (str): The output file name.
    """
    feather_file = output_file.replace('.csv', '.feather')
    df.reset_index(drop=True).to_feather(feather_file)
    df.to_csv(output_file, index=False)
    logging.info(f"Data saved as {feather_file} and {output_file}")
    print(f"Data saved as {feather_file} and {output_file}")

def save_dataframe_with_timestamps(df, output_file):
    """
    Save the DataFrame with valid timestamps to separate feather and CSV files.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_file (str): The output file name.

    Returns:
        tuple: The feather and CSV file names with timestamps.
    """
    timestamped_df = df.dropna(subset=['timestamp']).reset_index(drop=True)
    timestamped_output_file = output_file.replace('.csv', '_timestamps.feather')
    timestamped_csv_file = output_file.replace('.csv', '_timestamps.csv')
    timestamped_df.to_feather(timestamped_output_file)
    timestamped_df.to_csv(timestamped_csv_file, index=False)
    logging.info(f"Data with timestamps saved as {timestamped_output_file} and {timestamped_csv_file}")
    print(f"Data with timestamps saved as {timestamped_output_file} and {timestamped_csv_file}")
    return timestamped_output_file, timestamped_csv_file

def get_output_filename(kml_file, prefix):
    """
    Generate the output filename based on the KML filename.

    Args:
        kml_file (str): The KML file name.
        prefix (str): The prefix for the output file.

    Returns:
        str: The generated output file name.
    """
    base_name = os.path.splitext(os.path.basename(kml_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = f"{prefix}_{timestamp}_{base_name}.csv"
    logging.info(f"Output CSV filename: {output_file}")
    return output_file

# Data analysis functions
def filter_by_date(df, start_date, end_date):
    """
    Filter the DataFrame by the given date range.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        start_date (datetime): The start date for filtering.
        end_date (datetime): The end date for filtering.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    return df.loc[mask]

def analyze_data(df):
    """
    Analyze the parsed data and generate insights using numpy for performance.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.

    Returns:
        dict: Analysis results including total points, duplicate points, unique points, and top visited locations.
    """
    total_points = len(df)
    duplicate_points = df.duplicated(subset=['longitude', 'latitude']).sum()
    unique_points = total_points - duplicate_points

    # Count occurrences of each location using numpy
    location_counts = df.groupby(['longitude', 'latitude']).size().reset_index(name='counts').to_numpy()
    
    # Top 10 most visited locations
    top_10_most_visited = location_counts[np.argsort(location_counts[:, 2])][-10:]
    
    # Top 10 least visited locations
    top_10_least_visited = location_counts[np.argsort(location_counts[:, 2])][:10]

    return {
        'total_points': total_points,
        'duplicate_points': duplicate_points,
        'unique_points': unique_points,
        'top_10_most_visited': pd.DataFrame(top_10_most_visited, columns=['longitude', 'latitude', 'counts']),
        'top_10_least_visited': pd.DataFrame(top_10_least_visited, columns=['longitude', 'latitude', 'counts'])
    }

def save_analysis(analysis, output_file, valid_timestamp_count, invalid_timestamp_count):
    """
    Save the analysis to an Excel file.

    Args:
        analysis (dict): The analysis results.
        output_file (str): The output file name.
        valid_timestamp_count (int): The count of valid timestamps.
        invalid_timestamp_count (int): The count of invalid timestamps.
    """
    analysis_file = output_file.replace('.csv', '_analysis.xlsx')
    
    with pd.ExcelWriter(analysis_file) as writer:
        pd.DataFrame([{
            'Total Points': analysis['total_points'],
            'Duplicate Points': analysis['duplicate_points'],
            'Unique Points': analysis['unique_points'],
            'Valid Timestamps': valid_timestamp_count,
            'Invalid Timestamps': invalid_timestamp_count
        }]).to_excel(writer, sheet_name='Summary', index=False)
        
        analysis['top_10_most_visited'].to_excel(writer, sheet_name='Top 10 Most Visited', index=False)
        analysis['top_10_least_visited'].to_excel(writer, sheet_name='Top 10 Least Visited', index=False)
    
    logging.info(f"Analysis saved as {analysis_file}")
    print(f"Analysis saved as {analysis_file}")

# Plot creation functions
def create_plotly_map(df, plot_type):
    """
    Create the appropriate plot based on the plot type selected using Plotly.

    Args:
        df (pd.DataFrame): The DataFrame to plot.
        plot_type (str): The type of plot to create.

    Returns:
        plotly.graph_objects.Figure: The created plot.

    Raises:
        ValueError: If an unknown plot type is specified.
    """
    import plotly.express as px  # Lazy Load Plotly inside the function
    
    hover_data = {col: True for col in df.columns if col not in ['name', 'longitude', 'latitude']}
    if plot_type == "Scatter Plot":
        fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", hover_name="name", hover_data=hover_data, zoom=3)
    elif plot_type == "Heatmap":
        fig = px.density_mapbox(df, lat="latitude", lon="longitude", hover_name="name", hover_data=hover_data, zoom=3)
    elif plot_type == "Lines Plot":
        fig = px.line_geo(df, lat="latitude", lon="longitude", hover_name="name", hover_data=hover_data, projection="orthographic")
    elif plot_type == "Circle Markers":
        fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", hover_name="name", hover_data=hover_data, zoom=3, size_max=15)
    elif plot_type == "Polygon":
        fig = px.line_geo(df, lat="latitude", lon="longitude", hover_name="name", hover_data=hover_data, line_group="name", projection="orthographic")
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")

    fig.update_layout(mapbox_style="open-street-map", height=1080, width=1920)
    logging.info(f"Map created: {plot_type}")
    return fig

def export_plot(m, plot_name, prefix):
    """
    Export the plot to an HTML file.

    Args:
        m (plotly.graph_objects.Figure): The plot to export.
        plot_name (str): The name of the plot.
        prefix (str): The prefix for the output file name.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    html_file = f"{prefix}_{timestamp}_{plot_name}.html"
    m.write_html(html_file)
    logging.info(f"Plot saved as {html_file}")
    print(f"Plot saved as {html_file}")

def export_all_plots(df, prefix):
    """
    Export all plot types using parallel processing.

    Args:
        df (pd.DataFrame): The DataFrame to plot.
        prefix (str): The prefix for the output file names.
    """
    plot_types = ["Scatter Plot", "Heatmap", "Lines Plot", "Circle Markers", "Polygon"]
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(create_plotly_map, df, plot_type): plot_type.lower().replace(" ", "_") for plot_type in plot_types}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Exporting plots", unit=" plot"):
            plot_name = futures[future]
            try:
                m = future.result()
                export_plot(m, plot_name, prefix)
            except ValueError as e:
                logging.error(f"Error creating plot {plot_name}: {e}")

# Main function
def display_countdown(seconds):
    """
    Display a countdown timer in the console.

    Args:
        seconds (int): The number of seconds for the countdown.
    """
    print_blank_line()
    for remaining in range(seconds, 0, -1):
        print(f"\rReturning to main menu in {remaining} seconds...", end="")
        time.sleep(1)
    print("\rReturning to main menu...                     ")

def main():
    """Main function to execute the script workflow."""
    while True:
        configure_logging()
        clear_screen()
        print_header()

        try:
            kml_file = get_kml_filename()
            validate_kml_file(kml_file)
            
            df, valid_timestamp_count, invalid_timestamp_count = parse_kml(kml_file)
            
            print_blank_line()
            prefix = input("Enter a prefix for the output files (optional): ")
            print_blank_line()

            if not prefix:
                prefix = "output"

            output_file = get_output_filename(kml_file, prefix)
            save_dataframe(df, output_file)
            timestamped_output_file, timestamped_csv_file = save_dataframe_with_timestamps(df, output_file)

            # Perform and save analysis
            analysis = analyze_data(df)
            save_analysis(analysis, output_file, valid_timestamp_count, invalid_timestamp_count)
            
            start_date, end_date = get_date_range(df)
            if start_date and end_date:
                df = pd.read_feather(timestamped_output_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = filter_by_date(df, start_date, end_date)
                filtered_output_file = output_file.replace('.csv', '_filtered.csv')
                df.to_csv(filtered_output_file, index=False)
                logging.info(f"Filtered data saved as {filtered_output_file}")
                print(f"Filtered data saved as {filtered_output_file}")

            plot_types = choose_plot_types()
            
            for plot_type in plot_types:
                m = create_plotly_map(df, plot_type)
                plot_name = plot_type.lower().replace(" ", "_")
                html_file = get_html_filename(f"{prefix}_{plot_name}.html")
                export_plot(m, plot_name, prefix)
                
            # Delete the feather files if no longer needed
            if os.path.exists(output_file.replace('.csv', '.feather')):
                os.remove(output_file.replace('.csv', '.feather'))
                logging.info(f"Feather file {output_file.replace('.csv', '.feather')} deleted")
            if os.path.exists(timestamped_output_file):
                os.remove(timestamped_output_file)
                logging.info(f"Timestamped feather file {timestamped_output_file} deleted")

            # Visualize a 3-second countdown before clearing the screen
            display_countdown(3)
            clear_screen()

        except (FileNotFoundError, ValueError) as e:
            logging.error(e)
            print(e)

if __name__ == "__main__":
    main()

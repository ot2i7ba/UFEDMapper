# Copyright (c) 2024 ot2i7ba
# https://github.com/ot2i7ba/
# This code is licensed under the MIT License (see LICENSE for details).

"""
Processes a KML file to generate an interactive map using Plotly.
"""

import os
import pandas as pd
import folium
from lxml import etree
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import logging
import pytz
import numpy as np

# Configure logging
log_file = 'UFEDMapper.log'

def configure_logging():
    """Configure logging to log to both console and file."""
    if not os.path.exists(log_file):
        try:
            with open(log_file, 'w') as f:
                f.write("")
            print(f"Log file created: {log_file}")
        except IOError as e:
            print(f"Failed to create log file: {e}")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file),
                            logging.StreamHandler()
                        ])
    logging.info("Logging configured successfully")

def clear_screen():
    """Clear the screen depending on the operating system."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the header for the script."""
    print(" UFEDMapper v0.1.1 by ot2i7ba ")
    print("===============================")
    print("")

def get_kml_filename():
    """Prompt the user to input the KML filename."""
    kml_file = input("Input KML filename (enter for 'Locations.kml'): ")
    
    if not kml_file:
        kml_file = 'Locations.kml'
    elif not kml_file.endswith('.kml'):
        kml_file += '.kml'
    
    logging.info(f"KML file chosen: {kml_file}")
    return kml_file

def validate_kml_file(kml_file):
    """Validate if the file exists and is a KML file."""
    if not os.path.isfile(kml_file):
        logging.error(f"Error: The file '{kml_file}' could not be found.")
        raise FileNotFoundError(f"Error: The file '{kml_file}' could not be found.")
    if not kml_file.endswith('.kml'):
        logging.error(f"Error: The file '{kml_file}' is not a KML file.")
        raise ValueError(f"Error: The file '{kml_file}' is not a KML file.")
    logging.info(f"Validated KML file: {kml_file}")
    return kml_file

def clean_html(html_text):
    """Remove HTML tags from a string."""
    if html_text is None:
        return None
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text()

def parse_kml(file_path):
    """Parse the KML file and extract relevant data using parallel processing."""

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
        except Exception as e:
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

def filter_by_date(df, start_date, end_date):
    """Filter the DataFrame by the given date range."""
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    return df.loc[mask]

def analyze_data(df):
    """Analyze the parsed data and generate insights using numpy for performance."""
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
    """Save the analysis to an Excel file."""
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

def choose_plot_type():
    """Prompt the user to choose a plot type."""
    print()
    print("Choose a plot type:")
    plot_types = {
        "1": "Scatter Plot",
        "2": "Heatmap",
        "3": "Lines Plot",
        "4": "Circle Markers",
        "5": "Polygon",
        "6": "Arrow Lines",
        "7": "Cluster Map",
        "8": "Time Map",
        "A": "All"
    }
    for key, value in plot_types.items():
        print(f"{key}. {value}")
    
    choice = input("Enter the number of the plot type (default is 1): ")
    plot_type = plot_types.get(choice, "Scatter Plot")
    logging.info(f"Plot type chosen: {plot_type}")
    return plot_type

def add_arrow(folium_map, point1, point2):
    """Add an arrow to the map from point1 to point2."""
    folium.Marker(
        location=point2,
        icon=folium.Icon(icon='arrow-up', angle=0, prefix='fa')
    ).add_to(folium_map)

def create_heatmap(df, m):
    from folium.plugins import HeatMap
    heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]
    HeatMap(heat_data).add_to(m)

def create_cluster_map(df, m):
    from folium.plugins import MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_text = f"{row['name']}<br>{row['timestamp']}" if pd.notnull(row['timestamp']) else row['name']
        popup_text += f"<br>{row['description']}" if pd.notnull(row['description']) else ""
        for col in df.columns:
            if col not in ['name', 'longitude', 'latitude', 'timestamp', 'description']:
                popup_text += f"<br>{col}: {row[col]}"
        folium.Marker(location=[row['latitude'], row['longitude']], popup=popup_text).addTo(marker_cluster)

def create_time_map(df, m):
    from folium.plugins import TimestampedGeoJson
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    features = []
    for _, row in df.iterrows():
        if pd.notnull(row['timestamp']):
            popup_text = f"{row['name']}<br>{row['timestamp']}" if pd.notnull(row['timestamp']) else row['name']
            popup_text += f"<br>{row['description']}" if pd.notnull(row['description']) else ""
            for col in df.columns:
                if col not in ['name', 'longitude', 'latitude', 'timestamp', 'description']:
                    popup_text += f"<br>{col}: {row[col]}"
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [row['longitude'], row['latitude']],
                },
                'properties': {
                    'time': row['timestamp'].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    'style': {'color': 'red'},
                    'icon': 'circle',
                    'popup': popup_text,
                }
            }
            features.append(feature)
    TimestampedGeoJson({
        'type': 'FeatureCollection',
        'features': features,
    }, period='PT1H', add_last_point=True).add_to(m)

def create_important_places_map(df, m, important_places):
    for _, row in df.iterrows():
        popup_text = f"{row['name']}<br>{row['timestamp']}" if pd.notnull(row['timestamp']) else row['name']
        popup_text += f"<br>{row['description']}" if pd.notnull(row['description']) else ""
        for col in df.columns:
            if col not in ['name', 'longitude', 'latitude', 'timestamp', 'description']:
                popup_text += f"<br>{col}: {row[col]}"
        if row['name'] in important_places:
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup_text,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        else:
            folium.Marker(location=[row['latitude'], row['longitude']], popup=popup_text).add_to(m)

def create_folium_map(df, plot_type, important_places=None):
    """Create the appropriate plot based on the plot type selected using Folium."""
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=12)

    if plot_type == "Scatter Plot":
        for _, row in df.iterrows():
            popup_text = f"{row['name']}<br>{row['timestamp']}" if pd.notnull(row['timestamp']) else row['name']
            popup_text += f"<br>{row['description']}" if pd.notnull(row['description']) else ""
            for col in df.columns:
                if col not in ['name', 'longitude', 'latitude', 'timestamp', 'description']:
                    popup_text += f"<br>{col}: {row[col]}"
            folium.Marker(location=[row['latitude'], row['longitude']], popup=popup_text).add_to(m)
    elif plot_type == "Heatmap":
        create_heatmap(df, m)
    elif plot_type == "Lines Plot":
        points = [(row['latitude'], row['longitude']) for _, row in df.iterrows()]
        folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)
    elif plot_type == "Circle Markers":
        for _, row in df.iterrows():
            popup_text = f"{row['name']}<br>{row['timestamp']}" if pd.notnull(row['timestamp']) else row['name']
            popup_text += f"<br>{row['description']}" if pd.notnull(row['description']) else ""
            for col in df.columns:
                if col not in ['name', 'longitude', 'latitude', 'timestamp', 'description']:
                    popup_text += f"<br>{col}: {row[col]}"
            folium.CircleMarker(location=[row['latitude'], row['longitude']], radius=5, color='blue', fill=True, fill_color='blue', popup=popup_text).add_to(m)
    elif plot_type == "Polygon":
        points = [(row['latitude'], row['longitude']) for _, row in df.iterrows()]
        folium.Polygon(locations=points, color="blue", fill=True, fill_color="blue").add_to(m)
    elif plot_type == "Arrow Lines":
        points = [(row['latitude'], row['longitude']) for _, row in df.iterrows()]
        folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)
        for i in range(len(points) - 1):
            add_arrow(m, points[i], points[i + 1])
    elif plot_type == "Cluster Map":
        create_cluster_map(df, m)
    elif plot_type == "Time Map":
        create_time_map(df, m)
    elif plot_type == "Important Places" and important_places:
        create_important_places_map(df, m, important_places)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")

    logging.info(f"Map created: {plot_type}")
    return m

def create_plotly_map(df, plot_type):
    """Create the appropriate plot based on the plot type selected using Plotly."""
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

def export_plot(m, plot_name, prefix, engine):
    """Export the plot to an HTML file."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    html_file = f"{prefix}_{timestamp}_{plot_name}.html"
    
    if engine == 'folium':
        m.save(html_file)
    elif engine == 'plotly':
        m.write_html(html_file)
    
    logging.info(f"Plot saved as {html_file}")
    print(f"Plot saved as {html_file}")

def get_html_filename(default_name):
    """Prompt the user to input the output HTML filename."""
    html_file = input(f"Output html filename (enter for '{default_name}'): ")
    
    if not html_file:
        html_file = default_name
    elif not html_file.endswith('.html'):
        html_file += '.html'
    logging.info(f"HTML filename chosen: {html_file}")
    return html_file

def export_all_plots(df, prefix, important_places=None, engine='plotly'):
    """Export all plot types using parallel processing."""
    plot_types = ["Scatter Plot", "Heatmap", "Lines Plot", "Circle Markers", "Polygon"]
    with ThreadPoolExecutor() as executor:
        futures = {}
        if engine == 'folium':
            for plot_type in plot_types:
                futures[executor.submit(create_folium_map, df, plot_type, important_places)] = plot_type.lower().replace(" ", "_")
        elif engine == 'plotly':
            for plot_type in plot_types:
                futures[executor.submit(create_plotly_map, df, plot_type)] = plot_type.lower().replace(" ", "_")
        for future in tqdm(as_completed(futures), total=len(futures), desc="Exporting plots", unit=" plot"):
            plot_name = futures[future]
            try:
                m = future.result()
                export_plot(m, plot_name, prefix, engine)
            except Exception as e:
                logging.error(f"Error creating plot {plot_name}: {e}")

def get_output_filename(kml_file, prefix):
    """Generate the output filename based on the KML filename."""
    base_name = os.path.splitext(os.path.basename(kml_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = f"{prefix}_{timestamp}_{base_name}.csv"
    logging.info(f"Output CSV filename: {output_file}")
    return output_file

def save_dataframe(df, output_file):
    """Save the DataFrame to a feather file."""
    feather_file = output_file.replace('.csv', '.feather')
    df.reset_index(drop=True).to_feather(feather_file)
    logging.info(f"Data saved as {feather_file}")
    print(f"Data saved as {feather_file}")

def save_dataframe_with_timestamps(df, output_file):
    """Save the DataFrame with valid timestamps to a separate feather file."""
    timestamped_df = df.dropna(subset=['timestamp']).reset_index(drop=True)
    timestamped_output_file = output_file.replace('.csv', '_timestamps.feather')
    timestamped_df.to_feather(timestamped_output_file)
    logging.info(f"Data with timestamps saved as {timestamped_output_file}")
    print(f"Data with timestamps saved as {timestamped_output_file}")
    return timestamped_output_file

def choose_engine():
    """Prompt the user to choose the plotting engine."""
    print()
    print("Choose the plotting engine (default is Plotly):")
    print("p. Plotly")
    print("f. Folium")
    engine = input("Enter the engine (p/f): ").strip().lower()
    if engine not in ['p', 'f']:
        engine = 'p'
    logging.info(f"Engine chosen: {engine}")
    return 'plotly' if engine == 'p' else 'folium'

def get_date_range(df):
    """Prompt the user to input a date range."""
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

def main():
    """Main function to execute the script workflow."""
    configure_logging()
    clear_screen()
    print_header()

    try:
        kml_file = get_kml_filename()
        validate_kml_file(kml_file)
        
        df, valid_timestamp_count, invalid_timestamp_count = parse_kml(kml_file)
        
        prefix = input("Enter a prefix for the output files (optional): ")
        if not prefix:
            prefix = "output"

        output_file = get_output_filename(kml_file, prefix)
        save_dataframe(df, output_file)
        timestamped_output_file = save_dataframe_with_timestamps(df, output_file)

        # Perform and save analysis
        analysis = analyze_data(df)
        save_analysis(analysis, output_file, valid_timestamp_count, invalid_timestamp_count)
        
        start_date, end_date = get_date_range(df)
        if start_date and end_date:
            df = pd.read_feather(timestamped_output_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = filter_by_date(df, start_date, end_date)

        engine = choose_engine()
        plot_type = choose_plot_type()
        
        if plot_type == "All":
            important_places = ['Important Place 1', 'Important Place 2']  # Hier kannst du wichtige Orte definieren
            export_all_plots(df, prefix, important_places, engine)
        else:
            important_places = None
            if plot_type == "Important Places":
                important_places = ['Important Place 1', 'Important Place 2']  # Hier kannst du wichtige Orte definieren
            if engine == 'plotly':
                m = create_plotly_map(df, plot_type)
                plot_name = plot_type.lower().replace(" ", "_")
                html_file = get_html_filename(f"{prefix}_{plot_name}.html")
                m.write_html(html_file)
            else:
                m = create_folium_map(df, plot_type, important_places)
                plot_name = plot_type.lower().replace(" ", "_")
                html_file = get_html_filename(f"{prefix}_{plot_name}.html")
                m.save(html_file)
            
            logging.info(f"Plot saved as {html_file}")

        # Delete the feather files if no longer needed
        if os.path.exists(output_file.replace('.csv', '.feather')):
            os.remove(output_file.replace('.csv', '.feather'))
            logging.info(f"Feather file {output_file.replace('.csv', '.feather')} deleted")
        if os.path.exists(timestamped_output_file):
            os.remove(timestamped_output_file)
            logging.info(f"Timestamped feather file {timestamped_output_file} deleted")

    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        print(e)

if __name__ == "__main__":
    main()

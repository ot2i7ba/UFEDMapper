# UFEDMapper
UFEDMapper is a Python script designed to process and analyze KML files exported from Cellebrite UFED. It provides the functionality to create various types of map visualizations from the extracted data points. This script is based on **[UFEDkml2map](https://github.com/ot2i7ba/UFEDkml2map/)**, and I primarily use these scripts for professional purposes as they work well for me. I hope that by sharing this, it may help others too.

## Features
- **Logging**: Logs activities both to a file and the console.
- **KML File Input and Validation**: Prompts the user to input the KML file name and checks its existence and format.
- **Parsing KML File**: Extracts data points (Placemarks) in parallel to improve performance.
- **Data Analysis**: Analyzes the data to identify duplicates and unique points, and determines the most and least visited locations.
- **Data Storage**: Saves the data as CSV and Feather files.
- **Date Filtering**: Allows the user to filter the data by a specific date range.
- **Plot Creation**: Generates various types of map visualizations (Scatter Plot, Heatmap, Lines Plot, Circle Markers, Polygon, Cluster Map, Time Map) and saves them as HTML files.
- **Automatic Export**: Enables parallel export of all plot types.

## Requirements
- Python 3.6 or higher
   - The following Python packages:
   - pandas
   - folium
   - lxml
   - tqdm
   - logging
   - pytz
   - numpy
   - beautifulsoup4
   - plotly
   - feather-format

## Installation
1. **Clone the repository**:

   ```sh
   git clone https://github.com/your-username/UFEDMapper.git
   cd UFEDMapper
   ```

2. **Install the required packages**:

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the script**:
   ```sh
   python UFEDMapper.py
   ```

4. **Follow the Prompts**:
- **KML File**: The script will prompt you to enter the name of the KML file to be processed. If you press Enter without providing a name, it will default to Locations.kml.
- **Output Prefix**: Enter a prefix for the output files. If you press Enter without providing a prefix, it will default to output.
- **Date Range**: You will be prompted to enter a start and end date to filter the data. If you do not provide dates, all data will be used.
- **Plotting Engine**: Choose the plotting engine - Plotly (default) or Folium.
- **Plot Type**: Select the type of plot you wish to create. You can choose a specific plot type or generate all available plots.

### Plot Types
The user can choose between the Plotly and Folium plotting libraries. The following plot types are available:
- Scatter Plot
- Heatmap
- Lines Plot
- Circle Markers
- Polygon
- Cluster Map
- Time Map

## Example
```
Choose a plot type:
1. Scatter Plot
2. Heatmap
3. Lines Plot
4. Circle Markers
5. Polygon
6. Arrow Lines
7. Cluster Map
8. Time Map
A. All
Enter the number of the plot type (default is 1): 1
```

### Important Places
You can define important places in the script that will be highlighted in the visualizations. These places should match the names of the locations in your KML file exactly. For example, if your KML file contains the following locations:

- "Home"
- "Office"
- "Gym"
- "Supermarket"

And you want to highlight "Home" and "Office", you would configure the important places as follows:

   ```python
   important_places = ['Home', 'Office']
   ```

## Logging
The log file UFEDMapper.log will be created in the same directory as the script.

## License
This project is licensed under the **[MIT license](https://github.com/ot2i7ba/UFEDMapper/blob/main/LICENSE)**, providing users with flexibility and freedom to use and modify the software according to their needs.

## Disclaimer
This project is provided without warranties. Users are advised to review the accompanying license for more information on the terms of use and limitations of liability.


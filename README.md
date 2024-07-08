# UFEDMapper
UFEDMapper is a Python script designed to process and analyze KML files exported from Cellebrite UFED. It provides the functionality to create various types of map visualizations from the extracted data points. This script is based on **[UFEDkml2map](https://github.com/ot2i7ba/UFEDkml2map/)**, and I primarily use these scripts for professional purposes as they work well for me. I hope that by sharing this, it may help others too.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [PyInstaller](#pyinstaller)
- [Releases](#releases)
- [Example](#example)
- [Changes](#changes)
- [License](#license)

# Features
- Logging: Logs activities both to a file and the console.
- Parse KML files and extract data points.
- Generate various types of interactive maps:
   - Scatter Plot
   - Heatmap
   - Lines Plot
   - Circle Markers
   - Polygon
- Filter data points by date range.
- Save analysis results and maps in various formats (CSV, Excel, HTML).
- Enhanced user interaction and error handling.

# Requirements
- Python 3.6 or higher
   - The following Python packages:
   - pandas==1.3.3
   - lxml==4.6.3
   - tqdm==4.62.3
   - pytz==2021.3
   - numpy==1.21.2
   - plotly==5.3.1
   - beautifulsoup4==4.10.0

# Installation
1. **Clone the repository**:

   ```sh
   git clone https://github.com/ot2i7ba/UFEDMapper.git
   cd UFEDMapper
   ```

2. **To install the required dependencies, use the following command:**:

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the script**:
   ```sh
   python UFEDMapper.py
   ```

# Usage
1. Place your KML file in the same directory as the script.
2. Run the script:
   ```bash
   python UFEDMapper.py
   ```
3. Follow the prompts to select a KML file, choose plot types, and enter optional filters.

## Follow the Prompts
- **KML File Selection**: The script will search the directory for KML files and present a numbered list for selection.
- **Prefix for Output Files**: Enter a prefix for the output files (optional).
- **Date Range Filtering**: Optionally filter data points by entering a date range.
- **Plot Types**: Choose one or more plot types for visualization.

## Plot Types
The user can choose between the Plotly and Folium plotting libraries. The following plot types are available:
- **Scatter Plot**: Visualize data points on a map.
- **Heatmap**: Show density of data points.
- **Lines Plot**: Connect data points with lines.
- **Circle Markers**: Visualize data points with circle markers.
- **Polygon**: Draw polygons connecting data points.

# PyInstaller
To compile the UFEDMapper script into a standalone executable, you can use PyInstaller. Follow the steps below:

1. Install PyInstaller (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. Compile the script using the following command:
   ```bash
   pyinstaller --onefile --name UFEDMapper --icon=ufedmapper.ico --hidden-import pyarrow --hidden-import pyarrow.vendored.version UFEDMapper.py
   ```

- `--onefile`: Create a single executable file.
- `--name UFEDMapper`: Name the executable UFEDMapper.
- `--icon=myicon.ico`: Use myicon.ico as the icon for the executable.
- `--hidden-import pyarrow`: Ensure that the pyarrow module is included.
- `--hidden-import pyarrow.vendored.version`: Ensure that the pyarrow.vendored.version module is included.

3. Find the executable in the dist directory.

## Using UFEDMapper.spec
Alternatively, you can use the provided UFEDMapper.spec file to compile the script.

1. Compile the script using the spec file:
   ```bash
   pyinstaller UFEDMapper.spec
   ```

2. Find the executable in the dist directory.

**Running the executable**: After compilation, you can run the executable found in the dist directory.

## Releases
A compiled and 7zip-packed version of UFEDMapper for Windows is available as a release. You can download it from the **[Releases](https://github.com/ot2i7ba/UFEDMapper/releases)** section on GitHub. This version includes all necessary dependencies and can be run without requiring Python to be installed on your system.

# Example

## The script lists available KML files and prompts for selection:
```
Available KML files:
1. Example.kml
2. Locations.kml
e. Exit
Enter the number of the desired KML file (Enter to use 'Locations.kml' or 'e' to exit):
```

## After selecting a file, the script prompts for a prefix for the output files:
```
Enter a prefix for the output files (optional):
```

## Optionally filter data by date range:
```
Enter start date (DD.MM.YYYY) or press Enter to skip:
Enter end date (DD.MM.YYYY) or press Enter to skip:
```

## Choose one or more plot types for visualization:
```
Choose one or more plot types (e.g., 1,2,5):
1. Scatter Plot
2. Heatmap
3. Lines Plot
4. Circle Markers
5. Polygon
```

# Logging
The log file UFEDMapper.log will be created in the same directory as the script.

___

# Changes

## Changes in 0.1.3
- Import Optimization: 
   - Imports have been reordered according to best practices.
- Exit Handling: 
   - sys.exit(0) is now used to properly exit the script.
- Version Update: 
   - The version in the header has been updated to 0.1.3.

## Changes in 0.1.2
- Refactored Code Structure:
   - Grouped functions thematically: configuration, user interaction, file operations, data analysis, and plotting.
   - Improved readability and maintainability.

- Constants and Global Variables:
   - Introduced global constants (LOG_FILE, DEFAULT_KML_FILE) to avoid magic strings and hard-coded values.

- Enhanced User Interaction:
   - Added functionality to search for KML files in the script directory and present a numbered list for selection.
   - Implemented an exit option for easier script termination.

- Documentation and Comments:
   - Added comprehensive docstrings to all functions.
   - Included additional comments for better understanding and readability.

- Countdown Display:
   - Implemented a 3-second countdown display before clearing the screen and returning to the main menu.

- Improved Error Handling and Logging:
   - Enhanced error handling with more detailed logging.

- Functional Enhancements:
   - Added new functions and optimized existing ones for better performance and user experience.

## Changes in 0.1.1
- Initial release.

___

# License
This project is licensed under the **[MIT license](https://github.com/ot2i7ba/UFEDMapper/blob/main/LICENSE)**, providing users with flexibility and freedom to use and modify the software according to their needs.

# Contributing
Contributions are welcome! Please fork the repository and submit a pull request for review.

# Disclaimer
This project is provided without warranties. Users are advised to review the accompanying license for more information on the terms of use and limitations of liability.
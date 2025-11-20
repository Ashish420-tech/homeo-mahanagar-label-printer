# Homeopathy Name Search App

## Overview
The Homeopathy Name Search App is a Kivy-based desktop and mobile application designed to help users search for homeopathic remedy names. The application utilizes data from an Excel file containing remedy names in both Latin and Common formats.

## Features
- Search for homeopathic remedies using either Latin or Common names.
- Fuzzy matching support for multi-word queries.
- User-friendly interface built with Kivy.
- Data loaded from `remedies.xlsx` using pandas and openpyxl.

## File Structure
```
homeopathy-name-search-app
├── homeopathy_name_search_app.py  # Main application file
├── remedies.xlsx                  # Data source for remedy names
├── requirements.txt               # List of dependencies
├── buildozer.spec                 # Configuration for Android packaging
├── .gitignore                     # Files to ignore in Git
└── README.md                      # Documentation for the project
```

## Setup Instructions
1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd homeopathy-name-search-app
   ```

2. **Install dependencies:**
   Ensure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **Run the application:**
   Execute the following command in your terminal:
   ```
   python homeopathy_name_search_app.py
   ```

## Requirements
- Python 3.x
- Kivy
- pandas
- openpyxl

## Data Format
The `remedies.xlsx` file must contain the following columns:
- **Latin**: The Latin name of the remedy.
- **Common**: The common name of the remedy.

Both headers are case-insensitive.

## Android Packaging
To package the application for Android, use Buildozer. Ensure you have the necessary environment set up and run:
```
buildozer -v android debug
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
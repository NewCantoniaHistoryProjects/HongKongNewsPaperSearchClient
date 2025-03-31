# HongKongNewsPaperSearchClient
Search Client for Hong Kong newspaper in archive.org

This project is a desktop application for searching historical newspaper titles stored in text files. It processes newspaper data into a SQLite database and provides a graphical user interface (GUI) for searching titles based on keywords, date ranges, and newspaper types.

## Features

- **Data Processing**: Scans a directory of text files and stores newspaper metadata in a SQLite database.
- **Search Functionality**:
  - Keyword search with fuzzy matching (e.g., "bandit" matches "banditsdadx") or exact matching (using quotes, e.g., `"bandit"`).
  - Date range filtering with year and month dropdowns, limited to the data's range.
  - Newspaper selection with checkboxes, including "Select All" and "Invert Selection" options.
  - Clear buttons for resetting start and end dates.
  - Sort results by date (ascending or descending).
- **User Interface**: Built with `tkinter`, featuring a simple and intuitive design.
- **URL Access**: Double-click search results to open the corresponding archive.org page in a browser.
- **Keyboard Support**: Press Enter in the search field to trigger a search.

## Project Structure

- `scan_newspapers_to_sqlite.py`: Processes text files and generates the SQLite database (`newspapers.db`).
- `newspaper_search_client.py`: Launches the GUI client for searching the database.

## Prerequisites

- Python 3.6 or higher
- SQLite (included with Python, no separate installation needed)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd newspaper-search-tool
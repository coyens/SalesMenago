# SALESmanago Contact Data Processor

This Python script automates the process of retrieving contact data from the SALESmanago API, mapping contact tags to user preferences using Excel files, and exporting the results to timestamped JSON files.

## 📌 Features

- Fetches newly created and modified contacts from the SALESmanago API.
- Retrieves full contact details by ID.
- Maps contact tags to user preferences using Excel-based mappings.
- Generates structured JSON files for further processing or integration.
- Adds timestamps to output filenames to prevent overwriting.

## 🛠 Requirements

- Python 3.8+
- pandas
- requests
- openpyxl

## 📦 Installation

Install the required libraries using pip:

```bash
pip install pandas requests openpyxl

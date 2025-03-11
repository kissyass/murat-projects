# Google Contacts Clone

This Python-based program is designed to streamline and enhance your contact management process. Inspired by Google Contacts, it allows you to upload CSV or Excel files, map your data columns to the required fields, filter contacts, and export the refined data in your desired format.

## Features

### File Upload
- **Supported Formats:** CSV and Excel files.

### Column Mapping
- **Name:** Map up to three columns (e.g., business, first name, last name). The program concatenates the values with spaces.
- **Phone Number:** Map a column for phone numbers. The program automatically checks and converts numbers to international format (adding a '+' sign).
- **Email:** Map the email column.
- **Data Source & Tags:** 
  - You can either map these columns from your file or specify default values that will be applied to all records.

### Data Filtering
- **Value-based Filtering:** Filter contacts by specific column values.
- **Non-Empty Filtering:** Filter based on whether certain columns have data.

### Output Options
- **Export Formats:** Save the processed contacts as CSV or Excel files.
- **Customizable Columns:** Choose which columns to include in the output file, allowing you to exclude unnecessary data.
- **Additional Data:** A new column for "Country" is automatically added based on the international phone number validation.

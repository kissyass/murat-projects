# Facebook Groups Report Generator

This Python program automates the generation of detailed reports on Facebook groups. It uses Selenium to log into your Facebook account and processes an Excel file containing group links. For each group, the program retrieves key information such as the group name, privacy status (public or private), and member count. The results are then displayed in a table and can be downloaded as an Excel file.

## Features

- **Facebook Login:** Securely log into your Facebook account using your phone/email and password.
- **Excel Upload:** Easily upload an Excel file that contains links to Facebook groups.
- **Automated Data Retrieval:** Utilizes Selenium to navigate to each group link and extract:
  - **Group Name**
  - **Privacy Status:** Whether the group is public or private.
  - **Member Count**
- **Report Generation:** Displays the retrieved data in a user-friendly table format.
- **Excel Export:** Download the final report as an Excel file for further analysis.

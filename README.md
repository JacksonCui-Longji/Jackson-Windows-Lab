# Jackson-Windows-Lab
Developer tools for Windows platform.

## Overview
This repository provides a set of practical utilities designed to simplify development workflows related to CAN bus and code generation on Windows.

## Tools
### dbc2code
- Input: Standard DBC file
- Output: C language header files and corresponding interface function code
- Function: Parse CAN database definitions and automatically generate reusable code structures

### excel2dbc
- Input: Excel file following the provided example format
- Output: Standard DBC file
- Function: Convert CAN signal/message definitions organized in spreadsheets into industry-standard DBC format

## Important Notes
- As official OEM DBC or Excel sample files are not included in this repository, you may need to modify the Jinja2 (J2) template files to adapt to your specific definition rules and output requirements.
- Please refer to the example files in the `input/` directory for the required input format.

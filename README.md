# Wix Subscription Manager

A Python utility for managing Wix subscription data and syncing it to Google Sheets.

## Features

- Retrieves active subscription orders from Wix API
- Filters active subscription orders
- Fetches customer contact information
- Formats and uploads data to Google Sheets
- Highlights subscriptions with end dates for easy tracking

## Requirements

- Python 3.6+
- `requests`
- `gspread`
- `google-auth`

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wix-subscription-manager.git
cd wix-subscription-manager

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Create a service account in Google Cloud Console and download the credentials JSON file
2. Share your Google Sheet with the service account email
3. Update the configuration variables in `config.py`:
   - `API_KEY`: Your Wix API key
   - `SITE_ID`: Your Wix site ID
   - `SHEET_ID`: Your Google Sheet ID
   - `CREDENTIALS_PATH`: Path to your Google service account credentials

## Usage

```bash
python wix_subs.py
```

The script will:
1. Connect to the Wix API
2. Retrieve and filter active subscription orders
3. Get contact information for each subscriber
4. Format and upload data to the specified Google Sheet
5. Apply formatting to highlight relevant information

## Logging

The script logs operations to the console with the following levels:
- INFO: Normal operation logs
- WARNING: Non-critical issues
- ERROR: Operation failures

## License

[MIT License](LICENSE)

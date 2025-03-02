import requests
import gspread
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from config import API_KEY, SITE_ID, SHEET_ID, WORKSHEET_ID, CREDENTIALS_PATH

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class WixSubscriptionManager:
    def __init__(self, api_key: str, site_id: str):
        self.headers = {
            "Authorization": api_key,
            "wix-site-id": site_id,
            "Content-Type": "application/json"
        }
        
    def get_purchased_plans(self):
        """Get active orders with 'online' in plan name"""
        endpoint = "https://www.wixapis.com/pricing-plans/v2/orders"
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get Wix orders: {response.status_code}")
            return []
            
        all_orders = response.json().get('orders', [])
        logger.info(f"Retrieved {len(all_orders)} total orders from Wix")
        
        # Filter only active orders that contain 'online' in the plan name
        filtered_orders = [
            order for order in all_orders 
            if 'online' in order.get('planName', '').lower() and
            order.get('status', '').lower() == 'active'
        ]
        
        logger.info(f"Filtered to {len(filtered_orders)} active online plans")
        return filtered_orders

    def get_contact_info(self, contact_id: str):
        """Get contact information including email and name"""
        if not contact_id:
            return {'name': '', 'email': ''}
            
        try:
            response = requests.get(
                f"https://www.wixapis.com/contacts/v4/contacts/{contact_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"API error getting contact: {response.status_code}")
                return {'name': '', 'email': ''}
                
            contact_data = response.json()
            contact = contact_data.get('contact', {})
            
            # Get name information
            info = contact.get('info', {})
            first_name = info.get('name', {}).get('first', '')
            last_name = info.get('name', {}).get('last', '')
            name = f"{first_name} {last_name}".strip()
            
            # Get email from primaryEmail
            email = contact.get('primaryEmail', {}).get('email', '')
            
            return {'name': name, 'email': email}
            
        except Exception as e:
            logger.error(f"Error getting contact info: {e}")
            return {'name': '', 'email': ''}

def format_date(date_str):
    """Format ISO date string to DD/MM/YYYY format"""
    if not date_str:
        return ''
    
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return date_str

def upload_to_sheets(orders, sheet_id: str, worksheet_id: int, credentials_path: str, manager: WixSubscriptionManager):
    """Upload filtered orders to Google Sheets"""
    # Set up Google Sheets connection
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(sheet_id).get_worksheet_by_id(worksheet_id)
    
    # Prepare data for sheet
    headers = ['Order ID', 'Status', 'Plan Name', 'Customer Name', 'Email', 'Start Date', 'End Date', 'Price']
    all_values = [headers]
    rows_with_end_dates = []  # Track which rows have active status with end date

    # Process each order
    for order in orders:
        contact_id = order.get('buyer', {}).get('contactId', '')
        contact_info = manager.get_contact_info(contact_id)
        
        # Format dates
        start_date = format_date(order.get('startDate', ''))
        end_date = format_date(order.get('endDate', ''))
        
        # Get price information
        pricing = order.get('pricing', {})
        prices = pricing.get('prices', [{}])
        price_info = prices[0].get('price', {}) if prices else {}
        total = price_info.get('total', '')
        currency = price_info.get('currency', '')
        price_display = f"{total} {currency}" if total else ""
        
        status = order.get('status', '')
        
        # Add row data
        row = [
            order.get('id', ''),
            status,
            order.get('planName', ''),
            contact_info.get('name', ''),
            contact_info.get('email', ''),
            start_date,
            end_date,
            price_display
        ]
        
        all_values.append(row)
        
        # Check if this is an active order with end date
        if status.lower() == 'active' and end_date:
            # +1 for header row, +1 because we just added this row
            row_index = len(all_values)  # This is now the index of the row we just added
            rows_with_end_dates.append(row_index)

    # Update the worksheet
    worksheet.clear()
    worksheet.update(values=all_values)
    
    # Format header row
    worksheet.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}})
    
    # Highlight rows with end dates in light yellow for active subscriptions
    for row_index in rows_with_end_dates:
        worksheet.format(f'A{row_index}:H{row_index}', {
            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}  # Light yellow
        })
    
    logger.info(f"Updated sheet with {len(all_values)-1} orders, highlighted {len(rows_with_end_dates)} rows")

def main():
    logger.info("Starting WIX subscription data sync")
    
    try:
        # Initialize API client and get orders
        manager = WixSubscriptionManager(API_KEY, SITE_ID)
        orders = manager.get_purchased_plans()
        
        if orders:
            upload_to_sheets(orders, SHEET_ID, WORKSHEET_ID, CREDENTIALS_PATH, manager)
        else:
            logger.warning("No active online plans found")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    
    logger.info("WIX subscription data sync completed")

if __name__ == "__main__":
    main()
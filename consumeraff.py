import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime

# Database connection details
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'consumer_affairs'
}

def create_database_if_not_exists():
    connection = None
    cursor = None
    try:
        connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS consumer_affairs")
        connection.commit()
    except pymysql.MySQLError as err:
        print(f'Error: {err}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Function to truncate table
def truncate_table(cursor):
    try:
        cursor.execute("TRUNCATE TABLE consumer_affairs")
        print("Table truncated successfully")
    except pymysql.MySQLError as err:
        print(f'Error truncating table: {err}')

# Create the database if it does not exist
create_database_if_not_exists()

# URL of the webpage you want to scrape
url = 'https://consumeraffairs.nic.in/about-us/whos-who'

response = requests.get(url)
if response.status_code == 200:
    # Load the webpage content into BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all td elements with the specified classes and extract their text
    room_nos = [td.text.strip() for td in soup.select('td.views-field.views-field-field-room-no')]
    titles = [td.text.strip() for td in soup.select('td.views-field.views-field-title')]
    column_titles = [td.text.strip() for td in soup.select('td.views-field.views-field-field-column-title')]
    phone_numbers = [td.text.strip() for td in soup.select('td.views-field.views-field-php')]
    email_addresses = [td.text.strip() for td in soup.select('td.views-field.views-field-field-email-address')]
    
    # Ensure all lists are of the same length by padding the shorter lists with None
    max_length = max(len(room_nos), len(titles), len(column_titles), len(phone_numbers), len(email_addresses))
    while len(room_nos) < max_length: room_nos.append(None)
    while len(titles) < max_length: titles.append(None)
    while len(column_titles) < max_length: column_titles.append(None)
    while len(phone_numbers) < max_length: phone_numbers.append(None)
    while len(email_addresses) < max_length: email_addresses.append(None)

    # Create a list of dictionaries to represent the rows in the database
    data = [
        {
            'Room_no': room_nos[i],
            'Name': titles[i],
            'Designation': column_titles[i],
            'phone_number': phone_numbers[i],
            'email_address': email_addresses[i],
            'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        for i in range(max_length)
    ]

    # Insert data into the MySQL database
    connection = None
    cursor = None
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Truncate table before inserting new data
        truncate_table(cursor)

        # Insert data into the table
        for row in data:
            cursor.execute("""
            INSERT INTO consumer_affairs (Room_no, Name, Designation, phone_number, email_address, scraped_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['Room_no'], row['Name'], row['Designation'], row['phone_number'], row['email_address'], row['scraped_date']))

        # Commit the transaction
        connection.commit()
        print('Data has been saved to the database')

    except pymysql.MySQLError as err:
        print(f'Error: {err}')
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
else:
    print(f'Failed to retrieve the webpage. Status code: {response.status_code}')

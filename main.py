

import csv
import requests
from bs4 import BeautifulSoup

# The goal of the code is to fetch all the video links from the YouTube channel specified in base_url, and write them to a CSV file named listed_001.csv.

# Set the base URL for the YouTube channel
base_url = 'https://www.youtube.com/c/OpeninApp'


# ENTER YOUR URL in base_URL



# Open a CSV file for writing
with open('listed_001.csv', 'w') as csvfile:
    # Create a CSV writer object

    # This line opens a file named listed_001.csv in write mode and creates a file object named csvfile. The with statement ensures that the file is properly closed after the block of code inside the with statement is executed.

    writer = csv.writer(csvfile) 

    # This line creates a CSV writer object named writer, which is used to write data to the CSV file.



    # Write the header row
    writer.writerow(['URL'])

    # This line writes a single row to the CSV file with a single column header, which is "URL".



    # Loop through the first 10 pages of search results 
    for page_num in range(1, 10000):
        # Set the URL for the current page of search results
        url = f'{base_url}?page={page_num}'

        # Connect to the website and fetch the page
        page = requests.get(url)

        # This line uses the requests module to connect to the website and fetch the HTML content of the current page of search results.

        # Parse the HTML content
        soup = BeautifulSoup(page.content, 'html.parser')\
        
        # This line uses the beautifulsoup module to parse the HTML content of the current page of search results and create a BeautifulSoup object named soup.

        # Find all the video links on the page
        videos = soup.find_all('a', href=True)

        # This line uses the find_all method of the soup object to find all the <a> tags on the page that have an href attribute.



        # Loop through the videos and write their URLs to the CSV file
        for video in videos:
            writer.writerow([video['href']])

    # This for loop iterates through each video link found on the page, and writes its URL to the CSV file using the writerow method of the writer object.
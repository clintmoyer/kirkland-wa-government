"""
    Copyright 2024 Clint Moyer

    This file is part of kirkland-wa-government.

    kirkland-wa-government is free software: you can redistribute it and/or modify it under the terms
    of the GNU General Public License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    kirkland-wa-government is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with kirkland-wa-government.
    If not, see <https://www.gnu.org/licenses/>.
"""
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.codepublishing.com/WA/Kirkland/html/"
START_PAGE = "Kirkland01/Kirkland01.html"

# Global variables
markdown_content = "# Kirkland Municipal Code\n\n"
toc = "## Table of Contents\n\n"

# Create a new session and force the Connection to close after each request
session = requests.Session()

# Helper function to create a valid markdown link
def create_markdown_link(text, link):
    return f"[{text}](#{link})"

# Helper function to clean the id for Markdown links (GitHub compatible)
def clean_id(text):
    return text.lower().replace('.', '').replace(' ', '-').replace('*', '').replace('—', '')

# Function to process a single chapter page
def process_page(url):
    global markdown_content, toc

    # Log the page being processed
    logging.info(f"Processing page: {BASE_URL + url}")

    try:
        # Fetch the page content with Connection: close to disable connection pooling
        response = session.get(BASE_URL + url, headers={"Connection": "close"})
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract Title (found in h1 with class 'Title')
        title_header = soup.find('h1', class_='Title')
        if title_header:
            # Handle the <br> by joining the text with a space
            title_text = title_header.get_text(" ", strip=True).rstrip('*')  # Replaces <br> with a space
            title_text = title_text.replace("Title", "Title ")  # Ensure spacing between "Title" and number
            markdown_content += f"## {title_text}\n\n"
            title_id = clean_id(title_text)
            toc += f"- {create_markdown_link(title_text, title_id)}\n"

            # Log the title being processed
            logging.info(f"Found title: {title_text}")

        # Extract Chapter (found in h2 with class 'CH')
        chapter_header = soup.find('h2', class_='CH')
        if chapter_header:
            # Handle the <br> by joining the text with a space
            chapter_text = chapter_header.get_text(" ", strip=True).rstrip('*')  # Replaces <br> with a space
            chapter_text = chapter_text.replace("Chapter", "Chapter ")  # Ensure spacing between "Chapter" and number
            markdown_content += f"### {chapter_text}\n\n"
            chapter_id = clean_id(chapter_text)
            toc += f"  - {create_markdown_link(chapter_text, chapter_id)}\n"

            # Log the chapter being processed
            logging.info(f"Found chapter: {chapter_text}")

            # Extract Sections
            sections = soup.find_all('h3', class_='Cite')
            for section in sections:
                section_text = section.text.strip()
                section_id = clean_id(section_text)
                markdown_content += f"#### {section_text}\n\n"
                markdown_content += section.find_next('p', class_='P1').text.strip() + "\n\n"

                # Log the section being processed
                logging.info(f"Added section: {section_text}")

        # Find the next page link using the 'next.gif' image
        next_page_link = soup.find('img', {'src': '../images/next.gif'})
        if next_page_link:
            next_page_url = next_page_link.find_parent('a')['href'].replace('../', '')

            # Log the next page being followed
            logging.info(f"Following next page: {next_page_url}")
            process_page(next_page_url)
        else:
            logging.info(f"No next page found. Crawling finished for this section.")

    except requests.RequestException as e:
        # Log the failure
        logging.error(f"Failed to retrieve {url}: {e}")
    except Exception as e:
        logging.error(f"An error occurred while processing {url}: {e}")

# Start the process with the first page (Title 1)
logging.info("Starting the crawl from the first page.")
process_page(START_PAGE)

# Write the Table of Contents to the markdown document
markdown_content = toc + "\n" + markdown_content

# Save to a markdown file
markdown_filename = "municipal.md"
try:
    with open(markdown_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    logging.info(f"Markdown file '{markdown_filename}' successfully generated.")
except Exception as e:
    logging.error(f"Error writing the markdown file: {e}")

logging.info("Crawling completed. Check the logs for details.")
print("Crawling completed. Check the logs for details.")


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
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.codepublishing.com/WA/Kirkland/html/"
START_PAGE = "KirklandZ01/KirklandZ01.html"

# Global variables
toc = "## Table of Contents\n\n"  # Placeholder for the Table of Contents
markdown_content = ""  # Content will be appended to this later

# Create a new session and force the Connection to close after each request
session = requests.Session()

# Helper function to create a valid markdown link
def create_markdown_link(text, link):
    return f"[{text}](#{link})"

# Helper function to clean the id for Markdown links (GitHub compatible)
def clean_id(text):
    # 1. Convert to lowercase
    text = text.lower()

    # 2. Replace spaces with hyphens
    text = text.replace(' ', '-')

    # 3. Remove punctuation and other non-alphanumeric characters (except hyphens)
    text = re.sub(r'[^a-z0-9-]', '', text)

    # 4. Remove leading and trailing hyphens
    text = text.strip('-')

    return text

# Function to process a single chapter page
def process_page(url):
    global markdown_content, toc

    # Log the page being processed
    logging.info(f"Processing page: {BASE_URL + url}")

    try:
        # Fetch the page content
        response = session.get(BASE_URL + url, headers={"Connection": "close"})
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract Chapter (found in h1 with class 'Title')
        chapter_header = soup.find('h1', class_='Title')
        if chapter_header:
            # Handle the <br> by joining the text with a space
            chapter_text = chapter_header.get_text(" ", strip=True).rstrip('*')  # Replaces <br> with a space
            markdown_content += f"## {chapter_text}\n\n"
            chapter_id = clean_id(chapter_text)
            toc += f"- {create_markdown_link(chapter_text, chapter_id)}\n"

            # Log the chapter being processed
            logging.info(f"Found chapter: {chapter_text}")

            # Extract Sections (handle both normal and table sections)
            sections = soup.find_all(['h3', 'p'], class_=['Cite', 'CL1table2'])  # Cover both headers and table headers
            for section in sections:
                section_text = section.text.strip()
                section_id = clean_id(section_text)
                markdown_content += f"### {section_text}\n\n"

                # Extract all paragraph content following the section
                next_elements = section.find_all_next('p')
                for elem in next_elements:
                    paragraph_text = elem.get_text(strip=True)
                    if paragraph_text:
                        markdown_content += paragraph_text + "\n\n"

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

# Start the process with the first page (Chapter 1)
logging.info("Starting the crawl from the first page.")
process_page(START_PAGE)

# Combine the TOC and the content in the correct order
full_markdown = "# Kirkland Zoning Code\n\n" + toc + "\n" + markdown_content

# Save to a markdown file
markdown_filename = "Kirkland_Zoning_Code.md"
try:
    with open(markdown_filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    logging.info(f"Markdown file '{markdown_filename}' successfully generated.")
except Exception as e:
    logging.error(f"Error writing the markdown file: {e}")

logging.info("Crawling completed. Check the logs for details.")
print("Crawling completed. Check the logs for details.")


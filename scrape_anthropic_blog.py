import sys
import click
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from lxml import etree
import copy
import os

def parse_date(date_text):
    """
    Parse timestamp from date text like 'Sep 29, 2025'.
    Returns a timezone-aware datetime object.
    """
    if not date_text:
        # Default to current UTC time if no date provided
        return datetime.now(timezone.utc)

    try:
        # Parse the string and make it timezone-aware (assuming UTC at noon)
        date_text = date_text.strip()
        dt_naive = datetime.strptime(date_text, "%b %d, %Y")
        # Set to noon UTC for consistency
        dt_aware = dt_naive.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
        return dt_aware
    except ValueError:
        # Default to current UTC time if unable to parse
        print(f"Warning: Could not parse date '{date_text}'. Defaulting to now.", file=sys.stderr)
        return datetime.now(timezone.utc)


def create_base_feed_and_entries(soup, base_url):
    """
    Parses HTML, creates the base Atom feed structure, and extracts entry data.
    Returns the base feed element (without entries) and a list of tuples:
    [(datetime_updated, entry_element)].
    """
    # Create the root element for the feed
    feed = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")

    # Add feed metadata
    ET.SubElement(feed, "title").text = "Anthropic Engineering Blog"
    ET.SubElement(feed, "id").text = base_url
    author = ET.SubElement(feed, "author")
    ET.SubElement(author, "name").text = "Anthropic"
    ET.SubElement(feed, "link", href=base_url, rel="self")
    # Add a general updated time for the feed itself (last checked time)
    ET.SubElement(feed, "updated").text = datetime.now(timezone.utc).isoformat()

    # Find all article items
    articles = soup.find_all("article", class_="ArticleList_article__LIMds")
    entries_data = []

    for article in articles:
        entry = ET.Element("entry")

        # Get the article title (could be h2 or h3)
        title_elem = article.find(["h2", "h3"], class_="bold")
        title = title_elem.text.strip() if title_elem else "Unknown Article"
        ET.SubElement(entry, "title").text = title

        # Get the article URL
        link_elem = article.find("a", class_="ArticleList_cardLink__VWIzl")
        href = link_elem["href"] if link_elem and link_elem.get("href") else ""
        article_url = urljoin(base_url, href)
        ET.SubElement(entry, "id").text = article_url
        ET.SubElement(entry, "link", href=article_url)

        # Get the article summary (may not exist for all articles)
        summary_elem = article.find("p", class_="ArticleList_summary__G96cV")
        summary = summary_elem.text.strip() if summary_elem else ""
        if summary:
            ET.SubElement(entry, "summary").text = summary

        # Get the date
        date_elem = article.find("div", class_="ArticleList_date__2VTRg")
        date_text = date_elem.text.strip() if date_elem else None

        # Parse timestamp into a datetime object for sorting
        updated_dt = parse_date(date_text)
        # Format the datetime object into ISO format string for the XML element
        ET.SubElement(entry, "updated").text = updated_dt.isoformat()

        # Get the image as additional metadata
        img_elem = article.find("img")
        if img_elem and img_elem.get("src"):
            img_url = img_elem.get("src")
            img_alt = img_elem.get("alt", "")
            # Add image info to content
            content = ""
            if summary:
                content = f"<p>{summary}</p>"
            content += f'<p><img src="{img_url}" alt="{img_alt}" /></p>'
            ET.SubElement(entry, "content", type="html").text = content
        elif summary:
            # Just include summary if no image
            ET.SubElement(entry, "content", type="html").text = f"<p>{summary}</p>"

        # Store the datetime object and the entry element for sorting
        entries_data.append((updated_dt, entry))

    return feed, entries_data


def save_atom_feed(filename, base_feed_element, entries_data):
    """
    Adds entries to a copy of the base feed element, serializes,
    and saves the Atom feed to a file.

    Args:
        filename (str): The path to save the file.
        base_feed_element (ET.Element): The basic <feed> structure.
        entries_data (list): A list of (datetime_obj, entry_element) tuples.
                             Assumed to be sorted if order matters.
    """
    # Create a deep copy to avoid modifying the original base element
    feed_copy = copy.deepcopy(base_feed_element)

    # Add entry elements to the copied feed
    for _, entry_element in entries_data:
        feed_copy.append(entry_element)

    # Convert ElementTree element to bytes, then parse with lxml for pretty printing
    xml_string_bytes = ET.tostring(feed_copy, encoding="utf-8")
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        root = etree.fromstring(xml_string_bytes, parser)
        pretty_xml_string = etree.tostring(root, encoding="unicode", pretty_print=True)
    except Exception as e:
        print(f"Error pretty-printing XML for {filename}: {e}", file=sys.stderr)
        # Fallback to non-pretty printing if lxml fails
        pretty_xml_string = xml_string_bytes.decode('utf-8')


    # Write the output to the specified file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(pretty_xml_string)
        print(f"Successfully saved feed to {filename}")
    except IOError as e:
        print(f"Error writing file {filename}: {e}", file=sys.stderr)


@click.command()
@click.argument("url")
def html_to_atom(url):
    """
    Fetches HTML from a URL, converts it to an Atom feed,
    and saves two files: 'atom.xml' (all items) and
    'atom-recent-20.xml' (most recent 20 items).

    URL: The web page URL (or file://path/to/file.html) to convert.
    """
    output_full_filename = "atom.xml"
    output_recent_filename = "atom-recent-20.xml"

    try:
        # Determine if URL is a local file path
        if url.startswith("file://"):
            filepath = url[7:]
            # Ensure file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Local file not found: {filepath}")
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            # Use the Anthropic engineering URL as the base
            base_url = "https://www.anthropic.com/engineering"
        else:
            # Fetch the HTML content via HTTP/S
            headers = {'User-Agent': 'AtomFeedGenerator/1.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html_content = response.text
            base_url = url

        # Parse the HTML
        soup = BeautifulSoup(html_content, "lxml")

        # Create the base feed structure and extract entries with timestamps
        base_feed_element, entries_data = create_base_feed_and_entries(soup, base_url)

        # Sort entries by updated timestamp, most recent first
        entries_data.sort(key=lambda item: item[0], reverse=True)

        # --- Save the full feed ---
        save_atom_feed(output_full_filename, base_feed_element, entries_data)

        # --- Save the recent feed (top 20) ---
        recent_entries_data = entries_data[:20]
        save_atom_feed(output_recent_filename, base_feed_element, recent_entries_data)

    except requests.exceptions.RequestException as e:
        click.echo(f"Error fetching URL {url}: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error accessing file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        # Catch other potential errors (parsing, file writing, etc.)
        click.echo(f"An unexpected error occurred: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    html_to_atom()

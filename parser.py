import os, re, csv, time
from lxml import etree

# C:/Classes/Q9/PRO335/PRO335_Wikipedia_Project/wikipedia_dumps/enwiki-latest-pages-articles.xml
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(ROOT_DIR, 'csv_files\\')
XML_DUMP = os.path.join(ROOT_DIR, 'wikipedia_dumps', 'enwiki-latest-pages-articles.xml')

# Column declaration for the various types of occupation columns
people_columns=['id', 'page_name', 'category']

# Column declaration for creating the movies.csv file
movie_columns = ['movie_id', 'movie_title', 'movie_director', 'star1', 'star2', 'star3', 'star4', 'star5', 'star6']

# Column declaration for the movies.csv file that puts the 'stars' into an array in a single column
movie_array_columns = ['movie_id', 'movie_title', 'movie_director', 'stars']

# Occupations are not case sensitive, In testing there was no difference in results whether capitalized or not
all_occupations = ['Actor','Actress','Director']

def get_runtime(func):
    """
    Runtime wrapper to test function runspeeds
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f'--- {(time.time() - start_time)} seconds ---')
        return result
    return wrapper

def extract_page_to_txt(file_path: str, target_title: str, output_txt=None):
    """
    Parses a single Wikipedia page's text into a .txt file
    filename will default to the 'pagetitle' + '.txt'
    """
    namespaces = {
        'mediawiki': 'http://www.mediawiki.org/xml/export-0.11/'
    }
    
    context = etree.iterparse(
        file_path,
        events=("end",),
        tag="{http://www.mediawiki.org/xml/export-0.11/}page"
    )
    
    for event, elem in context:
        title_elem = elem.find("./mediawiki:title", namespaces=namespaces)
        revision_elem = elem.find("./mediawiki:revision", namespaces=namespaces)
        text_elem = revision_elem.find("./mediawiki:text", namespaces=namespaces) if revision_elem is not None else None
        
        if title_elem is not None and title_elem.text == target_title:
            if text_elem is not None and text_elem.text is not None:
                page_text = text_elem.text
                
                file_title = (title_elem.text).replace(" ", "")
                file_title += '.txt'

                with open(CSV_DIR + output_txt or file_title, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(page_text)
                
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
                
                return output_txt
        
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    
    return None

def extract_by_occupation(output_csv: str, file_path: str, max_pages: int, search_terms: list[str], columns: list[str]):
    titles = []
    actor_id = 1
    pages_processed = 0
    output_csv = str(output_csv)
    columns = columns

    try:
        os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
        if not output_csv.lower().endswith('.csv'):
            output_csv += '.csv'
    except Exception as e:
        output_csv = 'default.csv'

    with open(CSV_DIR + output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Write header row
        csv_writer.writerow(columns)

        namespaces = {
            'mediawiki': 'http://www.mediawiki.org/xml/export-0.11/'
        }
        context = etree.iterparse(
            file_path,
            events=("end",),
            tag="{http://www.mediawiki.org/xml/export-0.11/}page"
        )
        for event, elem in context:
            title_elem = elem.find("./mediawiki:title", namespaces=namespaces)
            revision_elem = elem.find("./mediawiki:revision", namespaces=namespaces)
            text_elem = revision_elem.find("./mediawiki:text", namespaces=namespaces) if revision_elem is not None else None

            if title_elem is not None and text_elem is not None and text_elem.text is not None:
                page_text = text_elem.text

                occupation_line = re.search(r"(?m)^\| occupation\s*=\s*(.*)", page_text)
                if occupation_line:
                    occupation_content = occupation_line.group(1).lower()

                    matching_term = next((term for term in search_terms if term.lower() in occupation_content), None)
                    if matching_term:
                        title_text = title_elem.text

                        row_data = [
                            actor_id if col == 'id' else
                            title_text if col in ['title', 'page_name'] else
                            matching_term if col == 'category' else
                            ''
                            for col in columns
                        ]
                        csv_writer.writerow(row_data)

                        titles.append(title_text)

                        actor_id += 1

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

            pages_processed += 1
            if max_pages and pages_processed >= max_pages:
                break

    print(f"Processed {pages_processed} pages")
    print(f"Found {len(titles)} matching titles")
    return titles

def extract_movies(output_csv: str, file_path: str, max_pages: int, columns: list[str]):
    """
    Parses Wikipedia dumps for text elements that contain the str "Infobox film"

    Returns:
        .csv output with columns: 'movie_id', 'movie_title', 'movie_director', 'star1', 'star2', 'star3', 'star4', 'star5', 'star6'
    """
    titles = []
    movie_id = 1
    pages_processed = 0

    try:
        os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
        if not output_csv.lower().endswith('.csv'):
            output_csv += '.csv'
    except Exception as e:
        output_csv = 'default_movies.csv'

    with open(CSV_DIR + output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        columns = columns or ['movie_id', 'movie_title', 'movie_director', 'star1', 'star2', 'star3', 'star4', 'star5', 'star6']
        
        csv_writer.writerow(columns)

        namespaces = {
            'mediawiki': 'http://www.mediawiki.org/xml/export-0.11/'
        }
        
        context = etree.iterparse(file_path, events=("end",), tag="{http://www.mediawiki.org/xml/export-0.11/}page")
        
        for event, elem in context:
            title_elem = elem.find("./mediawiki:title", namespaces=namespaces)
            revision_elem = elem.find("./mediawiki:revision", namespaces=namespaces)
            text_elem = revision_elem.find("./mediawiki:text", namespaces=namespaces) if revision_elem is not None else None

            if title_elem is not None and text_elem is not None and text_elem.text is not None:
                page_text = text_elem.text

                if "Infobox film" in page_text:
                    director_match = re.search(r"(?m)^\| director\s*=\s*(.*)", page_text)
                    director = None
                    if director_match:
                        director = director_match.group(1).strip()
                        director = re.sub(r"\[\[|\]\]", "", director)
                        director = re.sub(r"\{\{.*?\}\}", "", director)
                        director = re.sub(r"<.*?>", "", director)
                        director = re.sub(r"[\|\}\>].*", "", director).strip()

                    starring = None
                    starring_match = re.search(r"(?m)^\| starring\s*=\s*(\{\{(plainlist|Plainlist|plain List|Plain List)\|[\s\S]*?\}\})", page_text, re.IGNORECASE)
                    if starring_match:
                        starring = starring_match.group(1).strip()

                        plainlist_match = re.search(r"\{\{\s*(plainlist|Plainlist|plain List|Plain List)\s*\|\s*([\s\S]+?)\s*\}\}", starring, re.IGNORECASE | re.DOTALL)
                        if plainlist_match:
                            plainlist_content = plainlist_match.group(2).strip()
                            actors = [actor.strip() for actor in plainlist_content.split('\n') if actor.strip().startswith('*')]
                            actors = [actor.lstrip('*').strip() for actor in actors]
                            actors = [re.sub(r'\[\[|\]\]', '', actor) for actor in actors]
                        else:
                            print("No match found for {{plainlist}}")
                    else:
                        starring_match = re.search(r"(?m)^\| starring\s*=\s*(.*)", page_text)
                        if starring_match:
                            starring = starring_match.group(1).strip()
                            starring = re.sub(r"\[\[|\]\]", "", starring)

                            ubl_match = re.search(r"\{\{ubl\|([^\}]+)\}\}", starring)
                            
                            actors = []
                            if ubl_match:
                                ubl_content = ubl_match.group(1).strip()
                                actors = [actor.strip() for actor in ubl_content.split('|')]
                                # print(f"Actors extracted from {{ubl}}: {actors}")

                            if not actors:
                                actors = re.findall(r"\[\[([^\|\]]+)\]\]", starring)
                                # print(f"Actors extracted from regular wiki links: {actors}")  # Debug: regular wiki links actors

                            if not actors:
                                actors = ["Unknown", "Unknown", "Unknown"]
                                # print("No actors found, defaulting to Unknown.")  # Debug: fallback message

                    starring1 = actors[0] if len(actors) > 0 else ''
                    starring2 = actors[1] if len(actors) > 1 else ''
                    starring3 = actors[2] if len(actors) > 2 else ''
                    starring4 = actors[3] if len(actors) > 3 else ''
                    starring5 = actors[4] if len(actors) > 4 else ''
                    starring6 = actors[5] if len(actors) > 5 else ''
                    title_text = title_elem.text

                    row_data = [
                        movie_id if col == 'movie_id' else
                        title_text if col == 'movie_title' else
                        director if col == 'movie_director' else
                        starring1 if col == 'star1' else
                        starring2 if col == 'star2' else
                        starring3 if col == 'star3' else
                        starring4 if col == 'star4' else
                        starring5 if col == 'star5' else
                        starring6 if col == 'star6' else ''
                        for col in columns
                    ]
                    csv_writer.writerow(row_data)
                    titles.append(title_text)
                    movie_id += 1

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

            pages_processed += 1
            if max_pages and pages_processed >= max_pages:
                break

    print(f"Processed {pages_processed} pages")
    print(f"Found {len(titles)} movies")
    return titles

def extract_movies_array(output_csv: str, file_path: str, max_pages: int, columns: list[str]):
    """
    Parses Wikipedia dumps for text elements that contain the str "Infobox film"

    Writes a CSV output with columns:
    'movie_id', 'movie_title', 'movie_director', and 'stars'
    The 'stars' column outputs an array of up to 6 lead actors for each movie.
    """
    titles = []
    movie_id = 1
    pages_processed = 0

    try:
        os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
        if not output_csv.lower().endswith('.csv'):
            output_csv += '.csv'
    except Exception as e:
        output_csv = 'default_movies.csv'

    with open(CSV_DIR + output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        columns = columns or ['movie_id', 'movie_title', 'movie_director', 'stars']
        
        csv_writer.writerow(columns)

        namespaces = {
            'mediawiki': 'http://www.mediawiki.org/xml/export-0.11/'
        }
        
        context = etree.iterparse(file_path, events=("end",), tag="{http://www.mediawiki.org/xml/export-0.11/}page")
        
        for event, elem in context:
            title_elem = elem.find("./mediawiki:title", namespaces=namespaces)
            revision_elem = elem.find("./mediawiki:revision", namespaces=namespaces)
            text_elem = revision_elem.find("./mediawiki:text", namespaces=namespaces) if revision_elem is not None else None

            if title_elem is not None and text_elem is not None and text_elem.text is not None:
                page_text = text_elem.text

                if "Infobox film" in page_text:
                    director_match = re.search(r"(?m)^\| director\s*=\s*(.*)", page_text)
                    director = None
                    if director_match:
                        director = director_match.group(1).strip()
                        director = re.sub(r"\[\[|\]\]", "", director)
                        director = re.sub(r"\{\{.*?\}\}", "", director)
                        director = re.sub(r"<.*?>", "", director)
                        director = re.sub(r"[\|\}\>].*", "", director).strip()

                    starring = None
                    starring_match = re.search(r"(?m)^\| starring\s*=\s*(\{\{(plainlist|Plainlist|plain List|Plain List)\|[\s\S]*?\}\})", page_text, re.IGNORECASE)
                    actors = []
                    if starring_match:
                        starring = starring_match.group(1).strip()

                        plainlist_match = re.search(r"\{\{\s*(plainlist|Plainlist|plain List|Plain List)\s*\|\s*([\s\S]+?)\s*\}\}", starring, re.IGNORECASE | re.DOTALL)
                        if plainlist_match:
                            plainlist_content = plainlist_match.group(2).strip()
                            actors = [actor.strip() for actor in plainlist_content.split('\n') if actor.strip().startswith('*')]
                            actors = [actor.lstrip('*').strip() for actor in actors]
                            actors = [re.sub(r'\[\[|\]\]', '', actor) for actor in actors]
                    else:
                        starring_match = re.search(r"(?m)^\| starring\s*=\s*(.*)", page_text)
                        if starring_match:
                            starring = starring_match.group(1).strip()
                            starring = re.sub(r"\[\[|\]\]", "", starring)

                            ubl_match = re.search(r"\{\{ubl\|([^\}]+)\}\}", starring)
                            
                            if ubl_match:
                                ubl_content = ubl_match.group(1).strip()
                                actors = [actor.strip() for actor in ubl_content.split('|')]

                            if not actors:
                                actors = re.findall(r"\[\[([^\|\]]+)\]\]", starring)

                    # Trim the actors list to a maximum of 6
                    actors = actors[:6]
                    title_text = title_elem.text

                    row_data = [
                        movie_id if col == 'movie_id' else
                        title_text if col == 'movie_title' else
                        director if col == 'movie_director' else
                        actors if col == 'stars' else ''
                        for col in columns
                    ]
                    # Write row, converting 'actors' list to a string if it's in the 'stars' column
                    row_data = [
                        str(value) if isinstance(value, list) else value
                        for value in row_data
                    ]
                    csv_writer.writerow(row_data)
                    titles.append(title_text)
                    movie_id += 1

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

            pages_processed += 1
            if max_pages and pages_processed >= max_pages:
                break

    print(f"Processed {pages_processed} pages")
    print(f"Found {len(titles)} movies")
    return titles

def test_parse(output_csv: str, max_pages: int):
    # extract_page_to_txt(XML_DUMP, 'Betty White', None)
    # extract_by_occupation(output_csv, XML_DUMP, max_pages, director_terms, people_columns)
    extract_movies_array(output_csv, XML_DUMP, max_pages, movie_array_columns)

@get_runtime
def parse_data():
    output_csv = "movies_array.csv"

    # extract_page_to_txt(XML_DUMP, 'Betty White', None)
    # extract_by_occupation(output_csv, XML_DUMP, None, director_terms, people_columns)
    extract_movies_array(output_csv, XML_DUMP, None, movie_array_columns)

if __name__ == "__main__":
    parse_data()

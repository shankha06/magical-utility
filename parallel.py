# Standard library imports  
import concurrent.futures
import random  
import time 
import logging  
import requests
import numexpr  
import os  
import argparse
from typing import Callable, Any, List, Dict  
from urllib.parse import urlparse, unquote  
from multiprocessing import cpu_count
  
# Related third-party imports  
from magic_google import MagicGoogle 
import pandas as pd
from rich import print  
from rich.console import Console 
  

# Decorator to suppress print statements  
def suppress_print(func: Callable) -> Callable:  
    def wrapper(*args, **kwargs):  
        original_log_level = logging.getLogger().level  
        logging.getLogger().setLevel(logging.CRITICAL)  
  
        try:  
            result = func(*args, **kwargs)  
        finally:  
            logging.getLogger().setLevel(original_log_level)  
  
        return result  
    return wrapper 

def calculate_time(func: Callable[..., Any]) -> Callable[..., Any]:  
    """  
    Decorator function to calculate and print the time in seconds it takes to run a given function.  
      
    Args:  
    - func: Function to be timed.  
      
    Returns:  
    - Decorated function that prints the time taken to run the input function in seconds.  
    """ 
    def wrapper(*args, **kwargs):  
        start_time = time.time()  
        result = func(*args, **kwargs)  
        end_time = time.time()  
        print(f"<<--------------Time taken to run {func.__name__}: {((end_time - start_time) / 60):.2f} mins --------->>") 
        return result  
    return wrapper  

def internet_presence(searched_pages):

    internet_trust = ["www.nbcnews.com", "www.cnn.com", "abcnews.go.com", "apnews.com", "www.dallasnews.com", "www.usatoday.com", "www.washingtonpost.com", "news.google.com", "www.foxnews.com", "www.cbsnews.com", "www.fox4news.com", "www.nytimes.com", "www.axios.com", "www.reuters.com", "www.vox.com", "www.wsj.com", "www.politico.com", "time.com", "www.bloomberg.com", "www.forbes.com", "www.reuters.com", "finance.yahoo.com", "finance.google.com", "www.linkedin.com", 'www.zoominfo.com',"www.sec.gov/edgar.shtml", "www.hoovers.com", "www.dnb.com", "www.crunchbase.com", "angel.co", "www.owler.com", "pitchbook.com", "en.wikipedia.org"]

    total_count = len(set(internet_trust).intersection(set(searched_pages)))
    # print(searched_pages)
    if total_count >= 2:
        return True
    else:
        return False

@suppress_print  
def google_search(query: str) -> str:  
    """  
    Searches for the given query and returns the first Wikipedia result's title.  
  
    Args:  
    - query: A string representing the search query.  
  
    Returns:  
    - A string representing the title of the first Wikipedia result, or an empty string if none is found.  
    """  
    wiki_page = ""
    domain_search_result = []
    time.sleep(random.randrange(1, 5))
    for result in mg.search_url(query=query, language  = "en", num = 8):
        parsed_url = urlparse(result)
        domain_search_result.append(parsed_url.netloc)
        if parsed_url.netloc == "en.wikipedia.org" and wiki_page == "":
            wiki_page = unquote(parsed_url.path.replace("/wiki/",""))
    # print(f"{query}: {domain_search_result}")
    if internet_presence(domain_search_result):
        return wiki_page
    else:
        return ""

def get_wikipedia_data(wiki_title):
    """
    Get the summary and full text of a Wikipedia article.

    Parameters:
    wiki_title (str): The title of the Wikipedia article.

    Returns:
    str: full text of the Wikipedia article.
    """
    endpoint = "https://en.wikipedia.org/w/api.php"
    
    # Parameters to get the full Wikipedia page for the given title
    full_text_params = {
        "action": "query",
        "format": "json",
        "titles": wiki_title,
        "prop": "extracts",
        "explaintext": True
    }

    try:
        full_text_response = requests.get(endpoint, params=full_text_params).json()
        # Extract the article text from the API response
        pages = full_text_response['query']['pages']
        page_id = next(iter(pages))
        article_text = pages[page_id]['extract']

        # Return the full text of the article
        return article_text
    except Exception as e:
        print(wiki_title)
        print(e)
        return ""
  
# @calculate_time  
def parallelize_calls(queries: List[str], max_threads: int , func: Callable = google_search) -> Dict[str, str]:  
    """  
    Executes the provided function for each query in parallel using ThreadPoolExecutor.  
  
    Args:  
    - func: The function to execute for each query.  
    - queries: List of strings representing search queries.  
    - max_threads: Maximum number of threads to use for parallel execution.  
  
    Returns:  
    - Dictionary with query as key and search result as value.  
    """
  
    def chunks(lst, n):  
        """Yield successive n-sized chunks from lst."""  
        for i in range(0, len(lst), n):  
            yield lst[i:i + n]  
  
    results = {}  
  
    for chunk in chunks(queries, max_threads):  
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:  
            futures = {executor.submit(func, query): query for query in chunk}
            for future in concurrent.futures.as_completed(futures):  
                query = futures[future]  
                result = future.result()  
                if result is not None:  
                    results[query] = result  
            time.sleep(random.randrange(min(30,max_threads-4), max_threads))
    return results 
@calculate_time  
def process_search(arguments):
    company_df = pd.read_csv('company_source.csv')
    file_name = 'content_wiki.csv'
    if os.path.isfile(file_name):
        content_df = pd.read_csv('content_wiki.csv')
        merged_df = pd.merge(company_df, content_df, on='Company', how='left')
        filtered_df = merged_df[~pd.isnull(merged_df['Company'])].sample(arguments['batch_size'])
    else:
        filtered_df = company_df.sample(arguments['batch_size'])
    assert filtered_df.shape[0] == arguments['batch_size']
    companies_usa = filtered_df['Company'].tolist() 
    success = False
    while not success:
        try:
            wiki_pages_dict = parallelize_calls(queries = companies_usa, 
                                                max_threads = arguments["max_threads"],func=google_search)    
            success = True
        except:
            time.sleep(300)
            
    console.print("Google Search complete......", style="dark_green") 
    # time.sleep(1) 
    console.print("Starting Wikipedia search......", style="yellow")
    success_pages = [ wiki_pages_dict[search] for search in wiki_pages_dict.keys() if wiki_pages_dict[search] != ""]
    wiki_content_dict = parallelize_calls(queries = success_pages,  
                                          max_threads = arguments["max_threads"], func = get_wikipedia_data)
    console.print("Wikipedia Extraction complete......", style="dark_green")

    page_data = pd.DataFrame(list(wiki_pages_dict.items()), columns=['Company', 'Wikipedia Title']) 
    content_data = pd.DataFrame(list(wiki_content_dict.items()), columns=['Wikipedia Title', 'Wikipedia Content']) 
    wiki_data = pd.merge(page_data, content_data, on='Wikipedia Title', how = "left")  

    # Check if the file exists  
    if os.path.isfile(file_name):   
        existing_data = pd.read_csv(file_name)  
        wiki_data = pd.concat([existing_data, wiki_data], ignore_index=True)  
    wiki_data.to_csv(file_name, index=False)

def parse_arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()
    
    # Add arguments to the parser
    parser.add_argument("--max-threads", type=int, default=min(cpu_count()*4, 63), help="Maximum number of threads")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size")
    parser.add_argument("--epoch", type=int, default=30, help="Number of epochs")
    
    # Parse the arguments
    args = parser.parse_args()
    
    return vars(args)
    
if __name__ == '__main__':
    # companies_usa = ["Amazon", "Apple", "Boeing", "Caterpillar", "Chevron", "Cisco", "Coca-Cola", "Disney", "Exxon Mobil", "Facebook", "Goldman Sachs", "Google", "IBM", "Intel"]
    args = parse_arguments()
    os.environ['NUMEXPR_MAX_THREADS'] = str(args['max_threads'])
    numexpr.set_num_threads(args['max_threads'])  
    console = Console()
    mg = MagicGoogle()

    # Read the two files into DataFrames
    for _ in range(args['epoch']):
         process_search(args)

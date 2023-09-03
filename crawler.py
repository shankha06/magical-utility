import requests  
from bs4 import BeautifulSoup  
import re  
  
def get_terms_of_use_link(url): 
    """  
    This function takes a URL as input and returns the terms of use link found on the given website.  
      
    Args:  
    url (str): The URL of the website to search for the terms of use link.  
      
    Returns:  
    str or None: The terms of use link if found, otherwise None.  
    """ 
    if not url.startswith("http"):
        url = "http://" + url
    if not url.endswith("/"):
        url += "/"
        
    response = requests.get(url)  
      
    soup = BeautifulSoup(response.text, 'html.parser')  
  
    terms_links = []  
    patterns = ['terms of use', 'terms & conditions', 'terms and conditions', 'terms of service', 'user agreement']  
      
    for pattern in patterns:  
        terms_links.extend(soup.find_all('a', href=True, text=re.compile(pattern, re.IGNORECASE)))  
        terms_links.extend(soup.find_all('a', href=re.compile(pattern.replace(' ', '-'), re.IGNORECASE)))  
  
    if terms_links:  
        terms_url = terms_links[0]['href']  
        if not terms_url.startswith('http'):  
            terms_url = f"{url}/{terms_url.lstrip('/')}"  
        return terms_url  
    return None  
  
def crawl_terms_of_use_page(terms_url):  
    """
    Crawls the Terms of Use page of a given URL and returns the text content.
    If there are language or region-specific links, it prioritizes the US version.

    Args:  
        terms_url (str): The URL of the Terms of Use page to crawl.  

    Returns:  
        str: The text content of the Terms of Use page.  
    """  
    response = requests.get(terms_url)  
    soup = BeautifulSoup(response.text, 'html.parser') 
    
    # Check if there are language or region-specific links  
    for link in soup.find_all("a", href=True):  
        link_text = link.get_text().strip().lower()  
        if "US" in link_text or "united states" in link_text:
            terms_url = urljoin(terms_url, link["href"])  
            print(f"Terms of Use US specific: {terms_url}")  
            response = requests.get(terms_url)  
            soup = BeautifulSoup(response.text, "html.parser")  
            break  
  
    # print(soup.prettify())
    return soup.text

def partition_text(text, max_length=2048):  
    words = text.split(" ")  
    chunks = []  
    current_chunk = []  
  
    for word in words:  
        if len(" ".join(current_chunk)) + len(word) < max_length:  
            current_chunk.append(word)  
        else:  
            chunks.append(" ".join(current_chunk))  
            current_chunk = [word]  
  
    if current_chunk:  
        chunks.append(" ".join(current_chunk))  
  
    return chunks  
  
def ask_chatgpt_api(prompt:str, assumed_role: str = None) -> str:  
    """  
    This function sends a prompt to OpenAI's GPT-3 chatbot API and returns the response.  
  
    Args:  
        prompt (str): The prompt to send to the chatbot API.  
        assumed_role (str, optional): The assumed role of the chatbot. Defaults to   
                                      "You are an AI assistant that helps people find information.".  
  
    Returns:  
        str: The response from the chatbot API as a string.  
    """  
    if assumed_role is None:  
        assumed_role = "You are an AI assistant that helps people find information."  
    response = openai.ChatCompletion.create(  
                  engine="GPT35",  
                  messages = [  
                      {"role":"system","content":assumed_role},  
                      {"role":"user","content":prompt}],  
                  temperature=0.1,  
                  max_tokens=400,  
                  top_p=0.96,  
                  frequency_penalty=0,  
                  presence_penalty=0,  
                  stop=None)  
    output = response["choices"][0]["message"]["content"].strip()    
    return output 
  
import re  
  
def is_scraping_allowed_termsnconditions(url: str) -> bool:  
    """
    Checks if web scraping is allowed by the website's terms and conditions.  
  
    Args:  
    url (str): The URL of the website to check.  
  
    Returns:  
    bool: True if web scraping is allowed, False otherwise.  
    """  
    terms_link = get_terms_of_use_link(url)  
    if terms_link:  
        print(f"Terms of Use URL: {terms_link}")  
        content = crawl_terms_of_use_page(terms_link)  
        text_chunks = partition_text(content)  
  
        for chunk in text_chunks:  
            assumed_role = "You are a Legal consultant, whose job is to read legal documents and provide answer."  
            prompt = f"The following text is an excerpt from a website's Terms of Use:\n\n{chunk}\n\nDoes the website allow copying public information available about the company? Respond with 1 or 0 or 2, where 1 signifies the website allows copying public data regarding the company from the website via human or bot and 0 signifies the website doesn't allows copying public data regarding the company from the website via human or bot and 2 signifies no such restriction is mentioned in the Text. Don't explain yourself."  
            answer = ask_chatgpt_api(prompt, assumed_role)  
            # answer = chatgpt_call(f"{assumed_role} {prompt}", bearer_token)  
            answer = re.sub(r'[^a-zA-Z0-9\s]', '', answer)  
            print(answer)  
            if answer.lower().strip() in ["0"]:  
                print(prompt)  
                return False  
    else:  
        print("Terms of Use URL not found.")  
    return True     

import time  
import requests  
from urllib.parse import urlparse, urljoin  
from urllib.robotparser import RobotFileParser  

def meta_information(url):
    """
    Extracts the title and meta description from a given URL using BeautifulSoup.

    Args:  
        url (str): The URL of the webpage to extract the title and meta description from.  

    Returns:  
        str: A formatted string containing the webpage title and meta description.  
    """  
    response = requests.get(url)  
    soup = BeautifulSoup(response.text, 'html.parser')  

    title = soup.title.text  
    meta_desc = soup.find('meta', attrs={'name': 'description'})['content']
    return f"{title}. {meta_desc}"

def get_about_us_url(response, base_url): 
    """
    Given a response and a base URL, this function finds and returns the 'About Us' URL.

    Args:  
        response (str): The HTML response from the website.  
        base_url (str): The base URL of the website.  

    Returns:  
        str: The 'About Us' URL, or None if not found.  
    """
    soup = BeautifulSoup(response, 'html.parser')
    for link in soup.find_all('a'): 
        # print(link)
        href = link.get('href')  
        about_keywords = ['about us', 'about the team', 'meet the team', 'our team', 'who we are', "about"]
        
        if href is not None:
            if link.text.replace('-', ' ').replace('_', ' ').strip().lower() in about_keywords:  
                return urljoin(base_url, href)  
            for keyword in about_keywords:
                if keyword in href.replace('/', ' ').replace('-', ' ').replace('_', ' ').strip().lower():
                    return urljoin(base_url, href)  
        #     # Check if the anchor tag contains 'about-us', or 'about us' in the URL or text  
        #     if re.search(r'(about[-_]?us)', href, re.IGNORECASE) or re.search(r'(about[-_]?us)', link.text, re.IGNORECASE):  
        #         return urljoin(base_url, href)  
    
    return None  
  
def get_about_us_text(about_us_url, headers):  
    """  
    Retrieves the text content of an About Us page from a given URL.  
  
    Args:  
        about_us_url (str): The URL of the About Us page to be processed.  
        headers (dict): Headers to be sent with the HTTP request.  
  
    Returns:  
        str: The extracted text content of the About Us page with leading and trailing spaces removed.  
    """
    if not about_us_url.startswith("http"):
        about_us_url = "http://" + about_us_url
    if not about_us_url.endswith("/"):
        about_us_url += "/"
    response = requests.get(about_us_url, headers=headers)    
    soup = BeautifulSoup(response.text, 'html.parser')  
  
    # Remove script and style elements  
    for element in soup(['script', 'style']):  
        element.decompose()  
  
    # Get text from the page  
    text = soup.get_text()  
  
    # Remove leading and trailing spaces on each line  
    lines = (line.strip() for line in text.splitlines())  
  
    # Combine the lines into a single string  
    about_us_text = '\n'.join(line for line in lines if line)  
    return about_us_text  

def get_robots_txt_url(url):  
    parsed_url = urlparse(url)  
    scheme = parsed_url.scheme  
    netloc = parsed_url.netloc  
    return f"{scheme}://{netloc}/robots.txt"  
  
def parse_visit_time(robots_txt_content):  
    visit_time_directive = "Visit-time"  
    for line in robots_txt_content.splitlines():  
        if line.startswith(visit_time_directive):  
            visit_time_range = line[len(visit_time_directive):].strip()  
            start, end = visit_time_range.split("-")  
            return int(start), int(end)  
    return None, None  
  
def crawl_website(url: str, user_agent: str="Googlebot") -> str:
    """  
    Crawls a website starting from the given URL, respecting the rules specified in the robots.txt file.  
    Retrieves the About Us page and prints its content if found.  
  
    Args:  
        url (str): The starting URL of the website to be crawled.  
        user_agent (str, optional): The user agent to be used for crawling. Defaults to "Googlebot".  
  
    Returns:  
        None  
    """ 
    robots_txt_url = get_robots_txt_url(url)  
    response = requests.get(robots_txt_url)  
    robots_txt_content = response.text  
  
    rp = RobotFileParser()  
    rp.parse(robots_txt_content.splitlines())  
  
    if not rp.can_fetch(user_agent, url):  
        print(f"User-agent '{user_agent}' cannot crawl the URL: {url}")  
        return  
  
    crawl_delay = rp.crawl_delay(user_agent)  
    request_rate = rp.request_rate(user_agent)  
    visit_time_start, visit_time_end = parse_visit_time(robots_txt_content)  
  
    if crawl_delay:  
        print(f"Crawl delay for user-agent '{user_agent}': {crawl_delay} seconds")  
    if request_rate:  
        print(f"Request rate for user-agent '{user_agent}': {request_rate.requests}/{request_rate.seconds} seconds")  
    if visit_time_start is not None and visit_time_end is not None:  
        print(f"Visit-time for user-agent '{user_agent}': {visit_time_start}-{visit_time_end}")  
  
    start_time = time.time()  
  
    while True:  
        current_hour = time.localtime().tm_hour  
        if visit_time_start is not None and visit_time_end is not None:  
            if not (visit_time_start <= current_hour < visit_time_end):  
                time.sleep(3600)  # Sleep for an hour and check again  
                continue  
  
        if request_rate:  
            time_since_start = time.time() - start_time  
            if time_since_start >= request_rate.seconds:  
                requests_allowed = request_rate.requests  
                start_time = time.time()  
            else:  
                requests_allowed = 0  
        else:  
            requests_allowed = 1
            
        requests_allowed = min(1, requests_allowed)
  
        for _ in range(requests_allowed):  
            response = requests.get(url, headers={"User-Agent": user_agent}, timeout=10, allow_redirects=True)
            if response.status_code == 200:  
                print("Crawling:", url)  
                about_us_url = get_about_us_url(response.text, link)  
                if about_us_url:  
                    print("About Us URL:", about_us_url)  
                    about_us_text = get_about_us_text(about_us_url, headers={"User-Agent": user_agent})  
                    print("\nAbout Us Text:\n", about_us_text)
            
if __name__ == "__main__":  
    website = input("Enter the website URL to crawl: ") 
    crawl_website(website)  

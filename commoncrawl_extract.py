import io
import gzip
import requests
from comcrawl.utils import make_multithreaded
from comcrawl import IndexClient
URL_TEMPLATE = "https://data.commoncrawl.org/{filename}"

def download_single_result(result):
    """Downloads HTML for single search result.
    Args:
        result: Common Crawl Index search result from the search function.
    Returns:
        The provided result, extendey by the corresponding HTML String.

    """
    offset, length = int(result["offset"]), int(result["length"])

    offset_end = offset + length - 1

    url = URL_TEMPLATE.format(filename=result["filename"])
    response = (requests
                .get(
                    url,
                    headers={"Range": f"bytes={offset}-{offset_end}"}
                ))

    zipped_file = io.BytesIO(response.content)
    # print(response.content)
    unzipped_file = gzip.GzipFile(fileobj=zipped_file)

    raw_data: bytes = unzipped_file.read()
    try:
        data: str = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        print(f"Warning: Could not extract file downloaded from {url}")
        data = ""

    if len(data) > 0:
        data_parts = data.strip().split("\r\n\r\n", 2)
        html_content = data_parts[2] if len(data_parts) == 3 else ""
        soup = BeautifulSoup(html_content, 'html.parser')  
        # Remove script and style elements  
        for element in soup(['script', 'style']):  
            element.decompose()  

        # Get text from the page  
        text = soup.get_text()  

        # Remove leading and trailing spaces on each line  
        lines = (line.strip() for line in text.splitlines())  

        # Combine the lines into a single string  
        html_content = '\n'.join(line for line in lines if line)  
        result["html_parsed"] = html_content
        title = soup.title.text
        parsed_url = urlparse(result["url"])
        if parsed_url.path == "/":
            title = f"Home Page of the company | {title}"
        try:
            meta_desc = soup.find('meta', attrs={'name': 'description'})['content']
            result["url_metadata"] = f"{title}. {meta_desc}"
        except TypeError:
            result["url_metadata"] = title
    return result
def download_multiple_results(results, threads = 8):
    """Downloads search results.

    For each Common Crawl search result in the given list the
    corresponding HTML page is downloaded.
    Args:
        results: List of Common Crawl search results.
        threads: Number of threads to use for faster parallel downloads on
            multiple threads.
    Returns:
        The provided results list, extended by the corresponding
        HTML strings.

    """
    results_with_html = []
    if threads:
        multithreaded_download = make_multithreaded(download_single_result,
                                                    threads)
        results_with_html = multithreaded_download(results)

    else:
        for result in results:
            result_with_html = download_single_result(result)
            results_with_html.append(result_with_html)

    return results_with_html

if __name__ == "__main__": 

    client = IndexClient(["2023-23", "2023-14","2023-06","2022-49","2022-40", "2022-33", "2022-27", "2022-21", "2022-05", "2021-49", "2021-43", "2021-39", "2021-31", "2021-25", "2021-21", "2021-17", "2021-10", "2021-04"], verbose = False)
    client.search("covanta.com/*", threads=10)
    if len(client.results) > 0:
        first_page_html = client.results[0]["url"]
        print(first_page_html)
        client.results = (pd.DataFrame(client.results)
                        .sort_values(by="timestamp")
                        .drop_duplicates("urlkey", keep="last")
                        .to_dict("records"))
        
        result = pd.DataFrame(client.results)
        print(result.columns.tolist())
        result = result[(result["status"]=="200") & (result["mime"]=="text/html") & (result["languages"]=="eng") & (result["encoding"]=="UTF-8")]
        print(f"Total Searched pages in Common Crawl resulted for the domain : {result.shape[0]} pages")

    result["url_metadata"] = result.apply(lambda row: meta_information_pandas(row), axis = 1)
    content_detailed = result[(result["url_metadata"]!="")]
    content_detailed = download_multiple_results(content_detailed.to_dict('records'))
    content_detailed = pd.DataFrame(content_detailed)
    print(f"Result is filtered to contain only relevant pages: {content_detailed.shape[0]} pages")

import tkinter as tk
import tkinterweb
import requests
from bs4 import BeautifulSoup
import re

def split_text_by_date(text):
  # Define a regular expression pattern for date like "Aug 14, 2023, 11:12 PM IST"
  date_pattern = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+(?:AM|PM)\s+IST"
  # Find all the matches of the date pattern in the text
  dates = re.findall(date_pattern, text)
  # Split the text by the date pattern
  texts = re.split(date_pattern, text)
  # Return a list of tuples of (date, text) pairs
  return ".\n".join(texts)

# Define the function to scrape a website and show the headlines and content
def scrape_website():
    # Get the url from the entry widget
    url = "https://economictimes.indiatimes.com/news/economy"

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

    # Define an accept string to indicate the media types that are acceptable for the response
    accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"

    # Define a language string to indicate the preferred language for the response
    language = "en-US,en;q=0.9"

    # Define a connection string to indicate whether to keep the connection alive or not
    connection = "keep-alive"

    # Define a header dictionary with the keys and values for user agent, accept, language, connection
    headers = {"User-Agent": user_agent, "Accept": accept, "Accept-Language": language, "Connection": connection}
    # Make a request to the url and get the response
    response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)

    # Parse the response content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the headlines (h1-h6) tags in the soup
    headlines = soup.find_all(["h1", "h2", "h3"])

    # Create a list to store the headlines and content
    data = []

    # Loop through each headline
    for headline in headlines:
        # Get the headline text
        headline_text = headline.get_text().strip()

        # Get the next sibling element of the headline, which is usually the content
        content = headline.next_sibling

        # If the content is not None and is a tag (not a string)
        if content and content.name:
            # Get the content text
            content_text = content.get_text().strip()
        else:
            # Otherwise, set the content text to an empty string
            content_text = ""
        content_text = split_text_by_date(content_text)
        data.append((headline_text, content_text))

    # Clear the text widget
    text.delete("1.0", "end")

    # Loop through each item in the data list
    for item in data:
        # Insert the headline text as bold and with a newline
        text.insert("end", item[0] + "\n", "bold")

        # Insert the content text as normal and with a bullet point and a newline
        text.insert("end", "• " + item[1] + "\n", "normal")


# Create the main window
root = tk.Tk()
root.title("Tkinter Browser App with Tiles")
root.state("zoomed")

# Create the frames for the tiles
frame1 = tk.Frame(root, bg="red", width=200, height=200)
frame2 = tk.Frame(root, bg="green", width=100, height=100)
frame3 = tk.Frame(root, bg="blue", width=100, height=100)

# Pack the frames with appropriate options
frame1.pack(side="left", fill="both", expand=True)
frame2.pack(side="top", fill="x")
frame3.pack(side="bottom", fill="x")

# Create a browser widget in frame1
browser = tkinterweb.HtmlFrame(frame1)

# Load a default url page
browser.load_website("https://www.google.co.in")

# Pack the browser widget
browser.pack(fill="both", expand=True)

browser = tkinterweb.HtmlFrame(frame2)

# Load a default url page
browser.load_website("https://www.reddit.com")

# Pack the browser widget
browser.pack(fill="both", expand=True)

# Create a button to scrape the website and show the results
button = tk.Button(frame2, text="Read ET News", command=scrape_website)
button.pack(padx=10, pady=10)
# Create labels in frame2 and frame3 to show some text
text = tk.Text(frame2, autoseparators=True)
text.tag_configure("bold", font=("Arial", 12, "underline"))
text.tag_configure("normal", font=("Arial", 12))

# Pack the text widget
text.pack(padx=10, pady=10, fill="none", expand=True)

# label2.pack(padx=10, pady=10)
label3 = tk.Label(frame3, text="This is frame 3")
label3.pack(padx=10, pady=10)

# Start the main loop
root.mainloop()

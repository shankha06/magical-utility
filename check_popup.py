from bs4 import BeautifulSoup
import requests

def check_for_popups(url):
    """
    Scrapes a webpage and checks for potential pop-ups related to terms,
    content warnings, or subscription requests.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        bool: True if any potential pop-up indicators are found, False otherwise.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # Common keywords and phrases associated with pop-ups
        popup_keywords = [
            "terms",
            "terms of service",
            "privacy policy",
            "content warning",
            "mature content",
            "subscribe",
            "subscription",
            "premium",
            "sign up",
            "register",
            "agree",
            "accept",
            "continue",
            "confirm",
            "verify your age",
            "age verification",
            "access content",
            "unlock content",
            "get full access",
            "limited access",
            "cookies"
        ]

        # Check for these keywords in text content of specific elements
        elements_to_check = ['div', 'section', 'article', 'aside', 'main', 'footer', 'form', 'dialog']

        for element_type in elements_to_check:
            elements = soup.find_all(element_type)
            for element in elements:
                text_content = element.get_text(strip=True).lower()
                for keyword in popup_keywords:
                    if keyword in text_content:
                        print(f"Potential pop-up indicator found in <{element_type}> tag: '{keyword}'")
                        return True

        # Check for specific CSS classes or IDs that are often used for pop-ups
        popup_css_selectors = [
            ".popup",
            ".modal",
            ".overlay",
            "#popup-container",
            "#modal-window",
            "#overlay-background",
            "[role='dialog']",
            "[aria-modal='true']",
        ]

        for selector in popup_css_selectors:
            popup_elements = soup.select(selector)
            if popup_elements:
                first_element = popup_elements[0]
                element_text = first_element.get_text(strip=True).lower()
                # for keyword in popup_keywords:
                #     if keyword in element_text:
                #         tag_name = first_element.name
                print(f"Potential pop-up element found with CSS selector: '{selector}' (in <{first_element.name}> tag) containing keyword: '{element_text}'")
                return True

        return False

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return False
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return False
    
def check_for_human_interaction(url):
    """
    Scrapes a webpage and checks for potential indicators that human interaction
    might be required to access the content (e.g., login forms, age verification).

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        bool: True if potential human interaction indicators are found, False otherwise.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # Keywords and phrases suggesting human interaction
        interaction_keywords = [
            "login",
            "sign in",
            "log in",
            "username",
            "password",
            "email",
            "enter your email",
            "age verification",
            "verify your age",
            "are you 18 or older?",
            "date of birth",
            "captcha",
            "i'm not a robot",
            "create account",
            "register",
            "subscription required",
            "paywall",
            "unlock premium content",
            "enter your details",
            "submit",
            "continue",
            "accept terms",
            "agree to terms",
        ]

        # CSS selectors for common interactive elements
        interactive_selectors = [
            # "form",  # Look for forms (often login/registration)
            "input[type='password']",
            "input[type='email']",
            "input[type='text']",
            "button[type='submit']",
            "a[href*='login']",
            "a[href*='signup']",
            "div[role='dialog']",  # Dialog boxes can require interaction
            "iframe", # Can sometimes contain interactive elements
        ]

        # Check for keywords in the text content of the page
        # page_text = soup.get_text(strip=True).lower()
        # for keyword in interaction_keywords:
        #     if keyword in page_text:
        #         print(f"Potential human interaction indicator found in page text: '{keyword}'")
        #         return True

        # Check for specific interactive elements using CSS selectors
        for selector in interactive_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    if any(keyword in element.get_text(strip=True).lower() for keyword in interaction_keywords):
                        tag_name = element.name
                        print(f"Potential human interaction element found with CSS selector: '{selector}' (in <{tag_name}> tag) containing keyword: '{element.get_text(strip=True).lower()}'")
                        # return True
                # print(f"Potential human interaction element found with CSS selector: '{selector}' - {elements[0] }")
                # return True

        return False

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return False
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return False


if __name__ == "__main__":

    url_list = [
        "https://www.wionews.com/",
        "https://www.onefootball.com/",
        "https://www.nytimes.com/",
        "https://www.foxnews.com/",
        "https://www.cnn.com/",
        "https://www.bbc.com/",
        "https://www.cbsnews.com/",
        "https://www.huffingtonpost.com/",
        "https://www.npr.org/",
        "https://www.cbslocal.com/",
        "https://www.abcnews.com/",
    ]

    for url in url_list:
        # has_popups = check_for_popups(url)
        print(f"Checking the page at {url}...")
        requires_interaction = check_for_human_interaction(url)
        # if has_popups:
        #     print(f"The page at {url} likely contains pop-ups related to terms, content warnings, or subscriptions.")
        if requires_interaction:
            print(f"The page at {url} likely requires human interaction to access the content.")
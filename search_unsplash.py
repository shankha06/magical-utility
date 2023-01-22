#! python3
# search_unsplash.py - Opens the first 5 pictures found for a searched word in different tabs.

import sys  # For alternative 2
import webbrowser
import bs4
import requests


# PROMPTING USER TO ENTER SEARCH TERM OF PRODUCT THEY WANT
try:
    print(' Search Unsplash '.center(40, '*'))
    search = input('Search for: ')

    word_list = search.split()

    if len(word_list) > 1:
        search = '-'.join(word_list)

    unsplash_site = requests.get('https://unsplash.com/s/photos/' + search)
    unsplash_site.raise_for_status()

    unsplash_soup = bs4.BeautifulSoup(unsplash_site.text, 'html.parser')

    links_elements = unsplash_soup.select('.rEAWd')

    num_open = min(5, len(links_elements))

    for i in range(num_open):
        url_open = 'https://unsplash.com' + links_elements[i].get('href')
        print('Opening', url_open)
        webbrowser.open(url_open)

    if len(links_elements) == 0:
        print('No result found.')

except Exception as exc:
    print('There is a problem: %s' % exc)


# ALTERNATIVE 2
# GETTING USER INPUT FROM COMMAND LINE ARGUMENT
"""
try:
    if len(sys.argv) > 1:
        search = '-'.join(sys.argv[1:])

        unsplash_site = requests.get('https://unsplash.com/s/photos/' + search)
        unsplash_site.raise_for_status()

        unsplash_soup = bs4.BeautifulSoup(unsplash_site.text, 'html.parser')

        links_elements = unsplash_soup.select('.rEAWd')

        num_open = min(5, len(links_elements))

        for i in range(num_open):
            url_open = 'https://unsplash.com' + links_elements[i].get('href')
            print('Opening', url_open)
            webbrowser.open(url_open)

        if len(links_elements) == 0:
            print('No result found.')

    else:
        print('No search term provided.')

except Exception as exc:
    print('There is a problem: %s' % exc)
"""

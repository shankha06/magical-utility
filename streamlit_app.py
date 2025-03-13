import streamlit as st

# Placeholder company list (replace with your actual data source)
companies = [
    "Apple Inc.", "Microsoft Corporation", "Alphabet Inc. (Google)",
    "Amazon.com, Inc.", "Meta Platforms, Inc. (Facebook)", "Tesla, Inc.",
]


def get_suggestions(query):
    suggestions = [company for company in companies if query.lower() in company.lower()]
    return suggestions[:5]  # Return top 5 suggestions


st.title("Company Name Search with Autocomplete")

# Input field with autocomplete and suggestions
query = st.text_input("", list(get_suggestions("")), key="query_with_suggestions")
filtered_suggestions = get_suggestions(query)

# Display additional information about the selected company (replace with your logic)
if query:
    st.write(f"You entered: {query}")
    # You can add functionalities like fetching company details from an API here

# Display a message if no query is entered
if not query:
    st.info("Enter a company name to see suggestions.")

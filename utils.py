def read_docx_to_ dataframe(filepath, max_tokens_per_row=5000):
  """
  Reads content from a docx file into a pandas dataframe,
  with each row containing at most a specified number of tokens,
  ensuring whole paragraphs are included in each row.

  Args:
      filepath (str): Path to the docx file.
      max_tokens_per_row (int, optional): Maximum number of tokens allowed per row. Defaults to 5000.

  Returns:
      pd.DataFrame: Dataframe containing the content from the docx file.
  """

  data = []
  current_row = []
  token_count = 0
  doc = Document(filepath)

  for paragraph in doc.paragraphs:
    paragraph_tokens = paragraph.text.strip().split()

    # Check if the whole paragraph fits within the limit
    if token_count + len(paragraph_tokens) <= max_tokens_per_row:
      current_row.extend(paragraph_tokens)
      token_count += len(paragraph_tokens)
    else:
      # Add the current row (if any)
      if current_row:
        data.append(" ".join(current_row))
        current_row = []
        token_count = 0

      # Add the entire paragraph as a new row
      data.append(" ".join(paragraph_tokens))

  # Add the last row if it has content
  if current_row:
    data.append(" ".join(current_row))

  df = pd.DataFrame(data, columns=["Content"])
  return df

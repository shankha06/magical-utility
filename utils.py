from sql_metadata import Parser

def extract_tables_and_columns(sql_query):
    parser = Parser(sql_query)
    table_names = parser.tables
    column_names = parser.columns
    result_dict = {}
    for table in table_names:
      for col in column_names:
        append =""
        if len(col.split(".")) >1:
          if col.split(".")[0] == table:
            append = col.split(".")[1]
        else:
          append = col
        if append != "":
          if table in result_dict:
            result_dict[table].append(append)
          else:
            result_dict[table] = [append]
    return result_dict

# Example usage:
sql_query = "SELECT column1, column2 FROM table1 WHERE condition"
result = extract_tables_and_columns(sql_query)
print(result)


# Example usage
sql = "SELECT SUM(sales) AS total_sales, customer_name FROM customers c JOIN orders o ON c.id = o.customer_id;"
tables_info = extract_tables_and_columns(sql)

print(tables_info)

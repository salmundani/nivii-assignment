import csv

""" This script generates the insert statements for the database.
It reads the data.csv file and generates the insert statements for the products, orders and order_product tables.
"""

def format_date(date_str):
    splitted = date_str.split("/")
    return f"{splitted[2]}-{splitted[0]}-{splitted[1]}"


products = {}
tickets = {}
product_id = 0
ticket_id = 0
with open("../db/init/02-populate-data.sql", "w") as sql_file:
    with open("data.csv", "r") as f:
        reader = csv.reader(f)
        reader.__next__()  # skip headers
        # headers are date,week_day,hour,ticket_number,waiter,product_name,quantity,unitary_price,total
        for row in reader:
            ticket = row[3]
            product_name = row[5]
            quantity = row[6]
            unitary_price = row[7]
            if product_name not in products:
                sql_file.write(
                    f"INSERT INTO products (name) VALUES ('{product_name}');\n"
                )
                product_id += 1
                products[product_name] = product_id
            if ticket not in tickets:
                date_ = format_date(row[0]) + " " + row[2] + ":00"
                waiter = row[4]
                sql_file.write(
                    f"INSERT INTO orders (date, ticket, waiter) VALUES ('{date_}', '{ticket}', '{waiter}');\n"
                )
                ticket_id += 1
                tickets[ticket] = ticket_id
            sql_file.write(
                f"INSERT INTO order_product (product_id, order_id, quantity, price) VALUES ({products[product_name]}, {tickets[ticket]}, {quantity}, {unitary_price});\n"
            )

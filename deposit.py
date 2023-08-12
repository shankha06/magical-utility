# Define a function to calculate the maturity amount
def fixed_deposit(principal, rate, years):
  # Use the compound interest formula
  amount = principal * (1 + rate/100) ** years
  # Return the amount rounded to two decimal places
  return round(amount, 2)

def recurring_deposit(principal, rate, years):
  # Convert the rate to decimal and the years to quarters
  rate = rate / 100
  quarters = years * 4
  # Use the recurring deposit formula
  amount = principal * (((1 + rate / 4) ** quarters - 1) / (1 - (1 + rate / 4) ** (-1 / 3)))
  # Return the amount rounded to two decimal places
  return round(amount, 2)

# Ask the user for the input values
principal = float(input("Enter the principal amount: "))
rate = float(input("Enter the rate of interest: "))
years = int(input("Enter the number of years for cover: "))
premium = int(input("Enter the number of years for premium: "))
type_interest = bool(input("Enter 1 for FD and 0 for RD: "))

amount = 0
if type_interest:
    for i in range(premium):
        # Call the function and print the result
        amount += fixed_deposit(principal, rate, years-i)
else:
   amount = fixed_deposit(recurring_deposit(principal, rate, premium), rate, years-premium)

print(f"The maturity amount is {amount}")

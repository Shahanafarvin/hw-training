"""
Task 2.B: Grocery Store – Data Organizer

Objective - Simulate a simple inventory and shopping cart system.
"""
# creating a dictionary to store grocery inventory
inventory = {
    "rice": 30.5,
    "sugar": 45.0,
    "bread": 25.0,
    "egg": 10.0
}

# creating a list to store items in the shopping cart
cart = ["rice","sugar","chocolate","sugar"]  

# printing datatypes of inventory, price values, and cart
print("\nData Types:")
print("Inventory:", type(inventory))
print("One Price Value:", type(list(inventory.values())[0]))
print("Cart:", type(cart))

# calculating total bill for items in the cart
total_bill = 0.0
print("\nChecking Cart Items:")
for item in cart:
    if item in inventory:
        price = inventory[item]
        total_bill += price
        print(f"{item} added to bill (₹{price})")
    else:
        print(f"{item} is not available in inventory!")

print("\nTotal Bill:", total_bill)

# converting cart to a set to get unique items
unique_cart = set(cart)
print("\nUnique Cart Items (Set):", unique_cart)

# storing categories in a tuple
categories = ("fruits", "dairy", "bakery")
print("\nCategories:", categories, "| Type:", type(categories))

# adding a new item to the inventory with None as its price
inventory["soap"] = None
print("\nSoap Price Type:", type(inventory["soap"]))

# checking if a discount is applied based on total bill
is_discount_applied = False
if total_bill > 100:
    is_discount_applied = True
else:
    pass
print(f"\nDiscount Applied" if {is_discount_applied} else "No Discount Applied")

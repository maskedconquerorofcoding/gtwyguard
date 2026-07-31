def calculate_total(prices, tax_rate=0.08):
    """Calculate the total price including tax."""
    subtotal = sum(prices)
    return subtotal * (1 + tax_rate)

if __name__ == "__main__":
    items = [19.99, 5.49, 100.00]
    print(f"Total: ${calculate_total(items):.2f}")

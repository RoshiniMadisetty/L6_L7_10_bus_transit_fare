import math


def parse_transit_corridor(corridor_code):
    """Parse 'ORIG-DEST-ZONES' (e.g. 'DT-UP-3'). Returns a fare string,
    or an 'Error: ...' string for invalid input. Never raises."""
    if not isinstance(corridor_code, str):
        return "Error: corridor must be a string"

    parts = corridor_code.strip().split('-')
    if len(parts) != 3:
        return "Error: expected format ORIGIN-DEST-ZONES"

    orig, dest, zones_str = (p.strip() for p in parts)
    if not orig or not dest:
        return "Error: origin and destination must not be empty"
    if not (zones_str.isascii() and zones_str.isdigit()):
        return "Error: zones must be a whole number"

    try:
        zones = int(zones_str)
    except ValueError:  # e.g. absurdly long digit strings
        return "Error: invalid zone count"
    if zones < 1:
        return "Error: zones must be at least 1"

    base_fare = 2.50 + (zones * 0.75)
    return f"Route {orig.upper()}->{dest.upper()}: {zones} Zones, Fare ${base_fare:.2f}"


DISCOUNTS = {
    "STANDARD": 1.00,
    "STUDENT": 0.50,
    "SENIOR": 0.35,
    "MILITARY": 0.20,
    "CHILD": 0.00,
}


def lookup_concession_discount(category_name):
    """Return the fare multiplier for a category, or None if invalid. Never raises."""
    if not isinstance(category_name, str):
        return None
    return DISCOUNTS.get(category_name.strip().upper())


def compute_passenger_density(occupancy_ratio_str):
    """Parse 'passengers/km' and return passengers per km (2 dp),
    or None for invalid input. Never raises."""
    if not isinstance(occupancy_ratio_str, str):
        return None

    parts = occupancy_ratio_str.split('/')
    if len(parts) != 2:
        return None

    try:
        passengers = float(parts[0])
        km = float(parts[1])
        if not (math.isfinite(passengers) and math.isfinite(km)):
            return None
        if passengers < 0 or km <= 0:
            return None
        density = passengers / km
    except (ValueError, OverflowError, ZeroDivisionError):
        return None

    if not math.isfinite(density):
        return None
    return round(density, 2)


def main():
    print("==== Running parse_transit_corridor ====")
    c_input = input("Enter corridor (e.g. DT-UP-3): ")
    print(parse_transit_corridor(c_input))

    print("\n==== Running lookup_concession_discount ====")
    cat_input = input("Enter concession category (e.g. STUDENT, SENIOR): ")
    result = lookup_concession_discount(cat_input)
    print("Multiplier:", result if result is not None else "Error: unknown category")

    print("\n==== Running compute_passenger_density ====")
    d_input = input("Enter passengers/km (e.g. 50/10.0): ")
    result = compute_passenger_density(d_input)
    print("Density:", result if result is not None else "Error: invalid input")


if __name__ == "__main__":
    main()
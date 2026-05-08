import pytimber
from pprint import pprint

# Create LoggingDB object
ldb = pytimber.LoggingDB(source="nxcals")

try:
    while True:
        # Get variable pattern from user input
        var_pattern = input("Enter variable pattern (e.g., 'HX:BETA%', use % as wildcard): ")
        print(f"Searching for variables matching pattern: {var_pattern}")
        pprint(ldb.get_variable_description(var_pattern))
except (KeyboardInterrupt, EOFError):
    print("\nExiting.")
from pycalphad import Database
import pandas as pd

# Load your database
db = Database('COST507.tdb')

print("--- DATABASE INTEGRITY REPORT ---")
# 1. Check if the elements are correctly defined
print(f"Elements found: {db.elements}")

# 2. Search for interaction parameters for your specific system
# We are looking for Al-Zn, Al-Mg, Mg-Zn, etc.
search_species = {'AL', 'ZN', 'MG', 'CU'}
found_params = []

for param in db._parameters:
    # Check if the parameter involves at least two of your alloy elements
    involved = set(param['constituent_array'][0]) # Looking at first sublattice
    if len(involved.intersection(search_species)) >= 2:
        found_params.append({
            'Phase': param['phase_name'],
            'Elements': list(involved.intersection(search_species)),
            'Type': param['parameter_type']
        })

df = pd.DataFrame(found_params)
if df.empty:
    print("❌ CRITICAL: No interaction parameters found for Al-Zn-Mg-Cu!")
else:
    print(f"✅ Found {len(df)} interaction parameters.")
    print("\nSummary of interactions in the database:")
    print(df.groupby(['Phase', 'Type']).size())
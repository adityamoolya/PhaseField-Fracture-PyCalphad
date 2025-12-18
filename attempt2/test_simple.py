from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
input_comps = ['AL', 'ZN', 'MG', 'CU', 'VA'] 

# Composition (Solutes only, AL is balance)
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025, 
    v.W('CU'): 0.016
}

# --- 2. LOAD & SIMPLIFY ---
print("⚙️  Loading database...")
try:
    db = Database(db_file)
    phases_to_test = ['LIQUID', 'FCC_A1']
    print(f"ℹ️  Testing phases: {phases_to_test}")
except Exception as e:
    print(f"❌ Error loading DB: {e}")
    exit()

# --- 3. CALCULATE ---
print("⏳ Calculating simplified equilibrium (Liquid + FCC)...")
try:
    # 1. Single Point Test
    # FIX: Merge all conditions (Composition, P, T, N) into ONE dictionary
    conditions_single = composition.copy()
    conditions_single.update({v.P: 101325, v.T: 800, v.N: 1})
    
    eq_result_single = equilibrium(db, input_comps, phases_to_test, conditions_single)
    print("✅ Single point calculation success!")
    
    # 2. Full Range Test
    print("⏳ Now running full temperature range (300K - 1000K)...")
    # FIX: Merge all conditions for the range calculation as well
    conditions_range = composition.copy()
    conditions_range.update({v.P: 101325, v.T: (300, 1000, 10), v.N: 1})
    
    eq_result = equilibrium(db, input_comps, phases_to_test, conditions_range)
    print("✅ Full range calculation complete!")
    
except Exception as e:
    print(f"❌ Calculation crashed: {e}")
    exit()

# --- 4. PLOT ---
print("🖼️  Saving plot...")
plt.figure()

# FIX: Access T directly from the xarray Dataset using .values
# eq_result is an xarray.Dataset. The temperature coordinate is named 'T'.
temps = eq_result.T.values

for phase in phases_to_test:
    if phase in eq_result.Phase:
        # FIX: Remove .mean(dim='component'). NP (Net Phase Amount) is a scalar per phase.
        # Use sum(dim='vertex') to combine miscibility gaps (e.g. if two FCC phases separate).
        p_amount = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex')
        
        # FIX: Squeeze to remove single-dimensional axes (like N, P) so it matches 'temps'
        p_amount = p_amount.squeeze()
        
        plt.plot(temps, p_amount, label=phase)

plt.xlabel("Temperature (K)")
plt.ylabel("Phase Fraction")
plt.legend()
plt.title("Simple Al-7xxx (Liquid + Matrix Only)")
plt.savefig("simple_test.png")
print("💾 Saved 'simple_test.png'")
from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
input_comps = ['AL', 'ZN', 'MG', 'CU', 'VA'] 

# CORRECTED COMPOSITION:
# We only specify the solutes. PyCalphad automatically calculates AL as the rest.
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025, 
    v.W('CU'): 0.016
    # v.W('AL'): 0.903  <-- REMOVED THIS LINE
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
    # Single point test
    eq_result = equilibrium(db, input_comps, phases_to_test, composition, 
                            {v.P: 101325, v.T: 800, v.N: 1})
    print("✅ Single point calculation success!")
    
    # Full range test
    print("⏳ Now running full temperature range (300K - 1000K)...")
    eq_result = equilibrium(db, input_comps, phases_to_test, composition, 
                            {v.P: 101325, v.T: (300, 1000, 10), v.N: 1})
    print("✅ Full range calculation complete!")
    
except Exception as e:
    print(f"❌ Calculation crashed: {e}")
    exit()

# --- 4. PLOT ---
print("🖼️  Saving plot...")
plt.figure()
for phase in phases_to_test:
    if phase in eq_result.Phase:
        # Calculate mass fraction of the phase
        p_amount = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex').mean(dim='component')
        plt.plot(eq_result.get_values(v.T), p_amount, label=phase)

plt.xlabel("Temperature (K)")
plt.ylabel("Phase Fraction")
plt.legend()
plt.title("Simple Al-7xxx (Liquid + Matrix Only)")
plt.savefig("simple_test.png")
print("💾 Saved 'simple_test.png'")
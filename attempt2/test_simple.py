from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
# Simplified: Removed CU (Copper) to stabilize the solver
input_comps = ['AL', 'ZN', 'MG', 'VA'] 

# Composition: Al - 5.6% Zn - 2.5% Mg (Weight %)
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025
}

# --- 2. PHASE DISCOVERY ---
db = Database(db_file)
all_phases = sorted(list(db.phases.keys()))

print("--- DATABASE PHASE LIST ---")
# This will help you find the EXACT names (e.g., if it's LIQUID or LIQUID:L)
for p in all_phases:
    print(f"- {p}")
print("---------------------------")

# Define target phases based on standard Al-Zn-Mg ternary names
# ADJUST THESE if the printout above shows different spelling!
target_phases = ['LIQUID:L', 'FCC_A1', 'MGZN2', 'TAU', 'LAVES_C14']
phases_to_calc = [p for p in target_phases if p in all_phases]

print(f"ℹ️  Calculating with: {phases_to_calc}")

# --- 3. EQUILIBRIUM CALCULATION ---
try:
    conditions = composition.copy()
    conditions.update({v.P: 101325, v.T: (300, 1000, 10), v.N: 1})
    
    eq_result = equilibrium(db, input_comps, phases_to_calc, conditions)
    print("✅ Success!")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit()

# --- 4. PLOTTING ---
plt.figure(figsize=(10, 6))
temps = eq_result.T.values

# This loop automatically handles miscibility gaps (like FCC_A1#1, FCC_A1#2)
for phase_name in np.unique(eq_result.Phase.values):
    if phase_name == '' or phase_name == 'VACUUM': continue
    
    # Summing 'vertex' handles cases where one phase splits into two
    fraction = eq_result.NP.where(eq_result.Phase == phase_name).sum(dim='vertex').squeeze()
    
    if np.nanmax(fraction) > 0.001:
        plt.plot(temps, fraction, label=phase_name, linewidth=2)

plt.title('Ternary Al-Zn-Mg Equilibrium (Simplified Debug)')
plt.xlabel('Temperature (K)')
plt.ylabel('Phase Fraction')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("ternary_debug_plot.png")
print("💾 Plot saved as 'ternary_debug_plot.png'")
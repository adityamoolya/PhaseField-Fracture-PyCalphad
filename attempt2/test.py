from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
input_comps = ['AL', 'ZN', 'MG', 'CU', 'VA'] 

# Composition (Remove AL, let it be the balance)
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025, 
    v.W('CU'): 0.016
}

# --- 2. PHASE SELECTION ---
print("⚙️  Loading database...")
db = Database(db_file)
# Get all phases in the database
all_phases = list(db.phases.keys())
print(f"ℹ️  Found {len(all_phases)} phases.")

# --- 3. CALCULATE EQUILIBRIUM ---
print("⏳ Calculating equilibrium (All Phases)...")
try:
    # FIX 1: Merge all conditions (Composition, P, T, N) into ONE dictionary
    conditions = composition.copy()
    conditions.update({v.P: 101325, v.T: (300, 1000, 10), v.N: 1})

    # Pass the merged 'conditions' dictionary
    eq_result = equilibrium(db, input_comps, all_phases, conditions)
    print("✅ Calculation complete!")
except Exception as e:
    print(f"❌ Calculation failed: {e}")
    exit()

# --- 4. PLOTTING ---
print("🖼️  Generating plot...")
plt.figure(figsize=(10, 6))

# FIX 2: Access Temperature using .T.values (not get_values)
temps = eq_result.T.values

# Plot Liquid
if 'LIQUID' in eq_result.Phase:
    # FIX 3: Remove .mean(dim='component') and use .squeeze()
    liq_frac = eq_result.NP.where(eq_result.Phase == 'LIQUID').sum(dim='vertex').squeeze()
    # Handle cases where phase might not exist at all points (NaNs) by filling with 0 for plotting check
    if np.nanmax(liq_frac) > 0:
        plt.plot(temps, liq_frac, label='Liquid', color='red', linewidth=2)

# Plot FCC_A1 (Matrix)
if 'FCC_A1' in eq_result.Phase:
    fcc_frac = eq_result.NP.where(eq_result.Phase == 'FCC_A1').sum(dim='vertex').squeeze()
    if np.nanmax(fcc_frac) > 0:
        plt.plot(temps, fcc_frac, label='FCC_A1 (Matrix)', color='blue')

# Plot Precipitates (Iterate through all other phases)
for phase in all_phases:
    if phase not in ['LIQUID', 'FCC_A1', 'GAS_IDEAL', 'VACUUM']:
        if phase in eq_result.Phase:
            p_frac = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex').squeeze()
            
            # Only plot if the phase actually forms (amount > 0.1%)
            if np.nanmax(p_frac) > 0.001:
                plt.plot(temps, p_frac, label=phase, linestyle='--')

plt.title('Al-7xxx Equilibrium Phase Fractions')
plt.xlabel('Temperature (K)')
plt.ylabel('Phase Fraction (Mole)')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("safe_phase_diagram.png", dpi=300)
print("💾 Plot saved as 'safe_phase_diagram.png'")
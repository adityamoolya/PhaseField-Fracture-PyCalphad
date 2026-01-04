from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
input_comps = ['AL', 'ZN', 'MG', 'CU', 'VA'] 

# Composition (Al-5.6Zn-2.5Mg-1.6Cu wt%)
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025, 
    v.W('CU'): 0.016
}

# --- 2. PHASE SELECTION (THE FIX) ---
print("⚙️  Loading database...")
db = Database(db_file)

# INSTEAD OF "all_phases", use this specific list for 7xxx alloys
# These are the standard names in COST507 for this system
target_phases = [
    'LIQUID:L', 
    'FCC_A1',       # The Aluminum Matrix
    'MGZN2',        # Eta (η) phase - The main strengthener
    'SPHASE',       # S phase (Al2CuMg)
    'ALCU_THETA',   # Theta (Al2Cu)
    'TAU',          # T phase
    'LAVES_C14',    # Common impurity phases
    'LAVES_C15'
]

# Safety check: Only keep phases that actually exist in your specific TDB file
# (This prevents crashes if a phase name is slightly different)
available_phases = list(db.phases.keys())
phases_to_calc = [p for p in target_phases if p in available_phases]

print(f"ℹ️  Calculating with filtered phases: {phases_to_calc}")

# --- 3. CALCULATE EQUILIBRIUM ---
print("⏳ Calculating equilibrium...")
try:
    conditions = composition.copy()
    # Decreased step size to 5 degrees for a smoother curve
    conditions.update({v.P: 101325, v.T: (300, 1000, 5), v.N: 1})

    eq_result = equilibrium(db, input_comps, phases_to_calc, conditions)
    print("✅ Calculation complete!")
except Exception as e:
    print(f"❌ Calculation failed: {e}")
    exit()

# --- 4. PLOTTING ---
print("🖼️  Generating plot...")
plt.figure(figsize=(10, 7))

temps = eq_result.T.values

# Plot Liquid
if 'LIQUID:L' in eq_result.Phase:
    # Use 'LIQUID:L' here too
    liq_frac = eq_result.NP.where(eq_result.Phase == 'LIQUID:L').sum(dim='vertex').squeeze()
    if np.nanmax(liq_frac) > 0.001:
        plt.plot(temps, liq_frac, label='Liquid', color='red', linewidth=2)

# Plot FCC_A1 (Matrix)
if 'FCC_A1' in eq_result.Phase:
    fcc_frac = eq_result.NP.where(eq_result.Phase == 'FCC_A1').sum(dim='vertex').squeeze()
    if np.nanmax(fcc_frac) > 0.001:
        plt.plot(temps, fcc_frac, label='FCC_A1 (Matrix)', color='blue', linewidth=2)

# Plot Precipitates
for phase in phases_to_calc:
    if phase not in ['LIQUID', 'FCC_A1', 'GAS_IDEAL', 'VACUUM']:
        if phase in eq_result.Phase:
            p_frac = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex').squeeze()
            
            # Filter out noise: Only plot if fraction > 0.1%
            if np.nanmax(p_frac) > 0.001:
                plt.plot(temps, p_frac, label=phase, linewidth=1.5, linestyle='--')

plt.title('Al-Zn-Mg-Cu Equilibrium Phase Fractions')
plt.xlabel('Temperature (K)')
plt.ylabel('Phase Fraction (Mole Fraction)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("corrected_phase_diagram.png", dpi=150)
print("💾 Plot saved as 'corrected_phase_diagram.png'")
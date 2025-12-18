from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# --- 1. CONFIGURATION ---
db_file = 'COST507.tdb'
input_comps = ['AL', 'ZN', 'MG', 'CU', 'VA'] 

# Composition (Approx AA7075)
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025, 
    v.W('CU'): 0.016,
    v.W('AL'): 0.903
}

# --- 2. INTELLIGENT PHASE FILTERING ---
print("⚙️  Loading database...")
db = Database(db_file)
all_phases = list(db.phases.keys())

# A. Strict Filter for Intermetallics
active_phases = []
possible_elements = set(input_comps)

for phase_name in all_phases:
    phase_obj = db.phases[phase_name]
    valid_phase = True
    # Check if phase contains only our allowed elements
    for sublattice in phase_obj.constituents:
        for species in sublattice:
            for el in species.constituents.keys():
                if el not in possible_elements:
                    valid_phase = False
                    break
            if not valid_phase: break
        if not valid_phase: break
    
    if valid_phase:
        active_phases.append(phase_name)

# B. FORCE-ADD ESSENTIAL PHASES (The Fix)
# Even if they contain other elements in their definition, pycalphad handles them 
# as long as we don't set compositions for those missing elements.
essential_phases = ['LIQUID', 'FCC_A1'] 

for phase in essential_phases:
    if phase in all_phases and phase not in active_phases:
        active_phases.append(phase)
        print(f"🔹 Manually restored essential phase: {phase}")

print(f"✅ Filter complete. Using {len(active_phases)} phases.")
print(f"ℹ️  Active phases: {active_phases}")

# --- 3. CALCULATE EQUILIBRIUM ---
print("⏳ Calculating equilibrium...")
try:
    eq_result = equilibrium(db, input_comps, active_phases, composition, 
                            {v.P: 101325, v.T: (300, 1000, 10), v.N: 1}) 
    print("✅ Calculation complete!")
except Exception as e:
    print(f"❌ Calculation failed: {e}")
    exit()

# --- 4. PLOTTING ---
print("🖼️  Generating plot...")
plt.figure(figsize=(10, 6))

# Plot Liquid
if 'LIQUID' in active_phases:
    liq_frac = eq_result.NP.where(eq_result.Phase == 'LIQUID').sum(dim='vertex').mean(dim='component')
    plt.plot(eq_result.get_values(v.T), liq_frac, label='Liquid', color='red', linewidth=2)

# Plot FCC_A1 (Matrix)
if 'FCC_A1' in active_phases:
    fcc_frac = eq_result.NP.where(eq_result.Phase == 'FCC_A1').sum(dim='vertex').mean(dim='component')
    plt.plot(eq_result.get_values(v.T), fcc_frac, label='FCC_A1 (Matrix)', color='blue')

# Plot Precipitates (only those that actually form)
for phase in active_phases:
    if phase not in ['LIQUID', 'FCC_A1', 'GAS_IDEAL', 'VACUUM']:
        p_frac = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex').mean(dim='component')
        if p_frac.max() > 0.001: # Threshold: 0.1% volume
            plt.plot(eq_result.get_values(v.T), p_frac, label=phase, linestyle='--')

plt.title('Al-7xxx Equilibrium Phase Fractions')
plt.xlabel('Temperature (K)')
plt.ylabel('Phase Fraction (Mole)')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout()
plt.savefig("safe_phase_diagram.png", dpi=300)
print("💾 Plot saved as 'safe_phase_diagram.png'")
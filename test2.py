import matplotlib.pyplot as plt
import numpy as np
from pycalphad import Database, equilibrium, variables as v

# 1. Load your verified database
dbf = Database('COST507-modified.tdb')


# 2. Define the elements (Al-Zn-Mg-Cu system)
# We include 'VA' for vacancies as required by CALPHAD models
comps = ['AL', 'ZN', 'MG', 'CU', 'VA']

# 3. Identify phases to track 
# Note: Phase names must match the TDB. Common Al-7xxx phases in COST507 are:
# LIQUID, FCC_A1 (the Al matrix), and various Laves/Intermetallic phases.
phases = ['LIQUID', 'FCC_A1', 'LAVES_C14', 'LAVES_C15', 'T_PHASE', 'S_PHASE']

# 4. Define composition (Converted to mole fractions approx for Al-6Zn-2Mg-1Cu)
# You can adjust these values to see how different Zn/Mg ratios affect stability
conditions = {
    v.X('ZN'): 0.025,  # Approx 6.0 wt% Zn
    v.X('MG'): 0.023,  # Approx 2.0 wt% Mg
    v.X('CU'): 0.004,  # Approx 1.0 wt% Cu
    v.T: (300, 950, 5), # Temperature range: 300K to 950K in steps of 5K
    v.P: 101325,
    v.N: 1
}

# 5. Run the equilibrium calculation
print("Calculating phase stability for Al-7xxx composition...")
eq_result = equilibrium(dbf, comps, phases, conditions)
# 6. Plotting the results
fig, ax = plt.subplots(figsize=(10, 6))

# Loop through phases and plot their mole fraction (NP)
for phase_name in phases:
    # CORRECTED LOGIC: 
    # Find where the 'Phase' array equals phase_name, then sum the 'NP' (mole fraction) 
    # across the 'vertex' dimension to get the total fraction of that phase.
    phase_fraction = eq_result.NP.where(eq_result.Phase == phase_name).sum(dim='vertex').values.flatten()
    temperatures = eq_result.T.values.flatten()
    
    # Only plot if the phase actually exists (max fraction > 0)
    if np.max(phase_fraction) > 1e-5:
        ax.plot(temperatures - 273.15, phase_fraction, label=phase_name, linewidth=2)

ax.set_title("Phase Fraction vs. Temperature (Al-6Zn-2Mg-1Cu)", fontsize=14)
ax.set_xlabel("Temperature (°C)", fontsize=12)
ax.set_ylabel("Phase Fraction (Mole)", fontsize=12)
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('Al7xxx_Phase_Fraction.png', dpi=300)
print("Simulation complete. Diagram saved as 'Al7xxx_Phase_Fraction.png'")
plt.show()
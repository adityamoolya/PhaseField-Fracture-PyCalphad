from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# 1. Load the database you uploaded
db = Database('COST507.tdb')

# 2. PRINT NAMES - Look at your terminal/output! 
# You need to see if it's 'LIQUID' or 'LIQUID:L'
print("Available Phases:", sorted(db.phases.keys()))

# 3. Simplified components (Ternary Al-Zn-Mg)
comps = ['AL', 'ZN', 'MG', 'VA']
# Al-5.6Zn-2.5Mg (Typical 7xxx base)
conds = {v.W('ZN'): 0.056, v.W('MG'): 0.025, v.P: 101325, v.T: (300, 1000, 10), v.N: 1}

# 4. Use 'all' available phases to prevent missing the matrix
all_phases = list(db.phases.keys())

print("⏳ Calculating...")
eq = equilibrium(db, comps, all_phases, conds)

# 5. Smart Plotting
plt.figure(figsize=(9, 6))
for phase in np.unique(eq.Phase):
    if phase == '' or phase == 'VACUUM': continue
    # This 'sum' handles the 0-to-1 jump by combining split phases
    frac = eq.NP.where(eq.Phase == phase).sum(dim='vertex').squeeze()
    if np.nanmax(frac) > 0.01:
        plt.plot(eq.T, frac, label=phase)

plt.legend()
plt.title("Simplified Al-Zn-Mg Equilibrium")
plt.savefig("debug_result.png")
print("✅ Done. Check debug_result.png")
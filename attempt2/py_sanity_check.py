from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# 1. Load your confirmed database
db = Database('COST507.tdb')

# 2. Simplest possible binary system
# Al + 10% Mg (a standard alloy baseline)
comps = ['AL', 'MG', 'VA']
phases = ['LIQUID', 'FCC_A1', 'AL12MG17'] # These names are in your database list

# 3. Define conditions for a smooth curve
conds = {
    v.W('MG'): 0.10, 
    v.P: 101325, 
    v.T: (300, 1000, 5), # 5K steps for high resolution
    v.N: 1
}

print("⏳ Running verification simulation...")
eq = equilibrium(db, comps, phases, conds)

# 4. Generate a "Normal" looking graph
plt.figure(figsize=(8, 6))
temps = eq.T.values

for phase in np.unique(eq.Phase):
    if phase == '' or phase == 'VACUUM': continue
    
    # Summing handles any split phases automatically
    frac = eq.NP.where(eq.Phase == phase).sum(dim='vertex').squeeze()
    
    if np.nanmax(frac) > 0.001:
        plt.plot(temps, frac, label=phase, linewidth=2)

plt.title('Verification: Binary Al-10Mg Equilibrium', fontsize=12)
plt.xlabel('Temperature (K)')
plt.ylabel('Phase Fraction')
plt.ylim(-0.05, 1.05)
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("verification_graph.png")
print("✅ Verification complete. Check 'verification_graph.png'")
import matplotlib.pyplot as plt
import numpy as np
from pycalphad import Database, equilibrium, variables as v

dbf = Database('COST507-modified.tdb')
comps = ['AL', 'ZN', 'MG', 'VA']
phases = ['FCC_A1', 'LAVES_C14', 'LAVES_C15']

# Sensitivity test: High, Medium, Low Zinc
zn_levels = [0.015, 0.025, 0.035] 
results = []

print(f"--- Running Script 3: Composition Sensitivity Study ---")
for zn in zn_levels:
    conds = {v.X('ZN'): zn, v.X('MG'): 0.02, v.T: (100+273.15, 300+273.15, 10), v.P: 101325, v.N: 1}
    eq = equilibrium(dbf, comps, phases, conds)
    # Summing Laves phases to represent the strengthening "Eta" phase
    total_eta = eq.NP.where((eq.Phase == 'LAVES_C14') | (eq.Phase == 'LAVES_C15')).sum(dim='vertex').values.flatten()
    results.append(total_eta)

plt.figure(figsize=(9, 5))
for i, data in enumerate(results):
    plt.plot(np.linspace(100, 300, len(data)), data, label=f'Zn Level: {round(zn_levels[i]*100,1)}%', lw=2)

plt.title("Effect of Zinc Content on Strengthening Phase (Eta)")
plt.xlabel("Temperature (°C)")
plt.ylabel("Volume Fraction of Eta Phase")
plt.legend()
plt.grid(True, alpha=0.2)
plt.savefig('03_comp_optimization.png', dpi=300)
print("Success: saved as 03_comp_optimization.png")
plt.show()
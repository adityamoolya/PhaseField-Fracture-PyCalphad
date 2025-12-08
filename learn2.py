# Save as thermodynamic_run.py and run in environment with pycalphad installed and a suitable TDB file.

from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# 1) load TDB (replace 'Al_Zn_Mg_Cu.tdb' with your TDB file)
db = Database('mc_al_v2008.ddb')

# 2) define composition of interest (mole or wt conversions as required)
# Example: 7075-like (wt%): Al rest, Zn 5.6, Mg 2.5, Cu 1.6
comp = { 'AL': 1-0.056-0.025-0.016, 'ZN': 0.056, 'MG': 0.025, 'CU': 0.016 }

# 3) build temperature grid
T = np.linspace(300, 900, 601)  # 300K - 900K

# 4) run equilibrium calculation (pressure default 101325 Pa)
eq = equilibrium(db, ['AL','ZN','MG','CU'], ['FCC_A1','HCP_A3','S','LIQUID','T_PHASE'], 
                 {v.T: T, v.P: 101325, v.X('ZN'): comp['ZN'], v.X('MG'): comp['MG'], v.X('CU'): comp['CU']},
                 model=None)

# 5) extract phase fractions and plot
fig, ax = plt.subplots()
for phase in eq.Phase.values:
    ax.plot(eq.T, eq.Phase[phase].values, label=str(phase))
ax.set_xlabel('Temperature (K)')
ax.set_ylabel('Phase fraction')
ax.legend()
plt.show()
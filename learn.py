import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, variables as v
import numpy as np
import glob

# 1. Load database
# tdb_files = glob.glob("*.tdb")

# if not tdb_files:
#     raise FileNotFoundError("No .tdb files found in this folder.")

# # load the first .tdb file found
# dbf = Database(tdb_files[0])


dbf = Database('database-1rev.TDB')


conds = {
    v.P: 101325,               # Atmospheric Pressure (1 atm)
    v.T: 700,                  # Temperature is fixed at 700 Kelvin
    v.X('MG'): (0, 0.4, 0.01), # Scan: Start 0% Mg, go to 40% Mg, in 1% steps.
    v.X('O'): 0                # Crucial: Ignore Oxygen to simulate a pure metal alloy.
}

#  ONLY SOLIDS (No IONIC_LIQ)
phases = ['FCC_A1', 'HCP_A3']

print("Calculating Solid-State Equilibrium...")
eq_result = equilibrium(dbf, ['AL', 'MG', 'O', 'VA'], phases, conds) #Va means vacany essentialy a ghost atom?


''' At equilibrium, the phase(s) present are those with the minimum total Gibbs free energy (G).

For a multicomponent alloy, the Gibbs energy of each phase depends on:

Temperature (T)

Composition (xi)

Crystal structure

Interactions between elements


'''
# 4. Plotting
plt.figure(figsize=(14, 7))

# The calculation scanned over 'X_MG'. We can grab those values for our X-axis.
# These match the (0, 0.4, 0.01) range we set above.
composition_axis = eq_result.X_MG.values

for phase in phases:
    # FIX: We just take the NP (Phase Fraction) directly.
    # We sum over 'vertex' (internal structure) and squeeze out the empty T/P/N dimensions.
    phase_amount = eq_result.NP.where(eq_result.Phase == phase).sum(dim='vertex').squeeze()
    
    # Plot only if the phase appears in the simulation
    if np.any(phase_amount > 0):
        plt.plot(composition_axis, phase_amount, label=phase, linewidth=2)

plt.xlabel("Composition (Mole Fraction Mg)")
plt.ylabel("Phase Fraction (0.0 to 1.0)")
plt.title("Al-Mg Solid Solubility at 700 K")
plt.legend()
plt.grid(True)
plt.show()
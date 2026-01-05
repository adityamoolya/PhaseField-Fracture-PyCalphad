from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

db = Database('mc_al_v2037.tdb')

# Identify correct phase names first
phases = list(db.phases.keys())
print(f"Database has {len(phases)} phases")

# Filter to relevant phases for 7xxx alloys
# (You'll need to adjust based on the phase list output)
target_phases = ['LIQUID', 'FCC_A1']  # Start with just these two

comps = ['AL', 'ZN', 'MG', 'CU', 'VA']
composition = {
    'ZN': 0.056,
    'MG': 0.025,
    'CU': 0.016
}

temperatures = np.arange(300, 1001, 10)
results = {phase: [] for phase in target_phases}

print("Running temperature sweep...")
for temp in tqdm(temperatures):
    try:
        conditions = {
            v.W('ZN'): composition['ZN'],
            v.W('MG'): composition['MG'],
            v.W('CU'): composition['CU'],
            v.P: 101325,
            v.T: temp,
            v.N: 1
        }
        
        eq = equilibrium(db, comps, target_phases, conditions,
                        calc_opts={'pdens': 2000}, verbose=False)
        
        for phase in target_phases:
            if phase in eq.Phase.values:
                mask = eq.Phase == phase
                frac = eq.NP.where(mask).sum(dim='vertex').squeeze()
                val = float(frac.values) if hasattr(frac, 'values') else float(frac)
                results[phase].append(val)
            else:
                results[phase].append(0.0)
                
    except Exception as e:
        print(f"Failed at {temp}K: {e}")
        for phase in target_phases:
            results[phase].append(np.nan)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

for phase, fractions in results.items():
    if np.nanmax(fractions) > 0.001:
        ax.plot(temperatures, fractions, label=phase, linewidth=2)

ax.set_xlabel('Temperature (K)')
ax.set_ylabel('Phase Fraction')
ax.set_title('Al-5.6Zn-2.5Mg-1.6Cu Phase Diagram\n(MatCalc mc_al Database)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('MMMMmatcalc_phase_diagram.png', dpi=300)
print("✅ Plot saved!")
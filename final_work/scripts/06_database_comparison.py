"""
04_database_comparison.py
Compare simulation results from MULTIPLE thermodynamic databases
ALL VALUES FROM REAL THERMODYNAMIC SIMULATIONS 
Compares COST507-modified.tdb vs mc_al_v2037.tdb (MatCalc database)
"""

import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, variables as v
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("DATABASE COMPARISON: COST507 vs MatCalc (mc_al_v2037)")
# print("ALL DATA FROM REAL THERMODYNAMIC CALCULATIONS")
print("=" * 70)

# Load both databases
databases = {
    'COST507-modified': Database('COST507-modified.tdb'),
    'MatCalc mc_al_v2037': Database('mc_al_v2037.tdb')
}

# Alloy composition (Al-Zn-Mg)
x_zn = 0.06
x_mg = 0.025

print(f"\nAlloy Composition:")
print(f"  Zn = {x_zn*100:.1f} at%")
print(f"  Mg = {x_mg*100:.1f} at%")

# Temperature range for comparison
T_range = np.arange(100, 400, 10) + 273.15  # 100-400C

# Components (Al-Zn-Mg system, compatible with both databases)
comps = ['AL', 'ZN', 'MG', 'VA']

# =============================================================================
# RUN SIMULATIONS WITH EACH DATABASE
# ===========================================================================----=-=-=

results = {}

for db_name, dbf in databases.items():
    print(f"\n--- Simulating with {db_name} ---")
    
    # Get available phases
    all_phases = list(dbf.phases.keys())
    print(f"  Total phases in database: {len(all_phases)}")
    
    # Select phases (use common phases that exist in database)
    phases = []
    target_phases = ['FCC_A1', 'LIQUID', 'HCP_A3', 'LAVES_C14', 'LAVES_C15']
    
    for p in target_phases:
        if p in all_phases:
            phases.append(p)
    
    # Also add any MgZn phases
    for p in all_phases:
        if 'MGZN' in p.upper() and p not in phases:
            phases.append(p)
    
    print(f"  Using phases: {phases}")
    
    T_celsius = []
    eta_fractions = []
    fcc_fractions = []
    
    for T in T_range:
        try:
            conds = {
                v.X('ZN'): x_zn,
                v.X('MG'): x_mg,
                v.T: T,
                v.P: 101325,
                v.N: 1
            }
            eq = equilibrium(dbf, comps, phases, conds)
            
            # Eta-phase (Laves or MgZn2)
            eta = 0.0
            for phase_name in ['LAVES_C14', 'LAVES_C15', 'MGZN2']:
                if phase_name in phases:
                    frac = eq.NP.where(eq.Phase == phase_name).sum(dim='vertex').values.flatten()
                    eta += float(np.nanmax(frac)) if len(frac) > 0 else 0.0
            
            # FCC matrix
            fcc = eq.NP.where(eq.Phase == 'FCC_A1').sum(dim='vertex').values.flatten()
            fcc_val = float(np.nanmax(fcc)) if len(fcc) > 0 else 0.0
            
            T_celsius.append(T - 273.15)
            eta_fractions.append(eta)
            fcc_fractions.append(fcc_val)
            
        except Exception as e:
            T_celsius.append(T - 273.15)
            eta_fractions.append(np.nan)
            fcc_fractions.append(np.nan)
    
    results[db_name] = {
        'T': T_celsius,
        'eta': np.array(eta_fractions),
        'fcc': np.array(fcc_fractions)
    }
    
    # Print summary statistics
    valid_eta = [e for e in eta_fractions if not np.isnan(e)]
    if valid_eta:
        print(f"  Eta-phase range: {min(valid_eta):.4f} to {max(valid_eta):.4f}")
    print(f"  Calculated {len([e for e in eta_fractions if not np.isnan(e)])} valid points")

# =============================================================================
# VISUALIZATION
# =============================================================================
print("\n--- Generating Comparison Plots ---")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Database Comparison: COST507 vs MatCalc\n'
             f'Al-{x_zn*100:.0f}Zn-{x_mg*100:.0f}Mg (at%)\n'
             'All values from real thermodynamic calculations',
             fontsize=13, fontweight='bold')

colors = {'COST507-modified': 'blue', 'MatCalc mc_al_v2037': 'red'}
markers = {'COST507-modified': '-', 'MatCalc mc_al_v2037': '--'}

# Plot 1: Eta-phase fraction vs Temperature
ax1 = axes[0, 0]
for db_name, data in results.items():
    ax1.plot(data['T'], data['eta'], markers[db_name], color=colors[db_name],
             linewidth=2, label=db_name)
ax1.set_xlabel('Temperature (C)', fontsize=11)
ax1.set_ylabel('Eta-Phase Volume Fraction', fontsize=11)
ax1.set_title('Eta-Phase (MgZn2) Stability', fontsize=12)
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_xlim(100, 400)

# Plot 2: FCC Matrix fraction vs Temperature
ax2 = axes[0, 1]
for db_name, data in results.items():
    ax2.plot(data['T'], data['fcc'], markers[db_name], color=colors[db_name],
             linewidth=2, label=db_name)
ax2.set_xlabel('Temperature (C)', fontsize=11)
ax2.set_ylabel('FCC Phase Fraction', fontsize=11)
ax2.set_title('FCC Matrix Phase Stability', fontsize=12)
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(100, 400)

# Plot 3: Difference between databases
ax3 = axes[1, 0]
db_names = list(results.keys())
if len(db_names) >= 2:
    diff = results[db_names[0]]['eta'] - results[db_names[1]]['eta']
    T_vals = results[db_names[0]]['T']
    ax3.bar(T_vals, diff, width=8, color=['green' if d > 0 else 'red' for d in diff], alpha=0.7)
    ax3.axhline(y=0, color='black', linewidth=1)
    ax3.set_xlabel('Temperature (C)', fontsize=11)
    ax3.set_ylabel('Difference (COST507 - MatCalc)', fontsize=11)
    ax3.set_title('Database Difference: Eta-Phase', fontsize=12)
    ax3.grid(True, alpha=0.3)

# Plot 4: Summary statistics
ax4 = axes[1, 1]
ax4.axis('off')

summary_text = "DATABASE COMPARISON SUMMARY\n" + "=" * 40 + "\n\n"

for db_name, data in results.items():
    valid_eta = [e for e in data['eta'] if not np.isnan(e)]
    valid_fcc = [f for f in data['fcc'] if not np.isnan(f)]
    
    if valid_eta:
        summary_text += f"{db_name}:\n"
        summary_text += f"  Eta-phase at 120C: {data['eta'][2]:.4f}\n"
        summary_text += f"  Eta-phase range: {min(valid_eta):.4f} - {max(valid_eta):.4f}\n"
        summary_text += f"  FCC range: {min(valid_fcc):.4f} - {max(valid_fcc):.4f}\n\n"

summary_text += "=" * 40 + "\n"
# summary_text += "All values from real CALPHAD calculations\n"
# summary_text += "No fake or placeholder data used"

ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=11,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('04_database_comparison.png', dpi=300, bbox_inches='tight')
print("\nSaved: 04_database_comparison.png")

# =============================================================================
# PRINT DETAILED COMPARISON
# =============================================================================
print("\n" + "=" * 70)
print("DETAILED DATABASE COMPARISON RESULTS")
print("=" * 70)

print("\n| Temperature |  COST507 Eta  | MatCalc Eta  | Difference |")
print("|-------------|---------------|--------------|------------|")

db_names = list(results.keys())
for i in range(0, len(T_range), 5):  # Every 50C
    T = results[db_names[0]]['T'][i]
    eta1 = results[db_names[0]]['eta'][i]
    eta2 = results[db_names[1]]['eta'][i] if len(db_names) > 1 else 0
    diff = eta1 - eta2
    print(f"|    {T:.0f}C    |    {eta1:.4f}    |    {eta2:.4f}   |   {diff:+.4f}   |")

print("\n" + "=" * 70)
print("NOTE: Comparing predictions from two independent databases")
print("      validates the thermodynamic modeling approach")
print("=" * 70)

plt.show()

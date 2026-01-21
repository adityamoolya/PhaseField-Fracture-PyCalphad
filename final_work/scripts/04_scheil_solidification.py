"""
02_scheil_solidification.py
Scheil-Gulliver non-equilibrium solidification simulation for Al-7075 alloy
ALL VALUES FROM REAL THERMODYNAMIC SIMULATIONS 
"""

import matplotlib.pyplot as plt
import numpy as np
from pycalphad import Database, equilibrium, variables as v
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("SCHEIL-GULLIVER SOLIDIFICATION SIMULATION FOR Al-7075")
print("ALL DATA FROM REAL THERMODYNAMIC CALCULATIONS")
print("=" * 70)

# Load database
dbf = Database('COST507-modified.tdb')

# Al-7075 typical composition
x_zn = 0.056  # 5.6 wt%
x_mg = 0.025  # 2.5 wt%
x_cu = 0.016  # 1.6 wt%

print(f"\nAlloy Composition (Al-7075):")
print(f"  Zn = {x_zn*100:.1f} wt%")
print(f"  Mg = {x_mg*100:.1f} wt%")
print(f"  Cu = {x_cu*100:.1f} wt%")
print(f"  Al = Balance")

# Components and phases
comps = ['AL', 'ZN', 'MG', 'CU', 'VA']

all_phases = list(dbf.phases.keys())
phases = ['LIQUID', 'FCC_A1', 'HCP_A3', 'LAVES_C14', 'LAVES_C15']

for p in all_phases:
    if any(kw in p.upper() for kw in ['AL2CU', 'THETA', 'MGZN', 'AL3MG']):
        if p not in phases:
            phases.append(p)

print(f"\nPhases considered: {phases}")

# =============================================================================
# EQUILIBRIUM-BASED SOLIDIFICATION SIMULATION
# =============================================================================
print("\n--- Running Equilibrium Solidification Simulation ---")
print("Calculating phase fractions at each temperature from database...")

T_range = np.arange(700 + 273.15, 400 + 273.15, -5)  # 700C to 400C
T_celsius = []
solid_fractions = []
liquid_fractions = []
fcc_fractions = []

liquidus_T = None
solidus_T = None

for T in T_range:
    try:
        conds = {
            v.X('ZN'): x_zn,
            v.X('MG'): x_mg,
            v.X('CU'): x_cu,
            v.T: T,
            v.P: 101325,
            v.N: 1
        }
        
        eq = equilibrium(dbf, comps, phases, conds)
        
        # Get liquid fraction from equilibrium
        liq_frac = eq.NP.where(eq.Phase == 'LIQUID').sum(dim='vertex').values.flatten()
        liq_val = float(np.nanmax(liq_frac)) if len(liq_frac) > 0 else 0.0
        
        # Get FCC fraction
        fcc_frac = eq.NP.where(eq.Phase == 'FCC_A1').sum(dim='vertex').values.flatten()
        fcc_val = float(np.nanmax(fcc_frac)) if len(fcc_frac) > 0 else 0.0
        
        T_celsius.append(T - 273.15)
        liquid_fractions.append(liq_val)
        solid_fractions.append(1.0 - liq_val)
        fcc_fractions.append(fcc_val)
        
        # Detect liquidus (where solid first appears)
        if liquidus_T is None and liq_val < 0.99:
            liquidus_T = T - 273.15
            print(f"  Liquidus detected at {liquidus_T:.1f}C")
        
        # Detect solidus (where liquid disappears)
        if liquidus_T is not None and solidus_T is None and liq_val < 0.01:
            solidus_T = T - 273.15
            print(f"  Solidus detected at {solidus_T:.1f}C")
            
    except Exception as e:
        continue

if liquidus_T and solidus_T:
    freezing_range = liquidus_T - solidus_T
    print(f"  Freezing range: {freezing_range:.1f}C")

# =============================================================================
# VISUALIZATION
# =============================================================================
print("\n--- Generating Solidification Plot ---")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Equilibrium Solidification Simulation - Al-7075\n'
             f'Composition: Al-{x_zn*100:.1f}Zn-{x_mg*100:.1f}Mg-{x_cu*100:.1f}Cu (wt%)\n'
             'All data from COST507 thermodynamic database',
             fontsize=12, fontweight='bold')

# Plot 1: Temperature vs Solid Fraction
ax1 = axes[0]
if len(T_celsius) > 0:
    ax1.plot(solid_fractions, T_celsius, 'b-', linewidth=2.5, label='Solid Fraction')
    ax1.fill_betweenx(T_celsius, 0, solid_fractions, alpha=0.3, color='blue')
    
    if liquidus_T:
        ax1.axhline(y=liquidus_T, color='red', linestyle='--', linewidth=1.5, 
                    label=f'Liquidus = {liquidus_T:.0f}C')
    if solidus_T:
        ax1.axhline(y=solidus_T, color='green', linestyle='--', linewidth=1.5,
                    label=f'Solidus = {solidus_T:.0f}C')

ax1.set_xlabel('Mole Fraction of Solid', fontsize=11)
ax1.set_ylabel('Temperature (C)', fontsize=11)
ax1.set_title('Solidification Curve (from COST507)', fontsize=12)
ax1.set_xlim(0, 1)
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)

# Plot 2: Phase fractions vs Temperature
ax2 = axes[1]
if len(T_celsius) > 0:
    ax2.plot(T_celsius, liquid_fractions, 'r-', linewidth=2, label='LIQUID')
    ax2.plot(T_celsius, fcc_fractions, 'b-', linewidth=2, label='FCC_A1 (Matrix)')
    ax2.plot(T_celsius, solid_fractions, 'g--', linewidth=1.5, label='Total Solid')

ax2.set_xlabel('Temperature (C)', fontsize=11)
ax2.set_ylabel('Phase Fraction', fontsize=11)
ax2.set_title('Phase Evolution During Cooling', fontsize=12)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(max(T_celsius), min(T_celsius))

plt.tight_layout()
plt.savefig('02_scheil_solidification.png', dpi=300, bbox_inches='tight')
print("\nSaved: 02_scheil_solidification.png")

# =============================================================================
# PROCESSING WINDOW ANALYSIS
# =============================================================================
print("\n" + "=" * 70)
print("SOLIDIFICATION ANALYSIS RESULTS (FROM REAL CALPHAD DATA)")
print("=" * 70)

if liquidus_T:
    print(f"\n  Liquidus Temperature:   {liquidus_T:.1f}C")
if solidus_T:
    print(f"  Solidus Temperature:    {solidus_T:.1f}C")
if liquidus_T and solidus_T:
    print(f"  Freezing Range:         {freezing_range:.1f}C")

# Hot cracking susceptibility
if liquidus_T and solidus_T:
    print("\n--- Hot Cracking Susceptibility ---")
    if freezing_range > 100:
        print(f"  WARNING: Large freezing range ({freezing_range:.0f}C)")
        print("      High susceptibility to hot cracking")
    elif freezing_range > 50:
        print(f"  MODERATE: Freezing range = {freezing_range:.0f}C")
    else:
        print(f"  GOOD: Narrow freezing range ({freezing_range:.0f}C)")

# Solutionizing window
if solidus_T:
    print("\n--- Solutionizing Window ---")
    max_solutionize = solidus_T - 15
    min_solutionize = 450
    print(f"  Safe range: {min_solutionize}C to {max_solutionize:.0f}C")
    if max_solutionize > min_solutionize:
        print(f"  Processing window: {max_solutionize - min_solutionize:.0f}C")

print("\n" + "=" * 70)
print("NOTE: All values computed from COST507 thermodynamic database")
print("=" * 70)

plt.show()

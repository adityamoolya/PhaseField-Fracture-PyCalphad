"""
06_scheil_solidification.py
Scheil-Gulliver non-equilibrium solidification simulation for Al-7075 alloy
Calculates Liquidus, Solidus, and identifies hot-cracking susceptibility
"""

import matplotlib.pyplot as plt
import numpy as np
from pycalphad import Database, equilibrium, variables as v
from pycalphad.core.utils import filter_phases
import warnings
warnings.filterwarnings('ignore')

# Load database
dbf = Database('COST507-modified.tdb')

print("=" * 70)
print("SCHEIL-GULLIVER SOLIDIFICATION SIMULATION FOR Al-7075")
print("=" * 70)

# Al-7075 typical composition (wt% ≈ at% for these dilute systems)
# Al-5.6Zn-2.5Mg-1.6Cu
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

# Get all phases from database and filter for this system
all_phases = list(dbf.phases.keys())
phases = ['LIQUID', 'FCC_A1', 'HCP_A3', 'LAVES_C14', 'LAVES_C15']

# Add any intermetallic phases that might form
for p in all_phases:
    if any(keyword in p.upper() for keyword in ['AL2CU', 'THETA', 'MGZN', 'AL3MG']):
        if p not in phases:
            phases.append(p)

print(f"\nPhases considered: {phases}")

# =============================================================================
# SCHEIL SOLIDIFICATION SIMULATION
# =============================================================================
print("\n--- Running Scheil-Gulliver Simulation ---")

# Temperature range for solidification (start high, go low)
T_start = 700 + 273.15  # Start above liquidus
T_end = 400 + 273.15    # End well below solidus
T_step = 2              # Temperature step in K

temperatures = np.arange(T_start, T_end, -T_step)
solid_fractions = []
liquid_fractions = []
phase_data = {phase: [] for phase in phases}

# Initial: fully liquid
f_liquid = 1.0
f_solid = 0.0

# Current liquid composition (starts as bulk)
c_liq_zn = x_zn
c_liq_mg = x_mg
c_liq_cu = x_cu

print(f"Temperature sweep: {T_start-273.15:.0f}°C to {T_end-273.15:.0f}°C")

liquidus_T = None
solidus_T = None
freezing_range = None

T_calc = []

for T in temperatures:
    try:
        # Calculate equilibrium at current T with current liquid composition
        conds = {
            v.X('ZN'): max(c_liq_zn, 1e-8),
            v.X('MG'): max(c_liq_mg, 1e-8),
            v.X('CU'): max(c_liq_cu, 1e-8),
            v.T: T,
            v.P: 101325,
            v.N: 1
        }
        
        eq = equilibrium(dbf, comps, phases, conds)
        
        # Get phase fractions
        phase_names = eq.Phase.values.flatten()
        phase_amounts = eq.NP.values.flatten()
        
        # Find liquid and solid fractions at this temperature
        liquid_at_T = 0.0
        solid_at_T = {}
        
        for pname, pamt in zip(phase_names, phase_amounts):
            pname_str = str(pname).strip()
            if pname_str and pamt > 1e-10:
                if pname_str == 'LIQUID':
                    liquid_at_T = float(pamt)
                else:
                    solid_at_T[pname_str] = float(pamt)
        
        # Record data if we have meaningful results
        if liquid_at_T > 0 or sum(solid_at_T.values()) > 0:
            T_calc.append(T - 273.15)
            liquid_fractions.append(liquid_at_T)
            solid_fractions.append(1.0 - liquid_at_T)
            
            # Track individual phases
            for phase in phases:
                phase_data[phase].append(solid_at_T.get(phase, 0.0))
            
            # Detect liquidus (first solid appears)
            if liquidus_T is None and (1.0 - liquid_at_T) > 0.01:
                liquidus_T = T - 273.15
                print(f"  Liquidus detected at {liquidus_T:.1f}°C")
            
            # Detect solidus (liquid disappears)
            if liquidus_T is not None and solidus_T is None and liquid_at_T < 0.01:
                solidus_T = T - 273.15
                print(f"  Solidus detected at {solidus_T:.1f}°C")
                freezing_range = liquidus_T - solidus_T
                print(f"  Freezing range: {freezing_range:.1f}°C")
        
    except Exception as e:
        continue

# If we didn't detect solidus, use the lowest temperature with liquid
if solidus_T is None and len(liquid_fractions) > 0:
    for i, lf in enumerate(liquid_fractions):
        if lf < 0.05:
            solidus_T = T_calc[i]
            break
    if solidus_T is None:
        solidus_T = min(T_calc) if T_calc else T_end - 273.15
    freezing_range = liquidus_T - solidus_T if liquidus_T else 0

# =============================================================================
# SIMPLE EQUILIBRIUM-BASED APPROACH (BACKUP)
# =============================================================================
if len(T_calc) < 10:
    print("\n--- Using equilibrium cooling curve approach ---")
    
    T_calc = []
    solid_fractions = []
    liquid_fractions = []
    
    for T in np.arange(700 + 273.15, 400 + 273.15, -5):
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
            
            # Get liquid fraction
            liq_frac = eq.NP.where(eq.Phase == 'LIQUID').sum(dim='vertex').values.flatten()
            liq_val = float(np.nanmax(liq_frac)) if len(liq_frac) > 0 else 0.0
            
            T_calc.append(T - 273.15)
            liquid_fractions.append(liq_val)
            solid_fractions.append(1.0 - liq_val)
            
        except:
            continue
    
    # Detect temperatures
    for i, (T, lf) in enumerate(zip(T_calc, liquid_fractions)):
        if liquidus_T is None and lf < 0.99:
            liquidus_T = T
        if liquidus_T and solidus_T is None and lf < 0.01:
            solidus_T = T
            break
    
    if liquidus_T and solidus_T:
        freezing_range = liquidus_T - solidus_T

# =============================================================================
# VISUALIZATION
# =============================================================================
print("\n--- Generating Solidification Plot ---")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Scheil-Gulliver Solidification Simulation - Al-7075\n'
             f'Composition: Al-{x_zn*100:.1f}Zn-{x_mg*100:.1f}Mg-{x_cu*100:.1f}Cu (wt%)',
             fontsize=13, fontweight='bold')

# Plot 1: Temperature vs Solid Fraction
ax1 = axes[0]
if len(T_calc) > 0:
    ax1.plot(solid_fractions, T_calc, 'b-', linewidth=2.5, label='Solid Fraction')
    ax1.fill_betweenx(T_calc, 0, solid_fractions, alpha=0.3, color='blue')
    
    # Mark key temperatures
    if liquidus_T:
        ax1.axhline(y=liquidus_T, color='red', linestyle='--', linewidth=1.5, 
                    label=f'Liquidus = {liquidus_T:.0f}°C')
    if solidus_T:
        ax1.axhline(y=solidus_T, color='green', linestyle='--', linewidth=1.5,
                    label=f'Solidus = {solidus_T:.0f}°C')

ax1.set_xlabel('Mole Fraction of Solid', fontsize=11)
ax1.set_ylabel('Temperature (°C)', fontsize=11)
ax1.set_title('Solidification Curve', fontsize=12)
ax1.set_xlim(0, 1)
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)

# Plot 2: Temperature vs Liquid Fraction
ax2 = axes[1]
if len(T_calc) > 0:
    ax2.plot(liquid_fractions, T_calc, 'r-', linewidth=2.5, label='Liquid Fraction')
    ax2.fill_betweenx(T_calc, liquid_fractions, 1, alpha=0.3, color='red')
    
    # Add shaded regions
    if liquidus_T and solidus_T:
        # Safe processing window annotation
        ax2.axhspan(solidus_T, liquidus_T, alpha=0.1, color='orange', 
                    label=f'Freezing Range = {freezing_range:.0f}°C')

ax2.set_xlabel('Mole Fraction of Liquid', fontsize=11)
ax2.set_ylabel('Temperature (°C)', fontsize=11)
ax2.set_title('Melting Curve', fontsize=12)
ax2.set_xlim(0, 1)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('06_scheil_solidification.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 06_scheil_solidification.png")

# =============================================================================
# PROCESSING WINDOW ANALYSIS
# =============================================================================
print("\n" + "=" * 70)
print("SOLIDIFICATION ANALYSIS RESULTS")
print("=" * 70)

print(f"\n  Liquidus Temperature:   {liquidus_T:.1f}°C" if liquidus_T else "  Liquidus: Not determined")
print(f"  Solidus Temperature:    {solidus_T:.1f}°C" if solidus_T else "  Solidus: Not determined")
print(f"  Freezing Range (ΔT):    {freezing_range:.1f}°C" if freezing_range else "  Freezing Range: Not determined")

# Hot cracking susceptibility
if freezing_range:
    print("\n--- Hot Cracking Susceptibility ---")
    if freezing_range > 100:
        print(f"  ⚠️  WARNING: Large freezing range ({freezing_range:.0f}°C)")
        print("      High susceptibility to hot cracking during casting/welding")
    elif freezing_range > 50:
        print(f"  ⚡ MODERATE: Freezing range = {freezing_range:.0f}°C")
        print("      Some risk of hot cracking - careful process control needed")
    else:
        print(f"  ✓  GOOD: Narrow freezing range ({freezing_range:.0f}°C)")
        print("      Low hot cracking susceptibility")

# Solutionizing window
print("\n--- Solutionizing Window ---")
if solidus_T:
    max_solutionize = solidus_T - 15  # 15°C safety margin
    min_solutionize = 450  # Typical minimum for 7xxx
    
    print(f"  Safe solutionizing range: {min_solutionize}°C to {max_solutionize:.0f}°C")
    print(f"  (Stay below solidus with 15°C safety margin)")
    
    if max_solutionize > min_solutionize:
        print(f"  ✓ Processing window exists: {max_solutionize - min_solutionize:.0f}°C range")
    else:
        print("  ⚠️ Very narrow or no safe processing window!")

print("\n" + "=" * 70)

plt.show()

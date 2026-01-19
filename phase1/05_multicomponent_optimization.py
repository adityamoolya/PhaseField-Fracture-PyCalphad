"""
05_multicomponent_optimization.py
Multi-component sensitivity analysis for Al-Zn-Mg-Cu (7xxx series) alloy
Generates contour maps showing η-phase (MgZn2) and S-phase (Al2CuMg) fractions
"""

import matplotlib.pyplot as plt
import numpy as np
from pycalphad import Database, equilibrium, variables as v
import warnings
warnings.filterwarnings('ignore')

# Load database
dbf = Database('COST507-modified.tdb')
print("=" * 70)
print("MULTI-COMPONENT SENSITIVITY ANALYSIS FOR Al-7xxx ALLOY")
print("=" * 70)

# Components and phases for Al-Zn-Mg-Cu system
comps = ['AL', 'ZN', 'MG', 'CU', 'VA']

# Phases of interest - includes strengthening and detrimental phases
# η-phase (MgZn2) represented by LAVES phases
# S-phase (Al2CuMg) if available in database
phases = ['FCC_A1', 'LIQUID', 'LAVES_C14', 'LAVES_C15', 'HCP_A3']

# Check for S-phase or similar Al2CuMg phases
all_phases = list(dbf.phases.keys())
s_phase_candidates = [p for p in all_phases if 'AL2CU' in p.upper() or 'ALCUMG' in p.upper() or 'THETA' in p.upper()]
if s_phase_candidates:
    phases.extend(s_phase_candidates)
    print(f"Found potential S-phase candidates: {s_phase_candidates}")

print(f"Using phases: {phases}")

# Aging temperature for analysis
T_aging = 120 + 273.15  # 120°C in Kelvin

# =============================================================================
# PART 1: Zn-Mg Contour Map (Fixed Cu at 1.5%)
# =============================================================================
print("\n--- Part 1: Zn-Mg Contour Map (Cu=1.5 wt%) ---")

# Composition ranges (converted to mole fraction approximately)
# For Al-Zn-Mg-Cu: wt% ≈ at% for these compositions
zn_range = np.linspace(0.04, 0.08, 12)  # 4-8 wt% Zn
mg_range = np.linspace(0.01, 0.03, 10)  # 1-3 wt% Mg
cu_fixed = 0.015  # Fixed at 1.5 wt%

eta_fractions = np.zeros((len(mg_range), len(zn_range)))

print(f"Calculating eta-phase fractions at T={T_aging-273.15:.0f}C...")

for i, mg in enumerate(mg_range):
    for j, zn in enumerate(zn_range):
        try:
            conds = {
                v.X('ZN'): zn,
                v.X('MG'): mg,
                v.X('CU'): cu_fixed,
                v.T: T_aging,
                v.P: 101325,
                v.N: 1
            }
            eq = equilibrium(dbf, comps, phases, conds)
            
            # Sum Laves phases (η-phase representation)
            eta_frac = eq.NP.where(
                (eq.Phase == 'LAVES_C14') | (eq.Phase == 'LAVES_C15')
            ).sum(dim='vertex').values.flatten()
            
            eta_fractions[i, j] = float(np.nanmax(eta_frac)) if len(eta_frac) > 0 else 0.0
            
        except Exception as e:
            eta_fractions[i, j] = np.nan
    
    print(f"  Progress: {(i+1)/len(mg_range)*100:.0f}% complete")

# =============================================================================
# PART 2: Zn-Cu Contour Map (Fixed Mg at 2.5%)
# =============================================================================
print("\n--- Part 2: Zn-Cu Contour Map (Mg=2.5 wt%) ---")

cu_range = np.linspace(0.005, 0.02, 10)  # 0.5-2 wt% Cu
mg_fixed = 0.025  # Fixed at 2.5 wt%

eta_fractions_cu = np.zeros((len(cu_range), len(zn_range)))

print(f"Calculating eta-phase fractions at T={T_aging-273.15:.0f}C...")

for i, cu in enumerate(cu_range):
    for j, zn in enumerate(zn_range):
        try:
            conds = {
                v.X('ZN'): zn,
                v.X('MG'): mg_fixed,
                v.X('CU'): cu,
                v.T: T_aging,
                v.P: 101325,
                v.N: 1
            }
            eq = equilibrium(dbf, comps, phases, conds)
            
            eta_frac = eq.NP.where(
                (eq.Phase == 'LAVES_C14') | (eq.Phase == 'LAVES_C15')
            ).sum(dim='vertex').values.flatten()
            
            eta_fractions_cu[i, j] = float(np.nanmax(eta_frac)) if len(eta_frac) > 0 else 0.0
            
        except Exception as e:
            eta_fractions_cu[i, j] = np.nan
    
    print(f"  Progress: {(i+1)/len(cu_range)*100:.0f}% complete")

# =============================================================================
# VISUALIZATION
# =============================================================================
print("\n--- Generating Contour Plots ---")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Multi-Component Sensitivity Analysis for Al-7xxx Alloy\n'
             f'η-Phase (MgZn₂) Volume Fraction at {T_aging-273.15:.0f}°C', 
             fontsize=14, fontweight='bold')

# Plot 1: Zn vs Mg
ZN, MG = np.meshgrid(zn_range * 100, mg_range * 100)  # Convert to %
cf1 = axes[0].contourf(ZN, MG, eta_fractions, levels=20, cmap='viridis')
cs1 = axes[0].contour(ZN, MG, eta_fractions, levels=5, colors='white', linewidths=0.5)
axes[0].clabel(cs1, inline=True, fontsize=8, fmt='%.3f')
axes[0].set_xlabel('Zinc Content (wt%)', fontsize=11)
axes[0].set_ylabel('Magnesium Content (wt%)', fontsize=11)
axes[0].set_title(f'Zn-Mg Map (Cu = {cu_fixed*100:.1f}%)', fontsize=12)
plt.colorbar(cf1, ax=axes[0], label='η-Phase Fraction')

# Mark Al-7075 typical composition
axes[0].scatter([5.6], [2.5], c='red', s=100, marker='*', edgecolors='white', 
                linewidths=1, label='Al-7075 Typical', zorder=5)
axes[0].legend(loc='lower right')

# Plot 2: Zn vs Cu
ZN2, CU = np.meshgrid(zn_range * 100, cu_range * 100)
cf2 = axes[1].contourf(ZN2, CU, eta_fractions_cu, levels=20, cmap='plasma')
cs2 = axes[1].contour(ZN2, CU, eta_fractions_cu, levels=5, colors='white', linewidths=0.5)
axes[1].clabel(cs2, inline=True, fontsize=8, fmt='%.3f')
axes[1].set_xlabel('Zinc Content (wt%)', fontsize=11)
axes[1].set_ylabel('Copper Content (wt%)', fontsize=11)
axes[1].set_title(f'Zn-Cu Map (Mg = {mg_fixed*100:.1f}%)', fontsize=12)
plt.colorbar(cf2, ax=axes[1], label='η-Phase Fraction')

# Mark Al-7075 typical composition
axes[1].scatter([5.6], [1.6], c='cyan', s=100, marker='*', edgecolors='black', 
                linewidths=1, label='Al-7075 Typical', zorder=5)
axes[1].legend(loc='lower right')

plt.tight_layout()
plt.savefig('05_multicomponent_contour.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 05_multicomponent_contour.png")

# =============================================================================
# FIND OPTIMAL COMPOSITION
# =============================================================================
print("\n" + "=" * 70)
print("OPTIMAL COMPOSITION ANALYSIS")
print("=" * 70)

# Find maximum η-phase in Zn-Mg space
max_idx = np.unravel_index(np.nanargmax(eta_fractions), eta_fractions.shape)
opt_mg = mg_range[max_idx[0]] * 100
opt_zn = zn_range[max_idx[1]] * 100
max_eta = eta_fractions[max_idx]

print(f"\nOptimal composition (Zn-Mg space, Cu={cu_fixed*100:.1f}%):")
print(f"  Zn = {opt_zn:.2f} wt%")
print(f"  Mg = {opt_mg:.2f} wt%")
print(f"  Maximum η-phase fraction = {max_eta:.4f}")

# Find maximum in Zn-Cu space
max_idx2 = np.unravel_index(np.nanargmax(eta_fractions_cu), eta_fractions_cu.shape)
opt_cu = cu_range[max_idx2[0]] * 100
opt_zn2 = zn_range[max_idx2[1]] * 100

print(f"\nOptimal composition (Zn-Cu space, Mg={mg_fixed*100:.1f}%):")
print(f"  Zn = {opt_zn2:.2f} wt%")
print(f"  Cu = {opt_cu:.2f} wt%")
print(f"  Maximum η-phase fraction = {eta_fractions_cu[max_idx2]:.4f}")

print("\n" + "=" * 70)
print("RECOMMENDATION:")
print("=" * 70)
print(f"For maximum strengthening via η-phase precipitation:")
print(f"  Target: Al - {opt_zn:.1f}Zn - {opt_mg:.1f}Mg - 1.5Cu (wt%)")
print("=" * 70)

plt.show()

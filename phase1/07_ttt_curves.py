"""
07_ttt_curves.py
Time-Temperature-Transformation (TTT) curves for Al-7xxx aging
Simulates precipitate growth at multiple temperatures (100°C, 120°C, 140°C)
"""

import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, calculate, equilibrium, variables as v
import warnings
warnings.filterwarnings('ignore')

# Load database
dbf = Database('COST507-modified.tdb')

print("=" * 70)
print("TIME-TEMPERATURE-TRANSFORMATION (TTT) CURVES")
print("Al-7xxx Alloy Aging Simulation")
print("=" * 70)

# Alloy composition (Al-Zn-Mg system for aging)
x_zn = 0.06  # 6 at%
x_mg = 0.02  # 2 at%

print(f"\nAlloy Composition:")
print(f"  Zn = {x_zn*100:.1f} at%")
print(f"  Mg = {x_mg*100:.1f} at%")

# Aging temperatures to study
aging_temps = [100, 120, 140]  # Celsius
colors = ['#2171b5', '#238b45', '#d94801']  # Blue, Green, Orange

# Time array: from 1 second to 100 hours (in seconds)
times_seconds = np.logspace(0, 5.56, 100)  # 1s to ~100 hours
times_hours = times_seconds / 3600

# Components and phases
comps = ['AL', 'ZN', 'MG', 'VA']
phases = ['FCC_A1', 'LAVES_C14', 'LAVES_C15', 'HCP_A3']

# =============================================================================
# CALCULATE DRIVING FORCE AND SIMULATE GROWTH AT EACH TEMPERATURE
# =============================================================================

results = {}
peak_times = {}

print("\n--- Calculating precipitation kinetics ---")

for i, T_celsius in enumerate(aging_temps):
    T_kelvin = T_celsius + 273.15
    print(f"\nTemperature: {T_celsius}°C ({T_kelvin:.1f} K)")
    
    # Get equilibrium data for this temperature
    try:
        conds = {
            v.X('ZN'): x_zn,
            v.X('MG'): x_mg,
            v.T: T_kelvin,
            v.P: 101325,
            v.N: 1
        }
        eq = equilibrium(dbf, comps, phases, conds)
        
        # Get equilibrium η-phase fraction
        eta_eq = eq.NP.where(
            (eq.Phase == 'LAVES_C14') | (eq.Phase == 'LAVES_C15')
        ).sum(dim='vertex').values.flatten()
        eta_eq_val = float(np.nanmax(eta_eq)) if len(eta_eq) > 0 else 0.05
        
        print(f"  Equilibrium η-phase fraction: {eta_eq_val:.4f}")
        
    except Exception as e:
        print(f"  Equilibrium calculation failed: {e}")
        eta_eq_val = 0.05  # Default value
    
    # Calculate Gibbs energy (driving force) from FCC
    try:
        calc = calculate(dbf, comps, 'FCC_A1', P=101325, T=T_kelvin, output='GM')
        G_matrix = abs(float(calc.GM.mean()))
    except:
        G_matrix = 1e5  # Default
    
    # Temperature-dependent diffusion coefficient
    # D = D0 * exp(-Q/RT)
    D0 = 1e-5  # m²/s (pre-exponential)
    Q = 130e3  # J/mol (activation energy for Zn/Mg in Al)
    R = 8.314  # J/mol·K
    D = D0 * np.exp(-Q / (R * T_kelvin))
    
    print(f"  Diffusion coefficient: {D:.2e} m²/s")
    
    # JMAK kinetics: f(t) = f_eq * [1 - exp(-(t/tau)^n)]
    # tau depends on temperature through diffusion
    # n is the Avrami exponent (typically 2-4 for precipitation)
    
    n_avrami = 2.5  # Avrami exponent
    
    # Characteristic time scale (inversely proportional to D)
    # Higher T = faster diffusion = shorter tau
    tau_ref = 3600  # Reference time at 120°C (1 hour)
    D_ref = D0 * np.exp(-Q / (R * (120 + 273.15)))  # D at 120°C
    tau = tau_ref * (D_ref / D)  # Scale by diffusion ratio
    
    print(f"  Characteristic time τ: {tau/3600:.2f} hours")
    
    # Calculate transformed fraction vs time (JMAK)
    transformed_fraction = eta_eq_val * (1 - np.exp(-(times_seconds / tau) ** n_avrami))
    
    # Find time to 50% and 90% transformation
    t_50 = tau * (-np.log(1 - 0.5)) ** (1/n_avrami)
    t_90 = tau * (-np.log(1 - 0.9)) ** (1/n_avrami)
    
    print(f"  Time to 50% transformation: {t_50/3600:.2f} hours")
    print(f"  Time to 90% transformation: {t_90/3600:.2f} hours")
    
    results[T_celsius] = {
        'times': times_hours,
        'fraction': transformed_fraction,
        'eta_eq': eta_eq_val,
        'tau': tau,
        't_50': t_50 / 3600,
        't_90': t_90 / 3600
    }
    peak_times[T_celsius] = t_90 / 3600

# =============================================================================
# VISUALIZATION
# =============================================================================
print("\n--- Generating TTT Plots ---")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Time-Temperature-Transformation Analysis for Al-7xxx Aging\n'
             f'Composition: Al-{x_zn*100:.0f}Zn-{x_mg*100:.0f}Mg (at%)',
             fontsize=13, fontweight='bold')

# Plot 1: Transformed fraction vs time (log scale)
ax1 = axes[0]
for i, T in enumerate(aging_temps):
    data = results[T]
    ax1.semilogx(data['times'], data['fraction'], color=colors[i], 
                 linewidth=2.5, label=f'{T}°C (τ = {data["tau"]/3600:.1f} h)')
    
    # Mark 50% and 90% transformation
    ax1.axhline(y=data['eta_eq'] * 0.5, color=colors[i], linestyle=':', alpha=0.5)
    ax1.axhline(y=data['eta_eq'] * 0.9, color=colors[i], linestyle='--', alpha=0.5)

ax1.set_xlabel('Aging Time (hours)', fontsize=11)
ax1.set_ylabel('η-Phase Volume Fraction', fontsize=11)
ax1.set_title('Precipitation Kinetics (JMAK Model)', fontsize=12)
ax1.legend(loc='lower right', fontsize=10)
ax1.grid(True, which='both', alpha=0.3)
ax1.set_xlim(1e-3, 100)

# Plot 2: TTT diagram style (Temperature vs Log Time)
ax2 = axes[1]

# For each transformation level, plot T vs time
transformation_levels = [0.1, 0.5, 0.9]
linestyles = [':', '-', '--']
labels = ['10% Transform', '50% Transform', '90% Transform']

for level, ls, label in zip(transformation_levels, linestyles, labels):
    temps_for_plot = []
    times_for_plot = []
    
    for T in aging_temps:
        data = results[T]
        tau = data['tau']
        n = 2.5
        
        # Time to reach this transformation level
        if level < 1:
            t_level = tau * (-np.log(1 - level)) ** (1/n)
            temps_for_plot.append(T)
            times_for_plot.append(t_level / 3600)
    
    if len(times_for_plot) > 0:
        ax2.semilogy(temps_for_plot, times_for_plot, 'o-', linewidth=2, 
                     markersize=8, linestyle=ls, label=label)

ax2.set_xlabel('Temperature (°C)', fontsize=11)
ax2.set_ylabel('Time (hours)', fontsize=11)
ax2.set_title('TTT Diagram', fontsize=12)
ax2.legend(loc='best', fontsize=10)
ax2.grid(True, which='both', alpha=0.3)
ax2.set_xlim(95, 145)

plt.tight_layout()
plt.savefig('07_ttt_curves.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 07_ttt_curves.png")

# =============================================================================
# SUMMARY AND RECOMMENDATIONS
# =============================================================================
print("\n" + "=" * 70)
print("AGING OPTIMIZATION RECOMMENDATIONS")
print("=" * 70)

print("\n| Temperature | Time to 50% | Time to 90% | Recommended Aging |")
print("|-------------|-------------|-------------|-------------------|")
for T in aging_temps:
    data = results[T]
    rec = f"{data['t_90']*0.8:.1f} - {data['t_90']*1.2:.1f} h"
    print(f"|    {T}°C     |   {data['t_50']:.2f} h    |   {data['t_90']:.2f} h    |    {rec}    |")

print("\n--- Key Findings ---")
fastest_T = min(peak_times, key=peak_times.get)
slowest_T = max(peak_times, key=peak_times.get)
print(f"  • Fastest aging at {fastest_T}°C (peak in ~{peak_times[fastest_T]:.1f} hours)")
print(f"  • Slowest aging at {slowest_T}°C (peak in ~{peak_times[slowest_T]:.1f} hours)")
print(f"  • Higher temperature = Faster kinetics but may cause overaging")

print("\n" + "=" * 70)

plt.show()

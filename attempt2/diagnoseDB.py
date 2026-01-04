"""
Test different compositions to find what COST507 can actually calculate
"""

from pycalphad import Database, equilibrium, variables as v
import numpy as np
import warnings
warnings.filterwarnings('ignore')

db = Database('COST507.tdb')

print("="*70)
print("COST507 COMPOSITION VALIDATION TEST")
print("="*70)

test_cases = [
    # (name, comp_dict, description)
    ("Pure Binary Al-Zn", {'ZN': 0.10}, "Standard binary test"),
    ("Pure Binary Al-Mg", {'MG': 0.10}, "Standard binary test"),
    ("Low Zn-Mg", {'ZN': 0.02, 'MG': 0.01}, "Dilute ternary"),
    ("Medium Zn-Mg", {'ZN': 0.05, 'MG': 0.02}, "7xxx baseline"),
    ("Your Composition", {'ZN': 0.056, 'MG': 0.025}, "Al-5.6Zn-2.5Mg (7075)"),
    ("High Zn-Mg", {'ZN': 0.10, 'MG': 0.05}, "High alloy content"),
]

phases = ['LIQUID', 'FCC_A1', 'MGZN2']
test_temp = 600  # Test at room temperature equivalent

print(f"\nTesting compositions at {test_temp}K with phases: {phases}\n")
print(f"{'Case':<25} {'Status':<10} {'Phases':<30} {'Sum':<8} {'Issue'}")
print("-"*70)

for name, comp, desc in test_cases:
    try:
        # Build component list
        comps = ['AL', 'VA']
        conditions = {v.P: 101325, v.T: test_temp, v.N: 1}
        
        for element, fraction in comp.items():
            comps.append(element)
            conditions[v.W(element)] = fraction
        
        # Calculate
        eq = equilibrium(db, comps, phases, conditions, 
                        calc_opts={'pdens': 2000}, verbose=False)
        
        # Extract results
        unique_phases = [p for p in np.unique(eq.Phase.values) if p != '']
        
        # Calculate total fraction
        total_frac = 0
        phase_fracs = {}
        for phase in unique_phases:
            mask = eq.Phase == phase
            frac = eq.NP.where(mask).sum(dim='vertex').squeeze()
            val = float(frac.values) if hasattr(frac, 'values') else float(frac)
            phase_fracs[phase] = val
            total_frac += val
        
        # Diagnostic
        phases_str = ", ".join([f"{p}:{phase_fracs[p]:.2f}" for p in unique_phases])
        sum_ok = abs(total_frac - 1.0) < 0.01
        
        issue = ""
        if not sum_ok:
            issue = f"⚠️  Sum={total_frac:.3f}"
        elif len(unique_phases) == 1 and 'FCC_A1' in unique_phases:
            issue = "⚠️  Only matrix (no precipitates)"
        
        status = "✅" if sum_ok else "❌"
        
        print(f"{name:<25} {status:<10} {phases_str:<30} {total_frac:.3f}   {issue}")
        
    except Exception as e:
        print(f"{name:<25} {'❌':<10} FAILED: {str(e)[:40]}")

# ============================================================================
# Test temperature sweep for pure binary (should work perfectly)
# ============================================================================
print("\n" + "="*70)
print("BINARY Al-10Zn TEMPERATURE SWEEP TEST")
print("="*70)

try:
    from tqdm import tqdm
    
    comps = ['AL', 'ZN', 'VA']
    phases = ['LIQUID', 'FCC_A1']
    temps = np.arange(400, 900, 20)
    
    print(f"Testing {len(temps)} temperatures from 400K to 900K...")
    
    results = []
    for temp in tqdm(temps):
        conditions = {v.W('ZN'): 0.10, v.P: 101325, v.T: temp, v.N: 1}
        eq = equilibrium(db, comps, phases, conditions, 
                        calc_opts={'pdens': 2000}, verbose=False)
        
        # Get phase fractions
        fcc_frac = 0
        liq_frac = 0
        
        if 'FCC_A1' in eq.Phase.values:
            mask = eq.Phase == 'FCC_A1'
            frac = eq.NP.where(mask).sum(dim='vertex').squeeze()
            fcc_frac = float(frac.values) if hasattr(frac, 'values') else float(frac)
        
        if 'LIQUID' in eq.Phase.values:
            mask = eq.Phase == 'LIQUID'
            frac = eq.NP.where(mask).sum(dim='vertex').squeeze()
            liq_frac = float(frac.values) if hasattr(frac, 'values') else float(frac)
        
        results.append({
            'T': temp,
            'FCC': fcc_frac,
            'LIQ': liq_frac,
            'SUM': fcc_frac + liq_frac
        })
    
    # Check for jumps
    fcc_vals = [r['FCC'] for r in results]
    fcc_diffs = np.abs(np.diff(fcc_vals))
    max_jump = np.max(fcc_diffs)
    
    sum_vals = [r['SUM'] for r in results]
    sum_error = np.mean(np.abs(np.array(sum_vals) - 1.0))
    
    print(f"\n✅ Binary sweep completed")
    print(f"   Max phase fraction jump: {max_jump:.3f}")
    print(f"   Avg sum error: {sum_error:.4f}")
    
    if max_jump > 0.3:
        print(f"   ⚠️  LARGE JUMPS even in simple binary!")
        print(f"   → COST507 database has fundamental numerical issues")
    else:
        print(f"   ✅ Binary system is smooth")
        print(f"   → Problem is specifically with ternary Al-Zn-Mg")
    
except Exception as e:
    print(f"❌ Binary sweep failed: {e}")

# ============================================================================
# RECOMMENDATION
# ============================================================================
print("\n" + "="*70)
print("DIAGNOSIS & RECOMMENDATIONS")
print("="*70)

print("""
Based on the tests above:

1. If binaries work but ternary fails:
   → COST507 lacks accurate Al-Zn-Mg ternary interaction parameters
   → Solution: Need TCAL or TTAL database for 7xxx alloys

2. If even binaries show jumps:
   → COST507 has fundamental numerical instability
   → Solution: Database is too old (1998), use modern alternatives

3. Immediate workarounds:
   a) Use simplified compositions (reduce Zn/Mg by 50%)
   b) Use only LIQUID + FCC_A1 (skip precipitate phases)
   c) Switch to a validated database for your alloy system

For academic work on 7xxx Al alloys, you typically need:
   - TCAL8 (Thermo-Calc Al database) - Commercial
   - TTAL8 (Thermodynamic Assessment) - Research
   - PanAl (Open source) - Limited but free
""")

print("="*70)
"""
Comprehensive Database Sanity Check for COST507.tdb
Checks for missing parameters, phase stability issues, and database integrity
"""

from pycalphad import Database, variables as v
import pandas as pd
import numpy as np

print("="*70)
print("COST507.TDB DATABASE SANITY CHECK")
print("="*70)

# Load database
try:
    db = Database('COST507.tdb')
    print("✅ Database loaded successfully\n")
except Exception as e:
    print(f"❌ Failed to load database: {e}")
    exit()

# ============================================================================
# TEST 1: Element Coverage
# ============================================================================
print("1️⃣  ELEMENT COVERAGE")
print("-"*70)
print(f"Elements in database: {sorted(db.elements)}")

required_elements = {'AL', 'ZN', 'MG', 'CU', 'VA'}
missing = required_elements - set(db.elements)
if missing:
    print(f"❌ MISSING ELEMENTS: {missing}")
else:
    print(f"✅ All required elements present")

# ============================================================================
# TEST 2: Phase Availability
# ============================================================================
print(f"\n2️⃣  PHASE AVAILABILITY")
print("-"*70)
all_phases = sorted(db.phases.keys())
print(f"Total phases in database: {len(all_phases)}")
print(f"Phases: {all_phases}\n")

# Check for essential phases
essential_phases = ['LIQUID', 'FCC_A1']
for phase in essential_phases:
    if phase in db.phases:
        print(f"✅ {phase} present")
    else:
        print(f"❌ {phase} MISSING (critical!)")

# ============================================================================
# TEST 3: Interaction Parameters
# ============================================================================
print(f"\n3️⃣  INTERACTION PARAMETERS FOR Al-Zn-Mg SYSTEM")
print("-"*70)

target_elements = {'AL', 'ZN', 'MG'}
param_summary = []

for param in db._parameters:
    # Get elements involved in this parameter
    constituents = param.get('constituent_array', [[]])
    if not constituents or len(constituents) == 0:
        continue
    
    # Check first sublattice
    involved_elements = set()
    for sublattice in constituents:
        for species in sublattice:
            if hasattr(species, 'name'):
                involved_elements.add(str(species.name))
            else:
                involved_elements.add(str(species))
    
    # Filter out VA
    involved_elements.discard('VA')
    involved_elements.discard('VACUUM')
    
    # Check if this parameter involves our system
    if len(involved_elements.intersection(target_elements)) >= 2:
        param_summary.append({
            'Phase': param.get('phase_name', 'Unknown'),
            'Elements': ', '.join(sorted(involved_elements.intersection(target_elements))),
            'Type': param.get('parameter_type', 'Unknown'),
            'Order': param.get('parameter_order', 0)
        })

if not param_summary:
    print("❌ CRITICAL: NO interaction parameters found for Al-Zn-Mg!")
    print("   This database cannot calculate this alloy system accurately.")
else:
    df = pd.DataFrame(param_summary)
    print(f"✅ Found {len(df)} parameters\n")
    
    # Group by phase
    print("Parameters by phase:")
    phase_counts = df.groupby('Phase').size().sort_values(ascending=False)
    for phase, count in phase_counts.items():
        print(f"   {phase:20s}: {count:3d} parameters")
    
    print("\nParameter types:")
    type_counts = df.groupby('Type').size()
    for ptype, count in type_counts.items():
        print(f"   {ptype:20s}: {count:3d}")

# ============================================================================
# TEST 4: Phase Constituent Check
# ============================================================================
print(f"\n4️⃣  PHASE CONSTITUENT VALIDATION")
print("-"*70)

phases_of_interest = ['LIQUID', 'FCC_A1', 'MGZN2', 'TAU', 'LAVES_C14']

for phase_name in phases_of_interest:
    if phase_name not in db.phases:
        print(f"⚠️  {phase_name}: NOT IN DATABASE")
        continue
    
    phase = db.phases[phase_name]
    
    print(f"\n{phase_name}:")
    print(f"   Model: {phase.model_hints.get('model_name', 'Unknown')}")
    
    # Get constituents
    constituents = phase.constituents
    print(f"   Sublattices: {len(constituents)}")
    for i, sublattice in enumerate(constituents):
        species_list = [str(s) for s in sublattice]
        print(f"      Sublattice {i}: {', '.join(species_list)}")
    
    # Check if our elements can exist in this phase
    all_species = set()
    for sublattice in constituents:
        for species in sublattice:
            all_species.add(str(species))
    
    our_elements = {'AL', 'ZN', 'MG'}
    available = our_elements.intersection(all_species)
    missing = our_elements - all_species
    
    if len(available) >= 2:
        print(f"   ✅ Can accommodate: {', '.join(available)}")
    if missing:
        print(f"   ⚠️  Missing: {', '.join(missing)}")

# ============================================================================
# TEST 5: Simple Binary Test
# ============================================================================
print(f"\n5️⃣  SIMPLE BINARY CALCULATION TEST (Al-Zn)")
print("-"*70)

try:
    from pycalphad import equilibrium
    
    # Simplest possible: pure binary at one temperature
    test_comps = ['AL', 'ZN', 'VA']
    test_phases = ['LIQUID', 'FCC_A1']
    
    test_conds = {
        v.W('ZN'): 0.05,
        v.P: 101325,
        v.T: 600,
        v.N: 1
    }
    
    print("Testing: Al-5wt%Zn at 600K with LIQUID + FCC_A1")
    
    result = equilibrium(db, test_comps, test_phases, test_conds, 
                        calc_opts={'pdens': 500})
    
    # Check result
    phases_present = [p for p in np.unique(result.Phase.values) if p != '']
    print(f"✅ Binary calculation successful")
    print(f"   Phases stable: {phases_present}")
    
    for phase in phases_present:
        mask = result.Phase == phase
        frac = result.NP.where(mask).sum(dim='vertex').squeeze().values
        if isinstance(frac, np.ndarray):
            frac = frac[0] if len(frac) > 0 else frac
        print(f"   {phase}: {float(frac):.3f} mole fraction")
    
except Exception as e:
    print(f"❌ Binary test FAILED: {e}")
    print("   Database may have fundamental issues")

# ============================================================================
# TEST 6: Check for Known Issues
# ============================================================================
print(f"\n6️⃣  KNOWN DATABASE ISSUES CHECK")
print("-"*70)

issues_found = []

# Check 1: Magnetic ordering parameters
mag_phases = [p for p in db.phases.keys() if 'magnetic' in str(db.phases[p].model_hints)]
if mag_phases:
    issues_found.append(f"Magnetic phases present: {mag_phases} (can cause discontinuities)")

# Check 2: Metastable phases
metastable_keywords = ['METASTABLE', 'META', 'UNSTABLE']
metastable = [p for p in db.phases.keys() 
              if any(kw in p.upper() for kw in metastable_keywords)]
if metastable:
    issues_found.append(f"Metastable phases: {metastable}")

# Check 3: Check if LIQUID has sublattices (it shouldn't)
if 'LIQUID' in db.phases:
    liquid_sublat = db.phases['LIQUID'].constituents
    if len(liquid_sublat) > 1:
        issues_found.append(f"LIQUID has {len(liquid_sublat)} sublattices (should be 1)")

if issues_found:
    print("⚠️  Potential issues detected:")
    for issue in issues_found:
        print(f"   - {issue}")
else:
    print("✅ No obvious structural issues detected")

# ============================================================================
# TEST 7: Ternary Test at Single Temperature
# ============================================================================
print(f"\n7️⃣  TERNARY SINGLE-POINT TEST (Al-Zn-Mg at 600K)")
print("-"*70)

try:
    from pycalphad import equilibrium
    
    test_comps = ['AL', 'ZN', 'MG', 'VA']
    test_phases = ['LIQUID', 'FCC_A1', 'MGZN2']
    
    test_conds = {
        v.W('ZN'): 0.056,
        v.W('MG'): 0.025,
        v.P: 101325,
        v.T: 600,
        v.N: 1
    }
    
    print("Testing: Al-5.6Zn-2.5Mg at 600K")
    
    result = equilibrium(db, test_comps, test_phases, test_conds,
                        calc_opts={'pdens': 2000})
    
    phases_present = [p for p in np.unique(result.Phase.values) if p != '']
    print(f"✅ Ternary calculation successful")
    print(f"   Phases stable: {phases_present}")
    
    for phase in phases_present:
        mask = result.Phase == phase
        frac = result.NP.where(mask).sum(dim='vertex').squeeze().values
        if isinstance(frac, np.ndarray):
            frac = frac[0] if len(frac) > 0 else frac
        print(f"   {phase}: {float(frac):.3f} mole fraction")
    
except Exception as e:
    print(f"❌ Ternary test FAILED: {e}")

# ============================================================================
# FINAL DIAGNOSIS
# ============================================================================
print(f"\n" + "="*70)
print("DIAGNOSIS")
print("="*70)

if not param_summary:
    print("🔴 CRITICAL: Database lacks Al-Zn-Mg interaction parameters")
    print("   → Cannot accurately model this alloy system")
    print("   → Recommend: Use TTAL8, TCAL8, or other modern Al database")
elif len(param_summary) < 10:
    print("🟡 WARNING: Very few interaction parameters")
    print("   → Database may be incomplete for this system")
    print(f"   → Only {len(param_summary)} parameters found")
else:
    print("🟢 Database has interaction parameters")
    print("   → The jumping behavior is likely a NUMERICAL issue, not database")
    print("   → Problem: pycalphad's minimizer is getting trapped in local minima")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)
print("1. Try different phase selection (remove metastable phases)")
print("2. Use step-by-step temperature calculation instead of sweep")
print("3. Consider using a more modern database (TCAL, TTAL)")
print("4. The COST507 database is from ~1998 - may not have")
print("   accurate data for modern 7xxx alloy compositions")
print("="*70)
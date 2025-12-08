import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, variables as v
import numpy as np

# --- CONFIGURATION ---
DB_FILE = 'database.tdb'
# REMOVED 'CU' to test the stable Al-Zn-Mg ternary core
COMPONENTS = ['AL', 'ZN', 'MG', 'VA']

# --- SIMPLIFIED PHASES ---
# We focus on the Al-Zn-Mg basics.
# LAVES_C14 is the Eta Phase (MgZn2) -> The most important one for 7075
PHASES = ['LIQUID', 'FCC_A1', 'LAVES_C14', 'ALMG_BETA', 'T_PHASE', 'HCP_A3']

# --- ALLOY COMPOSITION (Al-7075 without Copper) ---
# We keep Zn and Mg ratios the same.
composition = {
    v.W('ZN'): 0.056, 
    v.W('MG'): 0.025,
}

def run_simulation():
    print(f"Loading database: {DB_FILE}...")
    try:
        db = Database(DB_FILE)
    except Exception as e:
        print(f"Error: {e}")
        return

    print("Simulating Al-Zn-Mg Ternary System (No Copper)...")
    
    # Check which phases from our list actually exist in the DB
    db_phases = list(db.phases.keys())
    active_phases = [p for p in PHASES if p in db_phases]
    print(f"Active Phases: {active_phases}")

    # Run Equilibrium
    eq_result = equilibrium(
        db, COMPONENTS, active_phases,
        {v.P: 101325, v.T: (400, 1000, 5), v.N: 1, **composition}
    )

    print("Plotting...")
    fig = plt.figure(figsize=(10, 7))
    ax = fig.gca()
    
    phases_plotted = []
    
    for phase_name in active_phases:
        if phase_name not in eq_result.Phase.values:
            continue
            
        # Logic to extract data
        phase_indices = eq_result.Phase.values == phase_name
        if np.any(phase_indices):
            phase_amount = np.nansum(
                np.where(eq_result.Phase.values == phase_name, eq_result.NP.values, 0),
                axis=-1
            ).flatten()
            
            # Plot only significant phases
            if np.max(phase_amount) > 0.001:
                ax.plot(eq_result.T.values, phase_amount, label=phase_name, linewidth=2)
                phases_plotted.append(phase_name)

    ax.set_title('Al-Zn-Mg Phase Stability (Simplified Core)', fontsize=14)
    ax.set_xlabel('Temperature (K)', fontsize=12)
    ax.set_ylabel('Mole Fraction', fontsize=12)
    ax.set_xlim(400, 1000)
    ax.set_ylim(0, 1.05)
    ax.legend(loc='center right')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    print(f"Plot generated for: {phases_plotted}")
    plt.show()

if __name__ == "__main__":
    run_simulation()
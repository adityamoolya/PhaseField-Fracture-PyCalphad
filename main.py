import matplotlib.pyplot as plt
from pycalphad import Database, binplot, variables as v

# --- 1. REAL AL-ZN DATABASE (Simplified for Learning) ---
# This mimics the thermodynamics of Aluminum (AL) and Zinc (ZN).
# It contains:
# - LIQUID phase
# - FCC_A1 phase (Aluminum-rich solid)
# - HCP_A3 phase (Zinc-rich solid)
al_zn_tdb = """
ELEMENT AL   FCC_A1  26.9815  4500.0  0.0 !
ELEMENT ZN   HCP_A3  65.38    4000.0  0.0 !

PHASE LIQUID % 1 1.0 !
CONSTITUENT LIQUID : AL, ZN : !

PHASE FCC_A1 % 1 1.0 !
CONSTITUENT FCC_A1 : AL, ZN : !

PHASE HCP_A3 % 1 1.0 !
CONSTITUENT HCP_A3 : AL, ZN : !

! --- Standard Gibbs Energies (Simplified) ---
PARAMETER G(LIQUID,AL;0)  298.15  11000 - 11*T; 6000 N !
PARAMETER G(LIQUID,ZN;0)  298.15  7000 - 9*T; 6000 N !

PARAMETER G(FCC_A1,AL;0)  298.15  -5000 + 5*T; 6000 N !
PARAMETER G(FCC_A1,ZN;0)  298.15  +2000 + 5*T; 6000 N !

PARAMETER G(HCP_A3,AL;0)  298.15  +3000 + 5*T; 6000 N !
PARAMETER G(HCP_A3,ZN;0)  298.15  -6000 + 6*T; 6000 N !

! --- Interaction Parameters (The Mixing Physics) ---
PARAMETER L(LIQUID,AL,ZN;0) 298.15 -15000 + 5*T; 6000 N !
PARAMETER L(FCC_A1,AL,ZN;0) 298.15 +18000 - 2*T; 6000 N !
"""

def plot_al_zn():
    print("Loading Al-Zn System...")
    dbf = Database.from_string(al_zn_tdb, fmt='tdb')
    
    # --- 2. Setup Calculation ---
    # We want to see what happens from 0% Zn to 100% Zn
    # And from Room Temp (300K) to Hot (1500K)
    comps = ['AL', 'ZN', 'VA'] # VA is "Vacuum" (required for crystal defects, standard in Calphad)
    phases = ['LIQUID', 'FCC_A1', 'HCP_A3']
    
    conds = {
        v.P: 101325, 
        v.T: (300, 1500, 10),   # 300K to 1500K
        v.X('ZN'): (0, 1, 0.02) # 0% to 100% Zinc
    }

    # --- 3. Plotting ---
    print("Calculating Al-Zn Phase Diagram (This takes ~15 seconds)...")
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111)
    
    # This command does ALL the heavy lifting
    binplot(dbf, ['AL', 'ZN'], phases, conds, plot_kwargs={'ax': ax})

    plt.title("Calculated Al-Zn Binary Phase Diagram")
    plt.xlabel("Composition (Mole Fraction Zinc)")
    plt.ylabel("Temperature (K)")
    
    print("Done. Check the popup window!")
    plt.show()

if __name__ == "__main__":
    plot_al_zn()
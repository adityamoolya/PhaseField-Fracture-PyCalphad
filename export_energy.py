import pycalphad
from pycalphad import Database, calculate, variables as v
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CORRECTED Al-Zn Database ---
# Fixed: Changed 'A' and 'B' to 'AL' and 'ZN' in the CONSTITUENT lines
al_zn_tdb = """
ELEMENT AL   FCC_A1  26.9815  4500.0  0.0 !
ELEMENT ZN   HCP_A3  65.38    4000.0  0.0 !

PHASE LIQUID % 1 1.0 !
CONSTITUENT LIQUID : AL, ZN : !

PHASE FCC_A1 % 1 1.0 !
CONSTITUENT FCC_A1 : AL, ZN : !

PHASE HCP_A3 % 1 1.0 !
CONSTITUENT HCP_A3 : AL, ZN : !

! --- Gibbs Energy Parameters ---
PARAMETER G(LIQUID,AL;0)  298.15  11000 - 11*T; 6000 N !
PARAMETER G(LIQUID,ZN;0)  298.15  7000 - 9*T; 6000 N !

PARAMETER G(FCC_A1,AL;0)  298.15  -5000 + 5*T; 6000 N !
PARAMETER G(FCC_A1,ZN;0)  298.15  +2000 + 5*T; 6000 N !

PARAMETER G(HCP_A3,AL;0)  298.15  +3000 + 5*T; 6000 N !
PARAMETER G(HCP_A3,ZN;0)  298.15  -6000 + 6*T; 6000 N !

! --- Interaction Parameters ---
PARAMETER L(LIQUID,AL,ZN;0) 298.15 -15000 + 5*T; 6000 N !
PARAMETER L(FCC_A1,AL,ZN;0) 298.15 +18000 - 2*T; 6000 N !
"""

def export_data():
    dbf = Database.from_string(al_zn_tdb, fmt='tdb')
    
    # --- 2. Define Conditions ---
    temp = 700 
    comps = ['AL', 'ZN', 'VA']
    
    print(f"Calculating Gibbs Energy curves at {temp} K...")

    phases = ['LIQUID', 'FCC_A1', 'HCP_A3']
    all_data = []

    for ph in phases:
        # Calculate GM (Gibbs Mass Energy)
        result = calculate(dbf, comps, ph, P=101325, T=temp, output='GM')
        
        # Select ZN component values
        # Note: result.X has shape (N, 2). We want the 2nd column (index 1) which is Zn.
        # But safely, we select by component name.
        x_zn = result.X.sel(component='ZN').values.flatten()
        energy = result.GM.values.flatten()
        
        for x, g in zip(x_zn, energy):
            all_data.append({'Phase': ph, 'X_ZN': x, 'Energy_J_mol': g})

    # --- 3. Save to CSV ---
    df = pd.DataFrame(all_data)
    filename = "thermo_data_700K.csv"
    df.to_csv(filename, index=False)
    print(f"SUCCESS: Data saved to {filename}")

    # --- 4. Quick Plot to Verify ---
    plt.figure(figsize=(8, 5))
    for ph in phases:
        subset = df[df['Phase'] == ph]
        # Sort values for a clean line plot
        subset = subset.sort_values(by='X_ZN')
        plt.plot(subset['X_ZN'], subset['Energy_J_mol'], label=ph)
    
    plt.title(f"Gibbs Energy Curves at {temp} K")
    plt.xlabel("Composition X(Zn)")
    plt.ylabel("Gibbs Energy (J/mol)")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    export_data()
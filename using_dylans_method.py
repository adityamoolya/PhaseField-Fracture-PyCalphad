import matplotlib.pyplot as plt
from pycalphad import Database, binplot
import pycalphad.variables as v

# 1. Load the database
# Make sure COST507.tdb is in the same folder as this script
db_alli = Database('COST507-modified.tdb')

# 2. Define components and phases
# 'VA' (Vacancy) must be in the components list
components = ['AL', 'LI', 'VA']

# These phase names must exist exactly as written in your .tdb file
my_phases_alli = ['FCC_A1', 'AL11', 'AL2I3', 'AL4I9', 'LIQUID', 'BCC_A2']

# 3. Define the conditions
# Modern pycalphad uses a dictionary for conditions
conditions = {
    v.X('LI'): (0, 1.0, 0.01),  # Composition range: (Start, Stop, Step)
    v.T: (100, 1000, 5),       # Temperature range: (Start, Stop, Step)
    v.P: 101325,               # Pressure in Pascals
    v.N: 1                     # Moles of system
}

# 4. Generate the plot
print("Generating phase diagram... this may take a moment.")
fig = plt.figure(figsize=(9, 6))
ax = fig.gca()

binplot(
    db_alli, 
    components, 
    my_phases_alli, 
    conditions, 
    ax=ax,
    plot_kwargs={'ticlines': False}
)

# 5. Save and display
plt.title("Al-Li Binary Phase Diagram (COST507)")
plt.tight_layout()
plt.savefig('Al_Li_Phase_Diagram.pdf', bbox_inches='tight')
print("Diagram saved as Al_Li_Phase_Diagram.pdf")
plt.show()
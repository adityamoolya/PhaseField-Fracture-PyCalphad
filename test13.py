import matplotlib.pyplot as plt
from pycalphad import Database, binplot
import pycalphad.variables as v

# Load thermodynamic database
db_alli = Database("COST507-modified.tdb")

# Define phases
my_phases_alli = [
    "FCC_A1",
    "ALLI",
    "AL2LI3",
    "AL4LI9",
    "LIQUID",
    "BCC_A2"
]

# Generate binary phase diagram
binplot(
    db_alli,
    components=["AL", "LI", "VA"],
    phases=my_phases_alli,
    conditions={
        v.X("LI"): (0, 1, 0.001),
        v.T: (100, 1000, 1),
        v.P: 101325,
        v.N: 1
    },
    plot_kwargs={"tielines": False}
)

plt.tight_layout()
plt.savefig("ALLI_phase_diagram.pdf", bbox_inches="tight")
plt.show()

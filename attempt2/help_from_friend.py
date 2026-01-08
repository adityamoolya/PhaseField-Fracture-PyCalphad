# %matplotlib inline
import matplotlib.pyplot as plt
from pycalphad import Database, binplot
import pycalphad.variables as v

db_alli = Database('database.tdb')
my_phases_alli = ['FCC_A1', 'AL11', 'AL2I3', 'AL4I9', 'LIQUID', 'BCC_A2']

binplot(
    db_alli,
    ['AL', 'LI'],
    'VA',
    my_phases_alli,
    (v.X('LI'), (0, 1.0, 0.001)),
    v.T,
    (100, 1000, 1),
    v.P,
    101325,
    v.N,
    1,
    plot_kwargs={'ticlines': False}
)

plt.tight_layout()
plt.savefig('DIAGRAAAMMMMMMMMM.pdf', bbox_inches='tight')
plt.show()

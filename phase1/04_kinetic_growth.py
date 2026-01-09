import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, calculate, variables as v

dbf = Database('COST507-modified.tdb')
T_aging = 120 + 273.15 # 120 Celsius in Kelvin

print(f"--- Running Script 4: Kinetic Growth Simulation ---")

# Pull thermodynamic driving force (GM) from your database
res = calculate(dbf, ['AL', 'ZN', 'VA'], 'FCC_A1', P=101325, T=T_aging, output='GM')
driving_force = abs(float(res.GM.mean()))

# Time array: 1 second up to 30 hours
times = np.logspace(0, 5.03, 50) 
# Parabolic growth law: R = sqrt(k * DrivingForce * time)
growth_rate = 1e-12 
radius = np.sqrt(growth_rate * driving_force * times) * 1e9 # Convert to nanometers

plt.figure(figsize=(8, 5))
plt.semilogx(times / 3600, radius, color='navy', lw=3)
plt.title("Predicted Precipitate Growth (Aging at 120°C)")
plt.xlabel("Aging Time (Hours)")
plt.ylabel("Average Precipitate Radius (nm)")
plt.grid(True, which="both", alpha=0.3)
plt.savefig('04_kinetic_growth.png', dpi=300)
print("Success: saved as 04_kinetic_growth.png")
plt.show()
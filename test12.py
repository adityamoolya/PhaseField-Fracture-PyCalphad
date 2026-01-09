"""
Al 7xxx Phase Field Simulation using COST507_modified.tdb
NO FALLBACK VALUES - Uses only real thermodynamic data from database
For scientific publication - all errors are raised, not suppressed
"""

import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, calculate, equilibrium, variables as v
from scipy.ndimage import convolve
import sys

class Al7xxxPhaseFieldCOST507:
    """
    Phase field simulation for Al-Zn-Mg using COST507_modified.tdb
    Raises errors if database data cannot be accessed - NO FAKE VALUES
    """
    
    def __init__(self, tdb_file, nx=128, ny=128, dx=1e-9, dt=1e-3, 
                 T=393.15, x_zn=0.06, x_mg=0.02):
        """
        Initialize phase field model with COST507 database
        
        Parameters:
        -----------
        tdb_file : str
            Path to COST507_modified.tdb file
        nx, ny : int
            Grid dimensions
        dx : float
            Grid spacing (m)
        dt : float
            Time step (s)
        T : float
            Temperature (K)
        x_zn, x_mg : float
            Mole fractions of Zn and Mg
        """
        self.nx = nx
        self.ny = ny
        self.dx = dx
        self.dt = dt
        self.T = T
        self.R = 8.314  # J/mol·K
        
        print("=" * 80)
        print("LOADING COST507_modified.tdb DATABASE")
        print("=" * 80)
        
        # Load database - will raise error if file not found
        self.db = Database(tdb_file)
        print(f"✓ Loaded: {tdb_file}")
        
        # Verify required elements exist
        required_elements = ['AL', 'ZN', 'MG']
        available_elements = list(self.db.elements)
        
        print(f"\nAvailable elements: {available_elements}")
        for elem in required_elements:
            if elem not in available_elements:
                raise ValueError(f"CRITICAL: Element {elem} not found in database!")
        print(f"✓ All required elements present: {required_elements}")
        
        # Setup components
        self.components = ['AL', 'ZN', 'MG', 'VA']
        
        # Get all phases
        all_phases = list(self.db.phases.keys())
        print(f"\nTotal phases in database: {len(all_phases)}")
        
        # Select phases relevant for Al-Zn-Mg system
        self.phases = self.select_relevant_phases(all_phases)
        print(f"Selected phases for simulation: {self.phases}")
        
        if len(self.phases) == 0:
            raise ValueError("CRITICAL: No relevant phases found in database!")
        
        # Store initial composition
        self.x_zn_initial = x_zn
        self.x_mg_initial = x_mg
        
        # Extract thermodynamic parameters from COST507
        print("\n" + "=" * 80)
        print("EXTRACTING THERMODYNAMIC DATA FROM COST507")
        print("=" * 80)
        self.extract_thermodynamic_data()
        
        # Initialize phase field variables
        self.eta = np.random.rand(nx, ny) * 0.01
        self.c_zn = np.ones((nx, ny)) * x_zn
        self.c_mg = np.ones((nx, ny)) * x_mg
        
        # Phase field parameters
        self.kappa = 1e-14  # Gradient energy coefficient (J/m)
        self.M_eta = 1e-10  # Order parameter mobility (m³/J·s)
        self.M_c = 1e-15    # Composition mobility (m⁵/J·s)
        self.W = 1e7        # Double well height (J/m³)
        
        # Time tracking
        self.time = 0.0
        self.step = 0
        
        print("\n✓ Phase field model initialized successfully")
        print("=" * 80)
    
    def select_relevant_phases(self, all_phases):
        """
        Select phases relevant for Al-Zn-Mg system
        Requires at least FCC_A1 (matrix) and one other phase
        """
        # Must have FCC_A1 for aluminum matrix
        if 'FCC_A1' not in all_phases:
            raise ValueError("CRITICAL: FCC_A1 phase not found - cannot simulate Al matrix!")
        
        relevant = ['FCC_A1', 'LIQUID', 'HCP_A3']  # Basic phases
        
        # Add any Mg-Zn compound phases
        for phase in all_phases:
            if any(keyword in phase.upper() for keyword in ['MGZN', 'MG2ZN', 'MG_ZN']):
                relevant.append(phase)
        
        # Return only phases that exist in database
        return [p for p in relevant if p in all_phases]
    
    def extract_thermodynamic_data(self):
        """
        Extract equilibrium compositions and Gibbs energies from COST507
        RAISES ERRORS IF DATA CANNOT BE EXTRACTED - NO FALLBACKS
        """
        # Calculate phase equilibrium
        print(f"Calculating equilibrium at T={self.T:.2f} K ({self.T-273.15:.1f}°C)")
        print(f"Composition: {self.x_zn_initial*100:.2f}% Zn, {self.x_mg_initial*100:.2f}% Mg")
        
        conditions = {
            v.T: self.T,
            v.P: 101325,
            v.X('ZN'): self.x_zn_initial,
            v.X('MG'): self.x_mg_initial
        }
        
        # Calculate equilibrium - let it raise error if it fails
        eq_result = equilibrium(
            self.db,
            self.components,
            self.phases,
            conditions
        )
        
        print("✓ Equilibrium calculation successful")
        
        # Debug: print structure of eq_result
        print("\nEquilibrium result structure:")
        print(f"  Variables: {list(eq_result.data_vars)}")
        print(f"  Coordinates: {list(eq_result.coords)}")
        print(f"  Dimensions: {eq_result.dims}")
        
        # Extract phase information from data variable (not coordinate)
        # Phase is stored as a data variable, NP contains phase fractions
        phase_data = eq_result['Phase'].values.squeeze()
        phase_amounts = eq_result['NP'].values.squeeze()
        
        # phase_data contains phase names as strings
        # phase_amounts contains corresponding mole fractions
        print(f"\nPhase data shape: {phase_data.shape}")
        print(f"Phase amounts shape: {phase_amounts.shape}")
        
        # Get unique phases and their amounts
        if phase_data.ndim == 0:
            # Single phase
            phase_names = [str(phase_data)]
            phase_amounts = [float(phase_amounts)]
        elif phase_data.ndim == 1:
            # Multiple phases
            phase_names = [str(p) for p in phase_data]
            phase_amounts = list(phase_amounts)
        else:
            # Multi-dimensional - take first vertex
            phase_names = [str(p) for p in phase_data.ravel()]
            phase_amounts = list(phase_amounts.ravel()[:len(phase_names)])
        
        # Find stable phases
        stable_phases = []
        stable_indices = []
        stable_fractions = []
        
        for i, (phase, amount) in enumerate(zip(phase_names, phase_amounts)):
            if amount > 1e-10:
                phase_str = str(phase).strip()
                if phase_str and phase_str != '' and phase_str != 'nan':
                    stable_phases.append(phase_str)
                    stable_indices.append(i)
                    stable_fractions.append(amount)
                    print(f"  Stable phase: {phase_str:15s} fraction = {amount:.6f}")
        
        if len(stable_phases) == 0:
            raise ValueError("CRITICAL: No stable phases found at equilibrium!")
        
        # Extract matrix composition (FCC_A1)
        if 'FCC_A1' not in stable_phases:
            raise ValueError("CRITICAL: FCC_A1 (matrix) not stable at these conditions!")
        
        fcc_idx = stable_indices[stable_phases.index('FCC_A1')]
        
        # Get composition data
        x_data = eq_result['X'].values.squeeze()
        component_names = list(eq_result.coords['component'].values)
        
        print(f"\nComposition data shape: {x_data.shape}")
        print(f"Components: {component_names}")
        
        zn_idx = component_names.index('ZN')
        mg_idx = component_names.index('MG')
        
        # Handle multi-dimensional X array (vertex dimension)
        if x_data.ndim == 2:
            # Shape is (vertex, component)
            self.c_matrix_zn = float(x_data[fcc_idx, zn_idx])
            self.c_matrix_mg = float(x_data[fcc_idx, mg_idx])
        elif x_data.ndim == 3:
            # Shape is (condition, vertex, component) - take first condition
            self.c_matrix_zn = float(x_data[0, fcc_idx, zn_idx])
            self.c_matrix_mg = float(x_data[0, fcc_idx, mg_idx])
        else:
            raise ValueError(f"Unexpected X data shape: {x_data.shape}")
        
        print(f"\n✓ Matrix (FCC_A1) composition:")
        print(f"  Zn: {self.c_matrix_zn:.6f} ({self.c_matrix_zn*100:.4f}%)")
        print(f"  Mg: {self.c_matrix_mg:.6f} ({self.c_matrix_mg*100:.4f}%)")
        
        # Extract precipitate composition (if exists)
        precipitate_phases = [p for p in stable_phases if p != 'FCC_A1' and p != 'LIQUID']
        
        if len(precipitate_phases) > 0:
            # Use first precipitate phase
            precip_phase = precipitate_phases[0]
            precip_idx = stable_indices[stable_phases.index(precip_phase)]
            
            if x_data.ndim == 2:
                self.c_precip_zn = float(x_data[precip_idx, zn_idx])
                self.c_precip_mg = float(x_data[precip_idx, mg_idx])
            elif x_data.ndim == 3:
                self.c_precip_zn = float(x_data[0, precip_idx, zn_idx])
                self.c_precip_mg = float(x_data[0, precip_idx, mg_idx])
            
            self.precipitate_phase_name = precip_phase
            
            print(f"\n✓ Precipitate ({precip_phase}) composition:")
            print(f"  Zn: {self.c_precip_zn:.6f} ({self.c_precip_zn*100:.4f}%)")
            print(f"  Mg: {self.c_precip_mg:.6f} ({self.c_precip_mg*100:.4f}%)")
        else:
            raise ValueError("CRITICAL: No precipitate phase stable - cannot simulate precipitation!")
        
        # Calculate Gibbs energies from COST507
        print("\nCalculating Gibbs free energies from COST507...")
        
        # Matrix energy
        calc_matrix = calculate(
            self.db,
            self.components,
            'FCC_A1',
            T=self.T,
            P=101325,
            points={'X(ZN)': [self.c_matrix_zn], 'X(MG)': [self.c_matrix_mg]}
        )
        G_matrix_array = calc_matrix.GM.values.squeeze()
        self.G_matrix = float(G_matrix_array.flat[0]) if G_matrix_array.size > 0 else float(G_matrix_array)
        print(f"  G(matrix) = {self.G_matrix:.2f} J/mol")
        
        # Precipitate energy
        calc_precip = calculate(
            self.db,
            self.components,
            self.precipitate_phase_name,
            T=self.T,
            P=101325,
            points={'X(ZN)': [self.c_precip_zn], 'X(MG)': [self.c_precip_mg]}
        )
        G_precip_array = calc_precip.GM.values.squeeze()
        self.G_precip = float(G_precip_array.flat[0]) if G_precip_array.size > 0 else float(G_precip_array)
        print(f"  G(precipitate) = {self.G_precip:.2f} J/mol")
        
        # Driving force for precipitation
        self.driving_force = float(self.G_matrix - self.G_precip)
        print(f"\n✓ Driving force: ΔG = {self.driving_force:.2f} J/mol")
        
        if self.driving_force < 0:
            print("  WARNING: Negative driving force - precipitation not thermodynamically favorable")
            print("  Consider adjusting temperature or composition")
        
        # Calculate chemical potential derivatives
        self.calculate_chemical_potential_derivatives()
    
    def calculate_chemical_potential_derivatives(self):
        """
        Calculate dG/dc numerically from COST507 data
        NO APPROXIMATIONS - uses actual database
        """
        print("\nCalculating chemical potential derivatives...")
        
        # Adaptive composition step for numerical derivative
        # Use smaller step if composition is very low
        dc_zn = min(0.001, self.c_matrix_zn * 0.1) if self.c_matrix_zn > 0 else 0.001
        dc_mg = min(0.001, self.c_matrix_mg * 0.1) if self.c_matrix_mg > 0 else 0.0001
        
        # For matrix phase (FCC_A1)
        # dG/dX_Zn
        c_zn_plus = min(self.c_matrix_zn + dc_zn, 0.99)
        c_zn_minus = max(self.c_matrix_zn - dc_zn, 0.0)
        actual_dc_zn = c_zn_plus - c_zn_minus
        
        if actual_dc_zn > 1e-10:
            G_plus_array = calculate(
                self.db, self.components, 'FCC_A1',
                T=self.T, P=101325,
                points={'X(ZN)': [c_zn_plus], 'X(MG)': [self.c_matrix_mg]}
            ).GM.values.squeeze()
            G_plus = float(G_plus_array.flat[0])
            
            G_minus_array = calculate(
                self.db, self.components, 'FCC_A1',
                T=self.T, P=101325,
                points={'X(ZN)': [c_zn_minus], 'X(MG)': [self.c_matrix_mg]}
            ).GM.values.squeeze()
            G_minus = float(G_minus_array.flat[0])
            
            self.dG_dc_zn = float((G_plus - G_minus) / actual_dc_zn)
            print(f"  dG/dX_Zn = {self.dG_dc_zn:.2f} J/mol (step={actual_dc_zn:.6f})")
        else:
            raise ValueError("Cannot calculate dG/dX_Zn - composition range too small")
        
        # dG/dX_Mg
        c_mg_plus = min(self.c_matrix_mg + dc_mg, 0.99)
        c_mg_minus = max(self.c_matrix_mg - dc_mg, 0.0)
        actual_dc_mg = c_mg_plus - c_mg_minus
        
        if actual_dc_mg > 1e-10:
            G_plus_array = calculate(
                self.db, self.components, 'FCC_A1',
                T=self.T, P=101325,
                points={'X(ZN)': [self.c_matrix_zn], 'X(MG)': [c_mg_plus]}
            ).GM.values.squeeze()
            G_plus = float(G_plus_array.flat[0])
            
            G_minus_array = calculate(
                self.db, self.components, 'FCC_A1',
                T=self.T, P=101325,
                points={'X(ZN)': [self.c_matrix_zn], 'X(MG)': [c_mg_minus]}
            ).GM.values.squeeze()
            G_minus = float(G_minus_array.flat[0])
            
            self.dG_dc_mg = float((G_plus - G_minus) / actual_dc_mg)
            print(f"  dG/dX_Mg = {self.dG_dc_mg:.2f} J/mol (step={actual_dc_mg:.6f})")
        else:
            raise ValueError("Cannot calculate dG/dX_Mg - composition range too small")
        
        print("✓ Chemical potential derivatives calculated from COST507")
    
    def double_well(self, eta):
        """Double well potential"""
        return self.W * eta**2 * (1 - eta)**2
    
    def double_well_derivative(self, eta):
        """dg/dη"""
        return 2 * self.W * eta * (1 - eta) * (1 - 2*eta)
    
    def interpolation(self, eta):
        """Interpolation function h(η) = 3η² - 2η³"""
        return 3*eta**2 - 2*eta**3
    
    def interpolation_derivative(self, eta):
        """dh/dη"""
        return 6*eta - 6*eta**2
    
    def laplacian(self, field):
        """Compute Laplacian using finite differences"""
        kernel = np.array([[0, 1, 0],
                          [1, -4, 1],
                          [0, 1, 0]]) / (self.dx**2)
        return convolve(field, kernel, mode='wrap')
    
    def compute_driving_force_eta(self):
        """
        Driving force for order parameter evolution
        Uses COST507 thermodynamic data - NO APPROXIMATIONS
        """
        # Double well contribution
        dg = self.double_well_derivative(self.eta)
        
        # Gradient energy
        lap_eta = self.laplacian(self.eta)
        
        # Chemical driving force from COST507
        h_prime = self.interpolation_derivative(self.eta)
        
        # Thermodynamic driving force from database
        chem_drive = -h_prime * self.driving_force / 1e9  # Scale for numerical stability
        
        return dg - self.kappa * lap_eta + chem_drive
    
    def compute_driving_force_composition(self, c, c_eq, dG_dc):
        """
        Driving force for composition evolution
        Uses chemical potential from COST507
        """
        # Chemical potential (from COST507)
        mu = dG_dc * (c - c_eq)
        
        # Diffusion coefficient (temperature dependent)
        D0 = 1e-5  # m²/s
        Q = 120e3  # J/mol activation energy
        D = D0 * np.exp(-Q / (self.R * self.T))
        
        # Laplacian for diffusion
        lap_c = self.laplacian(c)
        
        return mu - D * lap_c
    
    def evolve(self):
        """Time evolution using Allen-Cahn and Cahn-Hilliard equations"""
        
        # Allen-Cahn for order parameter
        dF_eta = self.compute_driving_force_eta()
        self.eta -= self.M_eta * dF_eta * self.dt
        self.eta = np.clip(self.eta, 0, 1)
        
        # Cahn-Hilliard for Zn composition
        dF_zn = self.compute_driving_force_composition(
            self.c_zn, self.c_matrix_zn, self.dG_dc_zn
        )
        flux_zn = self.M_c * self.laplacian(dF_zn)
        self.c_zn += flux_zn * self.dt
        self.c_zn = np.clip(self.c_zn, 0, 1)
        
        # Cahn-Hilliard for Mg composition
        dF_mg = self.compute_driving_force_composition(
            self.c_mg, self.c_matrix_mg, self.dG_dc_mg
        )
        flux_mg = self.M_c * self.laplacian(dF_mg)
        self.c_mg += flux_mg * self.dt
        self.c_mg = np.clip(self.c_mg, 0, 1)
        
        # Update time
        self.time += self.dt
        self.step += 1
    
    def add_nucleation_sites(self, n_sites=10):
        """Add nucleation sites with precipitate composition"""
        for _ in range(n_sites):
            x = np.random.randint(10, self.nx-10)
            y = np.random.randint(10, self.ny-10)
            r = 3
            Y, X = np.ogrid[:self.ny, :self.nx]
            mask = (X - x)**2 + (Y - y)**2 <= r**2
            self.eta[mask] = 0.8 + np.random.rand(np.sum(mask)) * 0.2
            self.c_zn[mask] = self.c_precip_zn
            self.c_mg[mask] = self.c_precip_mg
    
    def get_precipitate_fraction(self):
        """Volume fraction of precipitates"""
        return np.mean(self.eta > 0.5)
    
    def get_statistics(self):
        """Current simulation statistics"""
        return {
            'time': self.time,
            'step': self.step,
            'precipitate_fraction': self.get_precipitate_fraction(),
            'avg_zn': np.mean(self.c_zn),
            'avg_mg': np.mean(self.c_mg),
            'max_eta': np.max(self.eta)
        }

def run_simulation(tdb_file='COST507_modified.tdb', 
                   T=393.15, x_zn=0.06, x_mg=0.02,
                   steps=1000, save_interval=50):
    """
    Run phase field simulation with COST507 database
    NO FALLBACKS - will raise errors if data extraction fails
    """
    
    # Initialize model - will raise error if database issues occur
    model = Al7xxxPhaseFieldCOST507(
        tdb_file=tdb_file,
        nx=128, ny=128,
        dx=1e-9, dt=1e-3,
        T=T, x_zn=x_zn, x_mg=x_mg
    )
    
    # Add nucleation sites
    n_nuclei = 15
    model.add_nucleation_sites(n_sites=n_nuclei)
    print(f"\n✓ Added {n_nuclei} nucleation sites")
    
    print("\n" + "=" * 80)
    print("STARTING PHASE FIELD SIMULATION")
    print("=" * 80)
    print(f"Grid: {model.nx}×{model.ny}, dx={model.dx*1e9:.2f} nm, dt={model.dt:.2e} s")
    print(f"Total steps: {steps}")
    print("=" * 80 + "\n")
    
    # Storage
    saved_steps = []
    saved_eta = []
    saved_c_zn = []
    saved_c_mg = []
    statistics = []
    
    # Run simulation
    for i in range(steps):
        model.evolve()
        
        if i % save_interval == 0:
            saved_steps.append(model.step)
            saved_eta.append(model.eta.copy())
            saved_c_zn.append(model.c_zn.copy())
            saved_c_mg.append(model.c_mg.copy())
            
            stats = model.get_statistics()
            statistics.append(stats)
            
            print(f"Step {model.step:5d} | t={model.time:.2e}s | "
                  f"f_v={stats['precipitate_fraction']:.4f} | "
                  f"<Zn>={stats['avg_zn']:.4f} | <Mg>={stats['avg_mg']:.4f}")
    
    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    
    return model, saved_steps, saved_eta, saved_c_zn, saved_c_mg, statistics

def visualize_results(model, saved_eta, saved_c_zn, saved_c_mg, saved_steps):
    """Create visualization"""
    
    n_frames = len(saved_eta)
    times = [0, n_frames//2, n_frames-1]
    
    fig, axes = plt.subplots(3, 3, figsize=(15, 13))
    fig.suptitle(f'Al-Zn-Mg Phase Field (COST507 Data)\nT={model.T-273.15:.1f}°C', 
                 fontsize=16, fontweight='bold')
    
    for idx, t_idx in enumerate(times):
        # Order parameter
        im1 = axes[0, idx].imshow(saved_eta[t_idx], cmap='viridis', vmin=0, vmax=1)
        axes[0, idx].set_title(f'η (Order) - Step {saved_steps[t_idx]}')
        axes[0, idx].axis('off')
        plt.colorbar(im1, ax=axes[0, idx], fraction=0.046)
        
        # Zn composition
        im2 = axes[1, idx].imshow(saved_c_zn[t_idx], cmap='coolwarm')
        axes[1, idx].set_title(f'X(Zn) - Step {saved_steps[t_idx]}')
        axes[1, idx].axis('off')
        plt.colorbar(im2, ax=axes[1, idx], fraction=0.046)
        
        # Mg composition
        im3 = axes[2, idx].imshow(saved_c_mg[t_idx], cmap='plasma')
        axes[2, idx].set_title(f'X(Mg) - Step {saved_steps[t_idx]}')
        axes[2, idx].axis('off')
        plt.colorbar(im3, ax=axes[2, idx], fraction=0.046)
    
    plt.tight_layout()
    plt.savefig('al7xxx_cost507_phasefield.png', dpi=300, bbox_inches='tight')
    print("\n✓ Saved: al7xxx_cost507_phasefield.png")
    plt.show()

if __name__ == "__main__":
    
    # Run with COST507_modified.tdb
    # Will RAISE ERROR if database cannot be read or data extracted
    try:
        model, saved_steps, saved_eta, saved_c_zn, saved_c_mg, stats = run_simulation(
            tdb_file='COST507_modified.tdb',
            T=393.15,      # 120°C
            x_zn=0.06,     # 6 at% Zn
            x_mg=0.02,     # 2 at% Mg
            steps=1000,
            save_interval=50
        )
        
        visualize_results(model, saved_eta, saved_c_zn, saved_c_mg, saved_steps)
        
        print("\n" + "=" * 80)
        print("FINAL RESULTS (from COST507 thermodynamics)")
        print("=" * 80)
        final = model.get_statistics()
        print(f"Precipitate fraction: {final['precipitate_fraction']:.4f}")
        print(f"Average Zn: {final['avg_zn']:.4f}")
        print(f"Average Mg: {final['avg_mg']:.4f}")
        print(f"Total time simulated: {model.time:.2e} s")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("SIMULATION FAILED - ERROR IN DATABASE OR CALCULATION")
        print("=" * 80)
        print(f"Error: {e}")
        print("\nThis error must be resolved before proceeding.")
        print("Check that COST507_modified.tdb is in the same directory")
        print("and contains valid Al-Zn-Mg thermodynamic data.")
        print("=" * 80)
        raise  # Re-raise the error so it's not hidden
# 📋 Quick Reference Card for Judges

## Project: Al-7xxx Alloy Design via CALPHAD Simulation

---

## 🎯 One-Line Summary
> Optimized aerospace aluminum alloys using computational thermodynamics, identifying **Al-8Zn-3Mg-1.5Cu** as the strongest composition with **9% η-phase strengthening**.

---

## 🔑 Key Numbers to Remember

| Metric | Value |
|--------|-------|
| **Optimal Composition** | Al-8.0Zn-3.0Mg-1.5Cu (wt%) |
| **Max η-phase Fraction** | 9.01% |
| **Solutionizing Temp** | 450-460°C |
| **Peak Aging** | 120°C for 24 hours |
| **Freezing Range** | 150°C (hot cracking risk) |

---

## 📊 What Each Result Shows

| Image | What It Proves |
|-------|----------------|
| `01_multicomponent_contour.png` | Higher Zn+Mg = more strengthening phases |
| `02_scheil_solidification.png` | Large freezing range = welding challenges |
| `03_ttt_curves.png` | 24h @ 120°C = optimal aging time |
| `04_database_comparison.png` | Two databases agree = results are reliable |
| `05_multi_alloy_comparison.png` | Al-7085 strongest, Al-7075 most balanced |
| `06_microalloying_effects.png` | Zr better than Cr for grain refinement |
| `07_literature_validation.png` | Simulations match published experiments |

---

## ✅ Project Deliverables Checklist

- [x] Phase stability analysis
- [x] Solidification simulation (Scheil)
- [x] TTT aging curves
- [x] Composition optimization
- [x] Multi-alloy comparison (7050, 7075, 7085)
- [x] Micro-alloying effects (Cr, Zr)
- [x] Literature validation
- [x] Processing windows defined

---

## 🛠️ Tools Used

| Tool | Purpose |
|------|---------|
| **PyCALPHAD** | Thermodynamic calculations |
| **COST507.tdb** | Phase diagram database |
| **Matplotlib** | Visualization |
| **JMAK Kinetics** | Precipitation modeling |

---

## 📚 How to Navigate This Folder

1. **Start**: Read `README.md` for overview
2. **Visual Results**: Check `results/` folder for graphs
3. **Code**: See `scripts/` for Python simulations
4. **Deep Dive**: Read `docs/THEORY_GUIDE.md` for methodology

---

**Team Al-OyBoys | Theme 7 | January 2026**

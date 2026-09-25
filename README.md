# ⚙️ Lathe Machining Parameters & Machining Time Estimator

An interactive Streamlit web app that computes spindle speed (RPM), Material
Removal Rate (MRR) and turning time for a centre-lathe turning operation —
including a multi-pass reduction schedule, an interactive 3D lathe model, and
a 2D machining animation.

Built as a Python mini-project for **Diploma in Mechanical Engineering —
Semester 3**.

## 🔗 Live App

[Add your deployed Streamlit Community Cloud link here]

## Features

- **Machining Calculator** — enter workpiece diameter, target diameter,
  length of cut, feed per revolution, depth of cut per pass, and material;
  get a full pass-by-pass schedule (RPM, MRR, time per pass) plus totals
- **9-material database** with recommended cutting-speed ranges (Mild Steel,
  Medium Carbon Steel, Alloy Steel, Cast Iron, Stainless Steel, Aluminium,
  Brass, Copper, Titanium)
- **Input validation** — flags impossible values (final ≥ initial diameter,
  zero/negative feed or depth, oversized stock removal)
- **3D Lathe** — a real-time Three.js model of a centre lathe (bed,
  headstock, chuck, workpiece, tailstock, carriage, tool post); click any
  part for its name and function, and run a simulation that spins the chuck
  at the calculated RPM and feeds the carriage
- **2D Engineering Visualization** — an animated cross-section turning
  simulation (play / pause / restart) plus three labelled Matplotlib graphs:
  spindle speed vs diameter, machining time vs pass number, and diameter
  reduction per pass
- **Formulas** page showing every equation used
- Team details displayed in the sidebar and About page

## Formulas Used

| Quantity | Formula |
|---|---|
| Spindle Speed | `N = 1000 × Vc / (π × D)` (RPM) |
| Material Removal Rate | `MRR = Vc × f × ap × 1000` (mm³/min) |
| Turning Time per Pass | `t = L / (f × N)` (min) |
| Diameter after a Pass | `Dₙ = Dₙ₋₁ − 2×ap` |

Where `Vc` = cutting speed (m/min), `D` = diameter (mm), `f` = feed
(mm/rev), `ap` = depth of cut (mm), `L` = length of cut (mm).

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI and app framework
- [NumPy](https://numpy.org/) — numerical calculations
- [Matplotlib](https://matplotlib.org/) — graphs
- [Three.js](https://threejs.org/) (via CDN, embedded through
  `streamlit.components.v1.html`) — interactive 3D lathe model

## Project Structure

```
.
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md
```

## Run Locally

```bash
git clone <your-repo-url>
cd <your-repo-name>
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (public).
2. Go to [streamlit.io](https://streamlit.io/) and sign in with GitHub.
3. Click **New app**, select this repository and `app.py` as the entry
   point, then click **Deploy**.
4. Copy the live app link (e.g. `https://your-project.streamlit.app`).

## Team

- Group: `G-__`
- Members: *(see sidebar / About page in the app — edit the `TEAM` dict at
  the top of `app.py` before submitting)*
- Guide: *Faculty Guide Name*

## License

Educational project — for coursework submission.

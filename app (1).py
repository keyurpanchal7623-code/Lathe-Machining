"""
Lathe Machining Parameters & Machining Time Estimator
Diploma in Mechanical Engineering (Semester 3) — Python Mini Project
Framework: Streamlit | Libraries: streamlit, numpy, matplotlib

Run locally with:  streamlit run app.py
"""

import math
import time

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components

# ----------------------------------------------------------------------------------
# 0. TEAM DETAILS  -- EDIT ONLY THIS BLOCK BEFORE SUBMISSION
# ----------------------------------------------------------------------------------
TEAM = {
    "group_no": "Developers",
    "members": [
        {"name": "Keyur Panchal", "enrollment": "25012250610061"},
        {"name": "Dhruvil Panchal", "enrollment": "25012250610056"},
        {"name": "Shaurya Patel", "enrollment": "25012250610068"},
        {"name": "Het Thakkar", "enrollment": "25012250610048"},
    ],
    "guide": "Faculty Guide Name",
    "college": "Your College Name",
}

# ----------------------------------------------------------------------------------
# 1. PAGE CONFIG & THEME (navy / steel / orange industrial palette)
# ----------------------------------------------------------------------------------
st.set_page_config(
    page_title="Lathe Machining Estimator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-contrast industrial palette: near-black background, bright white text,
# a light steel-blue for borders/secondary text, a bright orange primary accent,
# and a cyan accent for anything that needs to stand apart from the orange.
NAVY = "#050A16"          # sidebar background (near-black navy)
BG = "#0A0F1C"             # main page background
CARD = "#16233A"           # card/panel background — lighter than BG for clear separation
STEEL = "#6D8CAD"          # borders — light enough to read against dark backgrounds
STEEL_LIGHT = "#E3ECF6"    # secondary text — bright, high contrast against CARD/BG
TEXT = "#F7FAFF"           # primary body text — near-white
ORANGE = "#FF8A1E"         # primary accent (buttons, headings, key values)
CYAN = "#2DE0FF"           # secondary accent — contrasts with orange, used sparingly

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG}; color: {TEXT}; }}
    section[data-testid="stSidebar"] {{ background-color: {NAVY}; }}
    section[data-testid="stSidebar"] * {{ color: {STEEL_LIGHT} !important; }}
    h1, h2, h3 {{ color: {ORANGE} !important; font-family: 'Trebuchet MS', sans-serif; }}
    p, li, label, span, div {{ color: {TEXT}; }}
    a {{ color: {CYAN} !important; }}
    .metric-card {{
        background-color: {CARD};
        border: 1px solid {STEEL};
        border-left: 5px solid {ORANGE};
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: {TEXT};
    }}
    .metric-card h3 {{ color: {CYAN} !important; }}
    .team-badge {{
        background-color: {CARD};
        border: 1px solid {STEEL};
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 0.9rem;
        color: {STEEL_LIGHT} !important;
    }}
    .team-badge * {{ color: {STEEL_LIGHT} !important; }}
    div[data-testid="stMetricValue"] {{ color: {ORANGE} !important; }}
    div[data-testid="stMetricLabel"] {{ color: {STEEL_LIGHT} !important; }}
    .stButton>button {{
        background-color: {ORANGE}; color: {NAVY} !important; font-weight: 700; border: none;
    }}
    .stButton>button:hover {{ background-color: {CYAN}; color: {NAVY} !important; }}
    thead tr th {{ background-color: {STEEL} !important; color: {NAVY} !important; }}
    tbody tr td {{ color: {TEXT} !important; }}
    .stAlert {{ color: {NAVY} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------------
# 2. MATERIAL DATABASE  (9 workpiece materials, recommended cutting speed Vc in m/min)
#    Ranges are typical HSS/carbide turning speeds from standard ME data tables.
# ----------------------------------------------------------------------------------
MATERIALS = {
    "Mild Steel (Low Carbon)":      {"vc_min": 90,  "vc_max": 130, "vc_default": 110, "color": "#9DB2BF"},
    "Medium Carbon Steel":          {"vc_min": 60,  "vc_max": 90,  "vc_default": 75,  "color": "#5C7285"},
    "Alloy Steel":                  {"vc_min": 40,  "vc_max": 70,  "vc_default": 55,  "color": "#425F70"},
    "Cast Iron (Grey)":             {"vc_min": 50,  "vc_max": 80,  "vc_default": 65,  "color": "#4A4A4A"},
    "Stainless Steel (Austenitic)": {"vc_min": 30,  "vc_max": 60,  "vc_default": 45,  "color": "#B8C4CE"},
    "Aluminium Alloy":              {"vc_min": 200, "vc_max": 400, "vc_default": 300, "color": "#C7D3DD"},
    "Brass (Free Cutting)":         {"vc_min": 150, "vc_max": 250, "vc_default": 200, "color": "#D4A24C"},
    "Copper":                       {"vc_min": 100, "vc_max": 200, "vc_default": 150, "color": "#C87941"},
    "Titanium Alloy":               {"vc_min": 20,  "vc_max": 50,  "vc_default": 35,  "color": "#7C8C94"},
}

# ----------------------------------------------------------------------------------
# 3. CORE ENGINEERING CALCULATIONS
# ----------------------------------------------------------------------------------
def spindle_rpm(vc, diameter_mm):
    """N = 1000 * Vc / (pi * D)   [rev/min], Vc in m/min, D in mm"""
    if diameter_mm <= 0:
        return 0.0
    return (1000.0 * vc) / (math.pi * diameter_mm)


def mrr(vc, feed_mm_rev, depth_mm):
    """MRR = Vc * f * d * 1000   [mm^3/min], Vc in m/min, f in mm/rev, d in mm"""
    return vc * feed_mm_rev * depth_mm * 1000.0


def pass_time(length_mm, feed_mm_rev, rpm):
    """t = L / (f * N)   [min]"""
    if feed_mm_rev <= 0 or rpm <= 0:
        return 0.0
    return length_mm / (feed_mm_rev * rpm)


def build_pass_table(d_start, d_final, length_mm, feed, depth_of_cut, vc):
    """
    Builds a multi-pass turning schedule.
    D_pass(n) = D_start - 2 * depth_of_cut * n   (diameter after n full passes)
    Stops early on the final pass if remaining stock < depth_of_cut.
    """
    rows = []
    d_current = d_start
    pass_no = 1
    guard = 0
    while d_current - d_final > 1e-6 and guard < 500:
        remaining = d_current - d_final
        ap_actual = min(depth_of_cut, remaining / 2.0)
        d_end = d_current - 2 * ap_actual
        n_rpm = spindle_rpm(vc, d_current)
        t_min = pass_time(length_mm, feed, n_rpm)
        m_rr = mrr(vc, feed, ap_actual)
        rows.append({
            "Pass": pass_no,
            "Start Dia. (mm)": round(d_current, 2),
            "End Dia. (mm)": round(d_end, 2),
            "Depth of Cut (mm)": round(ap_actual, 3),
            "Spindle Speed (RPM)": round(n_rpm, 1),
            "MRR (mm³/min)": round(m_rr, 1),
            "Time (min)": round(t_min, 3),
        })
        d_current = d_end
        pass_no += 1
        guard += 1
    return rows


# ----------------------------------------------------------------------------------
# 4. SESSION STATE (shared between Calculator / 3D Lathe / Visualization pages)
# ----------------------------------------------------------------------------------
defaults = {
    "d_start": 50.0, "d_final": 44.0, "length": 120.0,
    "feed": 0.2, "depth": 1.5, "material": "Mild Steel (Low Carbon)",
    "vc": 110.0, "computed": False, "rows": [], "total_time": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------------------------------------------------------------
# 5. SIDEBAR NAVIGATION
# ----------------------------------------------------------------------------------
st.sidebar.title("⚙️ Lathe Estimator")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Machining Calculator", "3D Lathe", "Engineering Visualization",
     "Formulas", "Materials", "About"],
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<div class='team-badge'><b>Group {TEAM['group_no']}</b><br>"
    + "<br>".join(f"{m['name']} ({m['enrollment']})" for m in TEAM["members"])
    + "</div>",
    unsafe_allow_html=True,
)

# ====================================================================================
# PAGE: HOME
# ====================================================================================
if page == "Home":
    st.title("🔧 Lathe Machining Parameters & Machining Time Estimator")
    st.markdown(
        "An interactive engineering tool to compute **spindle speed (RPM)**, "
        "**Material Removal Rate (MRR)** and **turning time per pass** for a "
        "centre-lathe turning operation — including a multi-pass reduction schedule, "
        "a 3D lathe model and 2D machining animation."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-card'><h3>🎯 Input</h3>Diameter, length of cut, "
                     "feed/rev, depth of cut, workpiece material</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-card'><h3>⚙️ Process</h3>Standard turning formulas "
                     "computed pass-by-pass as diameter reduces</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-card'><h3>📊 Output</h3>RPM, MRR, time/pass, total "
                     "time, 3D model, 2D animation, graphs</div>", unsafe_allow_html=True)
    st.info("Use the sidebar to open **Machining Calculator** first, then explore the "
            "**3D Lathe** and **Engineering Visualization** pages — both use the values "
            "you enter there.")
    st.markdown(f"<div class='team-badge'>Group {TEAM['group_no']} · {TEAM['college']} · "
                f"Guide: {TEAM['guide']}</div>", unsafe_allow_html=True)

# ====================================================================================
# PAGE: MACHINING CALCULATOR
# ====================================================================================
elif page == "Machining Calculator":
    st.title("🧮 Machining Calculator")

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("Inputs")
        material = st.selectbox("Workpiece Material", list(MATERIALS.keys()),
                                 index=list(MATERIALS.keys()).index(st.session_state["material"]))
        mat = MATERIALS[material]
        vc = st.slider(f"Cutting Speed Vc (m/min)  [recommended {mat['vc_min']}–{mat['vc_max']}]",
                        min_value=float(mat["vc_min"] * 0.5), max_value=float(mat["vc_max"] * 1.3),
                        value=float(mat["vc_default"]), step=1.0)

        d_start = st.number_input("Initial Workpiece Diameter D₀ (mm)", min_value=1.0, value=st.session_state["d_start"], step=1.0)
        d_final = st.number_input("Target Final Diameter D_f (mm)", min_value=0.1, value=st.session_state["d_final"], step=1.0)
        length = st.number_input("Length of Cut L (mm)", min_value=1.0, value=st.session_state["length"], step=1.0)
        feed = st.number_input("Feed per Revolution f (mm/rev)", min_value=0.01, value=st.session_state["feed"], step=0.01, format="%.2f")
        depth = st.number_input("Depth of Cut per Pass aₚ (mm)", min_value=0.05, value=st.session_state["depth"], step=0.05, format="%.2f")

        errors = []
        if d_final >= d_start:
            errors.append("Final diameter must be **smaller** than the initial diameter.")
        if d_final <= 0:
            errors.append("Final diameter must be greater than zero.")
        if feed <= 0:
            errors.append("Feed per revolution must be positive.")
        if depth <= 0:
            errors.append("Depth of cut must be positive.")
        if (d_start - d_final) / 2 > 25:
            errors.append("Total stock to remove is unusually large (>25 mm on radius) — check inputs.")

        for e in errors:
            st.error(e)

        compute = st.button("▶ Compute", disabled=bool(errors))

    if compute and not errors:
        rows = build_pass_table(d_start, d_final, length, feed, depth, vc)
        st.session_state.update({
            "d_start": d_start, "d_final": d_final, "length": length, "feed": feed,
            "depth": depth, "material": material, "vc": vc, "computed": True,
            "rows": rows, "total_time": sum(r["Time (min)"] for r in rows),
        })

    with right:
        if st.session_state["computed"] and st.session_state["rows"]:
            rows = st.session_state["rows"]
            first, last = rows[0], rows[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Passes Required", len(rows))
            m2.metric("Spindle Speed (Pass 1)", f"{first['Spindle Speed (RPM)']} RPM")
            m3.metric("MRR (Pass 1)", f"{first['MRR (mm³/min)']} mm³/min")
            m4.metric("Total Turning Time", f"{st.session_state['total_time']:.2f} min")

            st.subheader("Pass-by-Pass Schedule")
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.subheader("Single-Pass Summary (Pass 1 → theoretical, if machined in one cut)")
            n1 = spindle_rpm(vc, d_start)
            mrr1 = mrr(vc, feed, depth)
            t1 = pass_time(length, feed, n1)
            s1, s2, s3 = st.columns(3)
            s1.metric("Spindle Speed N", f"{n1:.1f} RPM")
            s2.metric("MRR", f"{mrr1:.1f} mm³/min")
            s3.metric("Time for this cut", f"{t1:.2f} min")
        else:
            st.warning("Enter valid inputs on the left and click **Compute** to see results.")

# ====================================================================================
# PAGE: 3D LATHE
# ====================================================================================
elif page == "3D Lathe":
    st.title("🌀 Interactive 3D Lathe Model")
    st.caption("Drag to orbit, scroll to zoom, click a part to see its name. "
               "Toggle simulation to spin the chuck at the RPM computed on the "
               "Machining Calculator page.")

    if not st.session_state["computed"]:
        st.warning("Go to **Machining Calculator** and click Compute first — "
                    "the simulation uses Pass-1 RPM and feed from there. "
                    "Showing default values for now.")
        n_rpm = spindle_rpm(st.session_state["vc"], st.session_state["d_start"])
        feed_val = st.session_state["feed"]
    else:
        n_rpm = st.session_state["rows"][0]["Spindle Speed (RPM)"]
        feed_val = st.session_state["feed"]

    st.markdown(f"**Simulated Spindle Speed:** {n_rpm:.1f} RPM &nbsp;&nbsp; "
                f"**Feed:** {feed_val:.2f} mm/rev")

    lathe_html = f"""
    <div id="lathe-container" style="width:100%;height:560px;border-radius:10px;overflow:hidden;background:{BG};position:relative;">
      <div id="tooltip" style="position:absolute;top:10px;left:10px;background:{CARD};color:{ORANGE};
           padding:6px 12px;border-radius:6px;font-family:sans-serif;font-size:14px;border:1px solid {STEEL};">
           Click a part of the lathe
      </div>
      <div style="position:absolute;top:10px;right:10px;">
        <button id="simBtn" style="background:{ORANGE};color:{NAVY};font-weight:700;border:none;
             padding:8px 16px;border-radius:6px;cursor:pointer;">▶ Run Simulation</button>
      </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    (function() {{
      const container = document.getElementById('lathe-container');
      const RPM = {n_rpm};
      const FEED = {feed_val};

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x0E1626);
      const camera = new THREE.PerspectiveCamera(45, container.clientWidth/container.clientHeight, 0.1, 1000);
      camera.position.set(60, 45, 90);

      const renderer = new THREE.WebGLRenderer({{antialias:true}});
      renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(renderer.domElement);

      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.target.set(0, 10, 0);
      controls.update();

      scene.add(new THREE.AmbientLight(0xffffff, 0.6));
      const dir = new THREE.DirectionalLight(0xffffff, 0.8);
      dir.position.set(50, 80, 50);
      scene.add(dir);

      const steel = new THREE.MeshStandardMaterial({{color: 0x6D8CAD, metalness:0.6, roughness:0.4}});
      const navy  = new THREE.MeshStandardMaterial({{color: 0x0F1B30, metalness:0.4, roughness:0.6}});
      const orange= new THREE.MeshStandardMaterial({{color: 0xFF8A1E, metalness:0.5, roughness:0.3}});
      const bronze= new THREE.MeshStandardMaterial({{color: 0x2DE0FF, metalness:0.6, roughness:0.35}});

      const parts = [];
      function addPart(mesh, name, info) {{
        mesh.userData = {{name: name, info: info}};
        scene.add(mesh);
        parts.push(mesh);
        return mesh;
      }}

      // Bed
      const bed = new THREE.Mesh(new THREE.BoxGeometry(90, 4, 18), navy);
      bed.position.set(0, 0, 0);
      addPart(bed, "Lathe Bed", "Rigid base guiding the carriage along the machine axis.");

      // Headstock
      const headstock = new THREE.Mesh(new THREE.BoxGeometry(16, 18, 16), steel);
      headstock.position.set(-35, 12, 0);
      addPart(headstock, "Headstock", "Houses the main spindle drive and gearbox.");

      // Chuck (rotating)
      const chuckGroup = new THREE.Group();
      const chuck = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 5, 24), orange);
      chuck.rotation.z = Math.PI/2;
      chuckGroup.add(chuck);
      chuckGroup.position.set(-25, 12, 0);
      scene.add(chuckGroup);
      addPart(chuck, "3-Jaw Chuck", "Clamps and rotates the workpiece with the spindle.");

      // Workpiece (rotates with chuck)
      const workpieceGroup = new THREE.Group();
      const workpiece = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 40, 24), bronze);
      workpiece.rotation.z = Math.PI/2;
      workpiece.position.set(-3, 0, 0);
      workpieceGroup.add(workpiece);
      workpieceGroup.position.set(-22, 12, 0);
      scene.add(workpieceGroup);
      addPart(workpiece, "Workpiece", "Raw stock being turned to the target diameter.");

      // Tailstock
      const tailstock = new THREE.Mesh(new THREE.BoxGeometry(10, 14, 14), steel);
      tailstock.position.set(30, 11, 0);
      addPart(tailstock, "Tailstock", "Supports the free end of long workpieces.");

      // Carriage + tool post (moves along Z-axis of lathe = X here)
      const carriageGroup = new THREE.Group();
      const carriage = new THREE.Mesh(new THREE.BoxGeometry(8, 3, 20), navy);
      carriage.position.set(0, 4, 0);
      carriageGroup.add(carriage);
      const toolpost = new THREE.Mesh(new THREE.BoxGeometry(4, 6, 4), orange);
      toolpost.position.set(0, 8, 6);
      carriageGroup.add(toolpost);
      const tool = new THREE.Mesh(new THREE.BoxGeometry(6, 2, 2), steel);
      tool.position.set(0, 11, 3);
      carriageGroup.add(tool);
      carriageGroup.position.set(-22, 5, 0);
      scene.add(carriageGroup);
      addPart(carriage, "Carriage", "Slides along the bed carrying the cross-slide and tool post.");
      addPart(toolpost, "Tool Post", "Holds the cutting tool at the correct height and angle.");
      addPart(tool, "Cutting Tool", "Removes material from the rotating workpiece.");

      // Raycasting for click labels
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      const tooltip = document.getElementById('tooltip');
      renderer.domElement.addEventListener('click', (e) => {{
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const hits = raycaster.intersectObjects(parts);
        if (hits.length > 0) {{
          const d = hits[0].object.userData;
          tooltip.innerHTML = "<b>" + d.name + "</b><br>" + d.info;
        }}
      }});

      // Simulation toggle
      let simulating = false;
      let carriageX = -22;
      const minX = -22, maxX = 18;
      document.getElementById('simBtn').addEventListener('click', () => {{
        simulating = !simulating;
        document.getElementById('simBtn').innerText = simulating ? "⏸ Pause Simulation" : "▶ Run Simulation";
      }});

      const clock = new THREE.Clock();
      function animate() {{
        requestAnimationFrame(animate);
        const dt = clock.getDelta();
        if (simulating) {{
          const radPerSec = (RPM / 60) * 2 * Math.PI * 0.15; // scaled for visibility
          chuckGroup.rotation.x += radPerSec * dt;
          workpieceGroup.rotation.x += radPerSec * dt;
          carriageX += FEED * 6 * dt;
          if (carriageX > maxX) carriageX = minX;
          carriageGroup.position.x = carriageX;
        }}
        controls.update();
        renderer.render(scene, camera);
      }}
      animate();

      window.addEventListener('resize', () => {{
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
      }});
    }})();
    </script>
    """
    components.html(lathe_html, height=580, scrolling=False)

# ====================================================================================
# PAGE: ENGINEERING VISUALIZATION
# ====================================================================================
elif page == "Engineering Visualization":
    st.title("📈 Engineering Visualization")

    if not st.session_state["computed"] or not st.session_state["rows"]:
        st.warning("Go to **Machining Calculator** and click Compute first.")
    else:
        rows = st.session_state["rows"]
        passes = [r["Pass"] for r in rows]
        start_d = [r["Start Dia. (mm)"] for r in rows]
        end_d = [r["End Dia. (mm)"] for r in rows]
        rpms = [r["Spindle Speed (RPM)"] for r in rows]
        times = [r["Time (min)"] for r in rows]
        cum_times = list(np.cumsum(times))

        st.subheader("2D Turning Animation")
        n_rpm = rows[0]["Spindle Speed (RPM)"]
        feed_val = st.session_state["feed"]
        length_val = st.session_state["length"]
        d0 = st.session_state["d_start"]
        anim_html = f"""
        <div style="background:{BG};border-radius:10px;padding:10px;">
        <canvas id="turnCanvas" width="760" height="260" style="background:{CARD};border-radius:8px;"></canvas>
        <div style="margin-top:8px;">
          <button id="playBtn" style="background:{ORANGE};color:{NAVY};font-weight:700;border:none;padding:6px 14px;border-radius:6px;">▶ Play</button>
          <button id="pauseBtn" style="background:{STEEL};color:{NAVY};font-weight:700;border:none;padding:6px 14px;border-radius:6px;">⏸ Pause</button>
          <button id="restartBtn" style="background:{STEEL};color:{NAVY};font-weight:700;border:none;padding:6px 14px;border-radius:6px;">⟲ Restart</button>
          <span style="color:{STEEL_LIGHT};margin-left:10px;">Cross-section view — tool sweeps left→right removing stock</span>
        </div>
        </div>
        <script>
        (function() {{
          const canvas = document.getElementById('turnCanvas');
          const ctx = canvas.getContext('2d');
          const N = {n_rpm};
          const FEED = {feed_val};
          const L = {length_val};
          const D0 = {d0};
          let toolX = 60;
          const startX = 60, endX = 680;
          let running = false, angle = 0;
          let lastT = null;

          function draw() {{
            ctx.clearRect(0,0,canvas.width,canvas.height);
            // workpiece (side view, tapering where tool has passed)
            const cy = 130, rMax = 60, rCut = 40;
            ctx.fillStyle = '{STEEL_LIGHT}';
            ctx.fillRect(startX, cy - rMax, toolX - startX, rMax*2);
            ctx.fillStyle = '{CYAN}';
            ctx.fillRect(toolX, cy - rCut, endX - toolX, rCut*2);
            // rotation hatch marks on turned (cut) section
            ctx.strokeStyle = 'rgba(5,10,22,0.35)';
            for (let x = startX+5; x < toolX; x += 14) {{
              ctx.beginPath();
              ctx.moveTo(x, cy - rMax);
              ctx.lineTo(x, cy + rMax);
              ctx.stroke();
            }}
            // chuck
            ctx.fillStyle = '{ORANGE}';
            ctx.fillRect(startX-25, cy-70, 25, 140);
            // tool post + tool
            ctx.fillStyle = '{STEEL}';
            ctx.fillRect(toolX-6, 20, 12, cy-rCut-20);
            ctx.fillStyle = '{TEXT}';
            ctx.fillRect(toolX-4, cy-rCut-6, 8, 10);
            // spin indicator on chuck face
            ctx.save();
            ctx.translate(startX-12, cy);
            ctx.rotate(angle);
            ctx.strokeStyle = '{NAVY}';
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(-10,0); ctx.lineTo(10,0); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(0,-10); ctx.lineTo(0,10); ctx.stroke();
            ctx.restore();
            // labels
            ctx.fillStyle = '{STEEL_LIGHT}';
            ctx.font = '12px sans-serif';
            ctx.fillText('RPM: ' + N.toFixed(0) + '   Feed: ' + FEED.toFixed(2) + ' mm/rev', 10, 20);
          }}

          function step(t) {{
            if (lastT === null) lastT = t;
            const dt = (t - lastT) / 1000;
            lastT = t;
            if (running) {{
              angle += (N/60) * 2*Math.PI * dt * 0.3;
              toolX += (FEED * 40) * dt;
              if (toolX > endX) toolX = endX;
            }}
            draw();
            requestAnimationFrame(step);
          }}
          draw();
          requestAnimationFrame(step);

          document.getElementById('playBtn').onclick = () => running = true;
          document.getElementById('pauseBtn').onclick = () => running = false;
          document.getElementById('restartBtn').onclick = () => {{ toolX = startX; angle = 0; running=false; draw(); }};
        }})();
        </script>
        """
        components.html(anim_html, height=340, scrolling=False)

        st.subheader("Graphs")
        g1, g2 = st.columns(2)

        with g1:
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            ax1.plot(start_d, rpms, marker="o", color="#E8590C")
            ax1.set_xlabel("Diameter (mm)")
            ax1.set_ylabel("Spindle Speed (RPM)")
            ax1.set_title("Spindle Speed vs Diameter")
            ax1.grid(True, alpha=0.3)
            ax1.invert_xaxis()
            st.pyplot(fig1)

        with g2:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            ax2.bar(passes, times, color="#1B4965", label="Time per pass")
            ax2.plot(passes, cum_times, marker="o", color="#E8590C", label="Cumulative time")
            ax2.set_xlabel("Pass Number")
            ax2.set_ylabel("Time (min)")
            ax2.set_title("Machining Time vs Passes")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(10, 3.5))
        ax3.plot(passes, start_d, marker="o", label="Start Diameter", color="#E8590C")
        ax3.plot(passes, end_d, marker="s", label="End Diameter", color="#1B4965")
        ax3.set_xlabel("Pass Number")
        ax3.set_ylabel("Diameter (mm)")
        ax3.set_title("Diameter Reduction per Pass")
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        st.pyplot(fig3)

# ====================================================================================
# PAGE: FORMULAS
# ====================================================================================
elif page == "Formulas":
    st.title("📐 Formulas Used")
    st.markdown(r"""
    **1. Spindle Speed (RPM)**
    $$ N = \dfrac{1000 \, V_c}{\pi D} $$
    where $V_c$ = cutting speed (m/min), $D$ = workpiece diameter at that pass (mm)

    **2. Material Removal Rate (MRR)**
    $$ MRR = V_c \times f \times a_p \times 1000 \quad \text{(mm}^3\text{/min)} $$
    where $f$ = feed per revolution (mm/rev), $a_p$ = depth of cut (mm)

    **3. Turning Time per Pass**
    $$ t = \dfrac{L}{f \times N} \quad \text{(min)} $$
    where $L$ = length of cut (mm)

    **4. Diameter after a Pass**
    $$ D_{n} = D_{n-1} - 2 a_p $$

    **5. Total Machining Time**
    $$ T_{total} = \sum_{i=1}^{n} t_i $$
    """)

# ====================================================================================
# PAGE: MATERIALS
# ====================================================================================
elif page == "Materials":
    st.title("🧱 Material Database")
    st.markdown("Recommended turning cutting speeds ($V_c$) for HSS/carbide tooling, "
                "from standard machining data tables.")
    table = [
        {"Material": k, "Vc min (m/min)": v["vc_min"], "Vc max (m/min)": v["vc_max"],
         "Default Vc (m/min)": v["vc_default"]}
        for k, v in MATERIALS.items()
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)

# ====================================================================================
# PAGE: ABOUT
# ====================================================================================
elif page == "About":
    st.title("ℹ️ About This Project")
    st.markdown(f"""
    **Project:** Lathe Machining Parameters & Machining Time Estimator
    **Course:** Diploma in Mechanical Engineering — Semester 3
    **Framework:** Python & Streamlit (streamlit, numpy, matplotlib)

    **Group:** {TEAM['group_no']}
    **Guide:** {TEAM['guide']}
    **College:** {TEAM['college']}

    **Members:**
    """)
    for m in TEAM["members"]:
        st.markdown(f"- {m['name']} — {m['enrollment']}")
    st.markdown("""
    ---
    This app computes spindle speed, material removal rate and turning time for a
    lathe turning operation, extended into a multi-pass reduction schedule, an
    interactive 3D lathe model, and a 2D machining animation, so a user can explore
    how machining parameters change as the workpiece is turned down to its final
    diameter.
    """)

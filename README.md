# On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics

<p align="center">
  <a href="https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/"><strong>🌐 Interactive Survey Portal</strong></a> |
  <a href="https://cdfg.csail.mit.edu/"><strong>🏛️ MIT CSAIL CDFG</strong></a>
</p>

---

## Authors

**Zhiyang Dou**<sup>1</sup>, **Akihisa Watanabe**<sup>1</sup>, **Jamison Meindl**<sup>1</sup>, **Anna Deng**<sup>1</sup>, **Tianyu Huang**<sup>1</sup>, **Igor Sadalski**<sup>1</sup>, **Harrison Liang**<sup>1</sup>, **Minghao Guo**<sup>1</sup>, **Benjamin Tod Jones**<sup>1</sup>, **Wojciech Matusik**<sup>1</sup>

<sup>1</sup>*Computational Design and Fabrication Group (CDFG), MIT CSAIL*

---

## Overview

Frontier multimodal foundation models demonstrate emergent capabilities to construct 3D environments, synthesize native parametric CAD assemblies, and operate robotic controllers through standard software harnesses. Because early breakthroughs circulate primarily through public demonstrations and technical reports with uneven documentation, the empirical record has remained fragmented. 

To establish a rigorous foundation, this project systematically analyzes over 190 community demonstrations, technical reports, and benchmark evaluations, cross-checking empirical claims against accessible code, execution logs, and evaluation protocols to treat this corpus as a distributed, crowdsourced natural experiment.

### Key Dimensions Covered
- **3D Spatial Perception & Reconstruction**: Advancements in single-view/multi-view geometry, neural radiance/Gaussian representations, and direct mesh synthesis.
- **Parametric CAD & Computational Design**: Code-based parametric synthesis across Open CASCADE, CadQuery, Blender Python API, and visual programming graphs.
- **Embodied Robotics & Control**: Policy grounding across MuJoCo, Isaac Sim, Genesis, and physical bimanual/quadrupedal execution.
- **Three-Tier Evidence Hierarchy**: Classification of all demonstrations into Rank 1 (Code & Data Reproducible), Rank 2 (Interactive Web/App Deployments), and Rank 3 (Demonstration-Only Media).

---

## Interactive Web Portal

The interactive web portal is deployed and publicly accessible at:
👉 **[https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/](https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/)**

The portal features:
1. **Full Survey HTML Reader**: Complete, unabridged paper sections with vector diagrams, mathematical formulas, and section-by-section TOC navigation.
2. **Benchmark Dashboard**: Quantitative model evaluations, error rate breakdowns, and cross-architecture radar comparisons.
3. **Visual Case Archive**: Searchable and filterable archive of over 170+ community showcases categorized by domain (3D Modeling, CAD, Robotics, Physics Simulation) and reproducibility tier.
4. **BibTeX Export**: One-click citation copy for academic citations.

---

## Repository Structure

```
.
├── index.html              # Main web portal (standalone responsive HTML5)
├── css/
│   └── style.css           # Academic design system styling
├── js/
│   └── main.js             # Navigation, scrollspy, and filter logic
├── fonts/                  # Publication typography (Linux Biolinum, Libertine, Inconsolata)
├── assets/                 # Figures, benchmark diagrams, and media thumbnails
│   ├── figures/            # Paper figures (vector SVGs and high-res diagrams)
│   ├── gallery/            # Visual case archive thumbnails
│   └── logos/              # MIT CSAIL CDFG brand assets
└── build_website.py        # Site compilation script
```

---

## Local Development

To run the survey web portal locally:

```bash
# Clone the repository
git clone https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics.git
cd awesome-ai-3d-modeling-robotics

# Start a local HTTP server
python3 -m http.server 8000
```

Open your browser at `http://localhost:8000`.

To recompile the web portal from source:

```bash
python3 build_website.py
```

---

## Citation

If you find this survey or archive useful for your research, please cite:

```bibtex
@article{dou2026frontier3drobotics,
  title={On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics},
  author={Dou, Zhiyang and Watanabe, Akihisa and Meindl, Jamison and Deng, Anna and Huang, Tianyu and Sadalski, Igor and Liang, Harrison and Guo, Minghao and Jones, Benjamin Tod and Matusik, Wojciech},
  journal={MIT CSAIL Research Report},
  year={2026},
  month={September},
  institution={Computational Design and Fabrication Group (CDFG), MIT CSAIL},
  url={https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/},
  note={Working draft, living survey}
}
```

---

## License & Affiliation

Maintained by the **Computational Design and Fabrication Group (CDFG)**, MIT CSAIL.  
Website and documentation content are made available for research and academic study.

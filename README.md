# On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics

<p align="center">
  <a href="https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/"><strong>🌐 Interactive Survey Portal</strong></a> |
  <a href="https://cdfg.csail.mit.edu/"><strong>🏛️ MIT CSAIL CDFG</strong></a>
</p>

---

## Authors

**Zhiyang Dou**<sup>1</sup>, **Jamison Meindl**<sup>1</sup>, **Akihisa Watanabe**<sup>1</sup>, **Anna Deng**<sup>1</sup>, **Tianyu Huang**<sup>1</sup>, **Igor Sadalski**<sup>1</sup>, **Harrison Liang**<sup>1</sup>, **Minghao Guo**<sup>1</sup>, **Benjamin Tod Jones**<sup>1</sup>, **Wojciech Matusik**<sup>1</sup>

<sup>1</sup>*Computational Design and Fabrication Group (CDFG), MIT CSAIL*

---

## Overview

Recent frontier multimodal models, including GPT-6 Astra, Claude Opus 5.5 and Fable 5.1, and Gemini 3.8 Flash, exhibit capabilities in 3D modeling, computational design and robotics that earlier models lacked. The most current evidence of these capabilities comes from public demonstrations and vendor reports, which appear well before peer-reviewed evaluations. This survey collects and verifies 328 demonstrations and their accompanying benchmark evaluations across 232 case groups to assess what these models can reliably accomplish and where human expertise remains necessary. It is maintained as a live record that is updated as new results appear. The record shows that *3D spatial perception, geometric reasoning and scene understanding have advanced substantially over previous model generations*, and it supports three findings about what this advance means in practice. First, frontier models are now effective drafting tools for 3D and CAD work: they produce editable scenes and parametric assemblies containing hundreds of verified solids and improve substantially over prior generations on standardized CAD benchmarks, although confirming conformance to tolerances and manufacturability requires further evaluation. Second, in robotics, models are most effective in offline development, where they synthesize controllers in simulation for subsequent deployment on hardware. This is because multi-second inference latency precludes fast closed-loop control and online action selection succeeds on coarse manipulation but not on precise, contact-rich tasks. Third, reported performance depends substantially on the software interfaces connecting a model to its tools, so benchmark results characterize complete model and harness systems rather than models in isolation. We organize this evidence by interface, development mode and feedback mechanism, identify applications where these models already alter practice, and outline the open problems in physical safety, attribution and evaluation that must be resolved before real-world adoption.

### Key Dimensions Covered
- **3D Spatial Perception & Reconstruction**: Advancements in single-view/multi-view geometry, neural radiance/Gaussian representations, and direct mesh synthesis.
- **Parametric CAD & Computational Design**: Code-based parametric synthesis across Open CASCADE, CadQuery, Blender Python API, and visual programming graphs.
- **Embodied Robotics & Control**: Policy grounding across MuJoCo, Isaac Sim, Genesis, and physical bimanual/quadrupedal execution.
- **Three-Tier Evidence Hierarchy**: Classification of all demonstrations into Rank 1 (Code Provided), Rank 2 (Interactive Verification), and Rank 3 (Demonstration Only).

---

## Interactive Web Portal

The interactive web portal is deployed and publicly accessible at:
👉 **[https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/](https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/)**

The portal features:
1. **Full Survey HTML Reader**: Complete, unabridged paper sections with vector diagrams, mathematical formulas, and section-by-section TOC navigation.
2. **Benchmark Dashboard**: Quantitative model evaluations and error rate breakdowns.
3. **Visual Case Archive**: Searchable and filterable archive of 232 community showcases categorized by domain (3D Modeling, CAD, Robotics, Animation) and reproducibility tier.
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
git clone https://github.com/MIT-CDFG/Survey-AI-for-3D-modeling-Robotics.git
cd Survey-AI-for-3D-modeling-Robotics

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
  author={Dou, Zhiyang and Meindl, Jamison and Watanabe, Akihisa and Deng, Anna and Huang, Tianyu and Sadalski, Igor and Liang, Harrison and Guo, Minghao and Jones, Benjamin Tod and Matusik, Wojciech},
  journal={MIT CSAIL Research Report},
  year={2026},
  month={September},
  institution={Computational Design and Fabrication Group (CDFG), MIT CSAIL},
  url={https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/},
  note={Living survey}
}
```

---

## License & Affiliation

Maintained by the **Computational Design and Fabrication Group (CDFG)**, MIT CSAIL.  
Website and documentation content are made available for research and academic study.

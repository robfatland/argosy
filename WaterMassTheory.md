# Water-Mass Theory — a research-framing note

Working doc (not in the Jupyter Book). Captures a hypothesis that emerged from eyeballing
shallow-profiler (SP) temperature profiles, and where it sits in the physical-oceanography
literature. Intended as a potential paper angle, not settled analysis.

> **Status:** speculative framing + first literature anchor (web search, 2026-10-10). NOT yet a
> rigorous review — see "Next" for using the Asta/Semantic-Scholar MCP to do a real citation-graph
> review. References below were found by general web search; verify and expand before citing.


## The suspicion (Rob's framing)

SP temperature profiles often show structure that is clearly **signal, not noise**, on a vertical
scale of ~10–100 m. This structure:

- **persists** from one profile to the next (and across many profiles),
- **evolves** — gradually changing shape over time,
- behaves as if the upper ocean were composed of **three-dimensional masses of water**, stacked
  or abutting, that are:
  - **elastic** (deformable),
  - **advected** by currents,
  - subject to **boundary behavior** such as heat exchange,
  - possessed of a degree of **integrity** that can be **disrupted** (e.g. by turbulence).

The question: to what extent has the research community already articulated this picture?


## Where this sits in physical oceanography

The suspicion is well-founded; it is a rediscovery of several established, still-active strands.

- **Water masses + T–S analysis.** Since Helland-Hansen (~1916), the ocean is read as stacked
  water masses, each with a conservative T–S signature set at a formation region, then spread and
  modified. A vertical profile = a sequence of water-mass layers meeting at interfaces. The T–S
  diagram is the classic tool (mixing of two masses → a line between them).

- **Thermohaline intrusions / interleaving** — the closest match to the 10–100 m persistent-but-
  evolving structure. Layers of one water mass push laterally into another at fronts, driven by
  horizontal T/S gradients; a key horizontal-mixing mechanism.

- **Thermohaline staircases + double diffusion** — "stacked masses with interfaces of a certain
  integrity." Well-defined stepped T/S structures; their time evolution includes **spontaneous
  layer-merging** (layers losing integrity and combining) — directly matching the "integrity that
  can be disrupted" intuition.

- **Submesoscale stirring vs turbulent mixing.** Intrusions are shaped ("elastic, advected") by
  submesoscale/mesoscale currents and eroded by shear-driven turbulence and double diffusion. The
  interface-stability-vs-mixing competition is governed by the Richardson number / Kelvin–Helmholtz
  instability; microstructure (Osborn, Gregg) measures the erosion.

- **Coherent vortices (meddies, submesoscale coherent vortices).** The clearest case of a water
  mass with genuine **object-like integrity** — retains identity for months–years while advected.
  This is where Rob's "bounded elastic mass" framing is most literally supported; elsewhere the
  field treats masses more statistically/thermodynamically than as bounded objects.


## The under-exploited angle (why SP data is special here)

Most intrusion/interleaving work comes from **spatial surveys** or **shorter mooring records**.
The RCA shallow profiler offers something unusual: **multi-year, ~9-profiles/day, single-point**
sampling of the upper ~200 m. Reading persistence and evolution of layered water-mass structure
from that high-cadence time series — structure drifting past and deforming as masses are advected
through the site — appears to be a genuinely underexploited vantage. A fixed point sees mesoscale
eddies / fronts pass by (days–weeks timescales); the SP cadence resolves the evolution within each.


## First literature anchors (unverified; found by web search 2026-10-10)

Rephrased for compliance; confirm and expand via Asta MCP before citing.

- Eurasian Basin intrusive layering, intrusions of **vertical scale 40–100 m** in upper layers —
  JGR Oceans 2011, https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2010JC006920
- Intrusions evolving on **inertial (~23 h) and sub-inertial (~10 day)** scales via **differential
  lateral advection**; interpreted as 3-D submesoscale turbulence of a frontal zone driven by the
  mesoscale — JPO (jpo4373), https://staff.washington.edu/shcher/papers/jpo4373.pdf  (UW)
- Thermohaline **staircases** and **spontaneous layer-merging** — "Double-Diffusive Recipes Part
  II," JPO 2013, https://journals.ametsoc.org/doi/full/10.1175/JPO-D-13-0156.1
- Stratification change at a mooring from **passage of mesoscale eddies** (8–13 day & longer) —
  NW Sea of Japan, Springer 2021, https://link.springer.com/article/10.1134/S0001437021030152
- Multilayered intrusions from **baroclinic instability / vertical shear** at a front — South Sea
  of Korea, JGR 2010, https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2009JC005266
- Double-diffusive layering with lateral T/S gradients, Canada Basin — JGR 2019,
  https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018JC014368

Search anchor terms for the real review: *water mass analysis / T–S diagram; thermohaline
intrusions & interleaving; thermohaline staircases; double diffusion; submesoscale fronts &
filaments; coherent vortices (meddies / SCVs); ocean microstructure & mixing; Richardson number /
Kelvin–Helmholtz.* Names: Munk, Osborn, Gregg, Polzin (mixing); Thomas, Ferrari, McWilliams,
Mahadevan (submesoscale).


## Next

- **Do a rigorous citation-graph literature review via the Asta/Semantic-Scholar MCP** (AI2's
  Scientific Corpus Tool, endpoint `https://asta-tools.allen.ai/mcp/v1`, see the chat note +
  SessionState reminder). Start from the anchors above, traverse citations/references, and build a
  properly cited section. This note's references are web-search-grade only.
- Then: assess whether the SP-time-series angle is already staked out or open, and whether argosy's
  pp06 record can demonstrate persistence/evolution of a specific intrusion/layer quantitatively.

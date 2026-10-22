# Seeking Research


What sorts of research topics can we articulate and pursue? This is a working document
(not in the Jupyter book) informed by various searches and by bias from looking at a
lot of profile data.


## Water-Mass Theory

WMT is a hypothesis that emerges from examining many shallow-profiler (SP) temperature profiles.
How is it reflected in physical-oceanography literature? 


> **Status:** speculative framing + first literature anchor (web search, 2026-10-10). NOT yet a
> rigorous review — see "Next" for using the Asta/Semantic-Scholar MCP to do a real citation-graph
> review. References below are fragmentary.


## Rob's framing


SP temperature profiles often show structure: **signal, not noise**, on a vertical
scale of ~10–100 m. This structure:

- **persists** from one profile to the next (and across many profiles),
- **evolves** — gradually changing shape over time,
- behaves as if the upper ocean were composed of **three-dimensional masses of water**, stacked
  or layered or abutting; masses that are:
  - **elastic**, deformable
  - **advected** by current
  - subject to **boundary behavior** such as heat exchange,
  - have **integrity** that can be **disrupted** (e.g. by turbulence).


Already articulated in the literature?


## In physical oceanography


Supported by established active research.


- **Water masses + T–S analysis.** Since Helland-Hansen (~1916), the ocean is read as stacked
water masses, each with a conservative T–S signature set at a formation region, then spread and
modified. A vertical profile = a sequence of water-mass layers meeting at interfaces. The T–S
diagram can show mixing of two masses; need an example.


- **Thermohaline intrusions / interleaving** matches "10–100 m persistent-but-
evolving structure". Layers of one water mass push laterally into another at fronts, driven by
horizontal T/S gradients: A horizontal-mixing mechanism.


- **Thermohaline staircases + double diffusion** Well-defined stepped T/S structures; time 
evolution includes **spontaneous layer-merging** (layers lose integrity, combine).


- **Submesoscale stirring vs turbulent mixing.** Intrusions are shaped ("elastic, advected") by
submesoscale/mesoscale currents and eroded by shear-driven turbulence and double diffusion. The
interface-stability-vs-mixing competition is governed by the Richardson number / Kelvin–Helmholtz
instability; microstructure (Osborn, Gregg) measures the erosion.


- **Coherent vortices (meddies, submesoscale coherent vortices).**: Water
masses with **object-like integrity** — retains identity for months–years while advected.


## SP value


Most intrusion/interleaving work comes from **spatial surveys** or **shorter mooring records**.
The RCA SP (**multi-year, ~9-profiles/day, single-point**) reads persistence and evolution of 
layered water-mass structure from time series: Structure drifting past and deforming as masses 
are advected through the site. The literature does not seem to be caught up. The fixed point aspect
observes mesoscale eddies / fronts pass by on days–weeks timescales.


## Missing piece of the puzzle



A single-point time series can't separate advection past the sensor from in-place evolution without velocity context — so the ADCP/current-synthesis thread is what makes Water Mass Theory testable rather than suggestive.



## Some related papers (web search 2026-10-10)



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


## Suggestion: Search anchor terms for reviews: 

- *water mass analysis / T–S diagram; thermohaline intrusions; interleaving; thermohaline staircases; 
- double diffusion; submesoscale fronts and filaments; coherent vortices (meddies / SCVs); 
- ocean microstructure & mixing; Richardson number / Kelvin–Helmholtz.* 
- Names: Munk, Osborn, Gregg, Polzin (mixing); Thomas, Ferrari, McWilliams, Mahadevan (submesoscale).


## Asta MCP idea


- **Do a rigorous citation-graph literature review via the Asta/Semantic-Scholar MCP** (AI2's
Scientific Corpus Tool, endpoint `https://asta-tools.allen.ai/mcp/v1`. Start from the anchors 
above, traverse citations/references, and build a properly cited section. This note's references 
are web-search-grade only.
- Assess whether the SP-time-series angle is staked out or open
- Specifics: Can argosy's pp06 record demonstrate persistence/evolution of a specific intrusion/layer quantitatively.




---


# Turn AI loose: "where does this lead research-wise?" 


Responses not edited so pardon the annoying AI tone.


## Extensional Exploration: 10 Testable Hypotheses from WMT


Starting from Water-Mass Theory (WMT) and fanning outward into physical–biogeochemical coupling,
phytoplankton ecology, and climate-driven circulation change. Each item: **research problem** →
**possible observational test**. Not restricted to the shallow profiler — the full RCA sensor
suite plus gliders, Argo/BGC-Argo, DAS, satellites, and circulation models are in play. The
emphasis the user asked for (physical/chemical coupling to phytoplankton ecosystems; climate
implications for circulation and ecological health) is woven through.


Grounding note: current literature frames several live frontiers these hypotheses engage —
submesoscale fronts/eddies injecting nutrients on phytoplankton-growth timescales
(Mahadevan 2016, Ann. Rev. Mar. Sci.; mixed-layer-eddy bloom studies); a basin-scale FINDING that
physical and biological patchiness are *uncorrelated* (Nature Comms 2025), challenging "physics
structures biology"; declining net primary production in the stratified ocean driven by
strengthening nutrient limitation (Nature Comms 2025); and EBUS deoxygenation / OMZ vertical
expansion with Oregon-shelf near-bottom hypoxia (IUCN; Pierce et al. 2012; Ann. Rev. Mar. Sci.
2024). The RCA Oregon line sits squarely in an eastern-boundary upwelling system, so the
climate/ecology hooks are not generic — they are local.


A recurring methodological thread: the RCA fixed-point, multi-year, ~9-profile/day, full-sensor-
suite time series is unusually suited to separating PERSISTENCE from EVOLUTION and (with current
data) ADVECTION from in-place change — the exact ambiguity WMT must resolve to be testable.


## H1 — Water-mass layers as coherent, trackable objects


**Problem.** WMT posits that upper-ocean structure behaves as discrete, elastic, advected water
masses with "integrity." Is a given intrusion/layer a persistent object that can be tracked and
have a lifetime, or merely transient stratification? No consensus on object-lifetimes from a fixed
point.


**Test.** From the pp06 multi-year SP record, define a layer by its T–S signature (conservative
tracer) and track its depth/thickness/intensity profile-to-profile; measure persistence time and
deformation rate. Corroborate "object vs. passing feature" by pairing with the 200 m platform
ADCP/VELPT: a coherent advected object should show a consistent cross-site velocity during its
visit (S = V·T length scale). Cross-check against satellite SSH/geostrophic-velocity eddies and a
regional circulation model (ROMS) to classify object type (meddy/SCV vs. frontal intrusion).


## H2 — Advection vs. in-place evolution (the WMT identifiability problem)


**Problem.** A single-point time series cannot, alone, distinguish structure *advected past* the
sensor from structure *evolving in place* — yet WMT claims both occur. Which dominates, and when?
**Test.** Jointly invert SP profile change rates against the ADCP-derived current(depth) field: the
advective term (V·∇ of the measured horizontal gradient, where the gradient is inferred from the
along-track feature and model fields) vs. the local tendency. Decompose variance into
advective vs. evolutionary on event-by-event basis. Validate the partition on a circulation model
where both terms are known. This is the hypothesis that makes all the others interpretable.


## H3 — Submesoscale fronts inject nutrients on phytoplankton-growth timescales (local test)


**Problem.** Submesoscale frontal dynamics are theorized/modeled to drive episodic vertical nutrient
fluxes that fuel production (Mahadevan), but direct in-situ, time-resolved confirmation from a
fixed open-ocean point is rare. Does the RCA site see nutrient-injection events coincident with
frontal passages, and do they trigger a biological response?
**Test.** Detect frontal/intrusion passages in SP T–S (WMT layers) and in the ADCP shear field;
test for coincident NUTNR nitrate pulses at depth and a lagged chlorophyll (FLORT CHLAFLO)
increase in the euphotic zone over the following days. The ~9/day cadence resolves the growth-
timescale lag. Corroborate the surface expression with satellite ocean-color + SST fronts.


## H4 — Physical and biological patchiness are decoupled in the vertical/temporal domain


**Problem.** A basin-scale result (Nature Comms 2025) found horizontal physical and biological
patchiness are *uncorrelated* — overturning "physics structures biology." Does that decoupling also
hold in the VERTICAL and TEMPORAL structure a fixed profiler sees, or does physics organize biology
at the water-mass-layer scale?
**Test.** Quantify the scale-variance slope of physical tracers (T, S, σ₀) vs. bio-optical tracers
(chlorophyll, CDOM, backscatter) across depth and time in pp06. Test whether cline/layer boundaries
(WMT interfaces) coincide with bio-optical structure boundaries more than chance. A positive result
(coupling at the layer scale) would reconcile with the basin-scale decoupling by showing it is
scale-dependent.


## H5 — The subsurface chlorophyll maximum is pinned to a water-mass interface, not a fixed depth


**Problem.** The deep/subsurface chlorophyll maximum (SCM) is often modeled at a light/nutrient
compromise depth, but may instead track a density/water-mass interface that migrates. Which frame
predicts SCM depth better, and does the SCM move as WMT layers deform?
**Test.** Regress FLORT chlorophyll-max depth against (a) fixed depth, (b) isolume (PAR level),
(c) pycnocline/σ₀-surface depth, and (d) a specific T–S interface, across the multi-year SP record.
If the SCM tracks a σ₀ surface or T–S interface that itself migrates with WMT layers, that links
water-mass dynamics directly to primary-production structure.


## H6 — Intrusions ventilate (or de-ventilate) the water column, modulating oxygen


**Problem.** In an EBUS with an expanding OMZ, lateral intrusions of differently-oxygenated water
could be a first-order control on local O₂ at depth — distinct from vertical mixing or in-situ
respiration. How much of observed O₂ variability is advective water-mass exchange?
**Test.** Attribute CTD dissolved-oxygen variability in pp06 to WMT layer swaps: when a new T–S
layer arrives (H1 tracking), does O₂ change step-wise with it (advective) vs. drift (respiration/
mixing)? Separate using the O₂–T–S relationship (a conservative-tracer argument: advected water
carries its O₂ signature). Tie to the deep profiler for full-column context and to shelf hypoxia
records (Oregon near-bottom hypoxia) for ecological stakes.


## H7 — Marine heatwaves reorganize water-mass layering and its biological consequences


**Problem.** Marine heatwaves (e.g. the NE Pacific "Blob") are increasing with climate change.
Do they manifest as anomalous water-mass intrusions/stratification in the WMT sense, and do they
suppress the nutrient-injection pathway (H3), thereby reducing production?
**Test.** Identify heatwave periods in the multi-year SP + satellite SST record; characterize the
anomalous T–S layer structure (shallower, warmer, more stratified?), test for reduced frequency/
magnitude of nitrate-injection events and depressed chlorophyll during/after. The decadal SP record
spans multiple heatwave events — a natural experiment in circulation-change impact on ecology.


## H8 — Stratification trend is tightening nutrient limitation at the RCA line


**Problem.** Global NPP is declining in the stratified ocean via strengthening nutrient limitation
(Nature Comms 2025). Is a multi-year stratification-intensification trend detectable at the RCA
sites, and is it coupled to a trend in nutrient supply and production?
**Test.** Fit long-term trends in pycnocline strength/depth (σ₀ gradient, from the MLD/cline
metadata products) and in NUTNR nitrate inventory and FLORT chlorophyll over the decade-plus
record, per site (sb/oo/ab span a cross-margin gradient). Attribute: does increasing stratification
lead decreasing near-surface nitrate and production? Argo/BGC-Argo regional context extends the
spatial inference beyond the point.


## H9 — Internal waves / turbulence erode water-mass integrity and spike biogeochemical noise


**Problem.** WMT says layer "integrity can be disrupted by turbulence." Where and when does mixing
actually erode intrusions, and does that erosion have a measurable biogeochemical signature (e.g.
nutrient entrainment, or the sensor-noise artifact we already see at cline onset)?
**Test.** Use the VADCP (5-beam) shear + the ADCPT to estimate Richardson number / Kelvin–Helmholtz
susceptibility at WMT interfaces; test whether low-Ri intervals coincide with (a) observed layer-
merging/erosion in the SP T–S sequence and (b) elevated small-scale variance in salinity/DO (the
"scratchiness" the MLD annotator keys on). DAS on the RCA cable and the hydrophones offer
independent internal-wave / fine-structure detection to corroborate timing.


## H10 — A fixed-point "water-mass census" as a climate sentinel for circulation reorganization


**Problem.** Climate change is expected to shift the strength/position of eastern-boundary upwelling
and the source-water pathways feeding the margin. Can a multi-year census of water-mass
*types and frequencies* at a fixed RCA point serve as an early-warning sentinel for circulation
reorganization — a quantity simpler and more robust than any single variable?
**Test.** Cluster the pp06 T–S (and O₂) record into recurrent water-mass classes (unsupervised;
this is where the argosy ML/SGA machinery earns its keep); track the *frequency and seasonality of
each class* across the decade and across sb/oo/ab. A trend in class composition (e.g. more
low-O₂ / more subtropical source water) is a circulation-change fingerprint. Validate the source-
water attribution against a circulation-model particle-backtracking (ROMS) and Argo climatology.


## Cross-cutting notes


- **The three enabling capabilities** these hypotheses repeatedly need: (1) water-mass layer
  tracking from T–S (H1); (2) a current(depth) field to separate advection from evolution
  (H2, H3, H6, H9) — the ADCP/VELPT synthesis already flagged in BR.md; (3) recurrent-class
  clustering (H10) — the SGA/ML line. Building these three unlocks most of the list.
- **The climate/ecology payoff** concentrates in H6–H8, H10: deoxygenation, heatwaves, stratification-
  driven nutrient limitation, and circulation reorganization — all live EBUS questions with Oregon-
  margin stakes (fisheries, hypoxia) and all approachable from the multi-year RCA record.
- **Where the SP is genuinely ahead:** persistence/evolution of layered structure from a sustained
  fixed point (H1, H2, H5, H10). Most intrusion/submesoscale-productivity work is spatial surveys,
  short moorings, or models; the decade-plus, high-cadence, full-BGC-suite single point is the
  underexploited niche.
- **Honest caveat:** several hypotheses (H2, H3, H6, H9) are only decisively testable WITH the
  current/velocity data. Without it the SP can describe structure but struggles to attribute
  mechanism. This reinforces the ADCP-synthesis as the highest-leverage next data capability.
- **Rigor gate:** these are articulated from reasoning + a web-search-grade literature scan, not a
  citation-graph review. Before committing to any as a funded direction, run the Asta/Semantic-
  Scholar MCP review (per the WMT "Asta MCP idea" above) to confirm each is genuinely open and to
  find the groups already working it.

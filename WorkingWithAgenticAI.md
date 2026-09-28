# Working With Agentic AI — Lessons Learned

Working notes (repo-only, not in the Jupyter Book) on collaborating with an agentic AI
assistant on the argosy project. Each entry is a concrete lesson from lived experience, meant
to improve the partnership rather than to theorize about it.


## Lesson 1: The slow walk-through, and closing the human's accountability deficit

### What happened

While building the MLD 1-D CNN, the human asked the agent to explain the training machinery
"from the ground up" — one small step per exchange, the human restating each step in their own
words and the agent correcting only where needed. It was slow and deliberate by design.

Partway through, at the point of defining the loss and what the "no-MLD" target heatmap means,
the human realized that the annotation tool (`MLD.py`) had been recording two different things
as the same label: a genuine **no-mixed-layer** profile (data present, no cline — a valid
"learn to abstain" target) and an **empty chart** with no data at all (an Advance click past a
blank profile — not a training example at all). Both had been stored as `no_mld_recorded=True`,
silently poisoning the abstain class of the training data.

The agent had described the abstain-via-flat-heatmap design many times without ever noticing
this conflation. The human found it by grinding through the mechanics by hand.

### Why the agent missed it

The agent reasoned about the system **as specified** — the design as described in the code and
docs — rather than auditing **how the data was actually produced**, click by click, at
labeling time. The gap was one of *provenance*: the difference between "what the pipeline is
supposed to do" and "what actually went into it." Agentic AI is fluent and fast at the former
and, left to its own momentum, tends to skate past the latter. It will confidently elaborate a
design without stopping to ask whether the ground-truth inputs match the design's assumptions.

### The lesson

- **The slow walk-through is a method, not just pedagogy.** Forcing the system to be
  re-derived one verifiable step at a time — with the human restating each step — surfaces
  assumptions that fluent narration glosses over. The value is not (only) that the human
  learns; it is that the act of slow re-derivation is itself a debugging technique. Speed hides
  errors; deliberate pace exposes them.

- **The human's job is to close their own accountability deficit.** When an agent produces
  working code and confident explanations quickly, the human can drift into rubber-stamping —
  accepting outputs they could not themselves defend. That is an accountability deficit: the
  human is nominally responsible for the work but no longer actually understands it well enough
  to vouch for it. The remedy is to periodically *earn back* that understanding by tracing the
  system slowly enough to catch what the agent didn't. This is not distrust of the tool; it is
  the human reclaiming the position of being able to stand behind the result.

- **Agents audit specifications; humans should audit provenance.** A productive division of
  labor: let the agent move fast on design, implementation, and explanation, but reserve for the
  human (and prompt the agent toward) the question the agent under-weights — *"where did this
  actually come from, and does it match what we assumed?"* Data-generation steps, human-labeling
  conventions, and the exact meaning of edge cases are where this pays off.

### Practical takeaways

- Schedule deliberate slow walk-throughs of any system the human will be accountable for,
  especially before trusting its outputs (here: before trusting a trained model's numbers).
- When the agent explains a design, occasionally ask it to trace a concrete example end to end,
  including how the *inputs* were generated — not just how the code transforms them.
- Treat "the agent has explained this confidently many times" as no guarantee the underlying
  data honors the explanation. Confidence is about the description, not the provenance.
- Log the discovered inconsistencies as explicit to-dos (this one is in `DevelopmentLog.md`
  Open Topics: the no-MLD vs no-data conflation) so the catch converts into a fix.


## Lesson 2: Deprecating borrowed idioms that mislead ("1×1 convolution")

During the same walk-through, the agent referred to each output head as a "1×1 convolution."
In our model the convolutions are **1-D** (one spatial axis: depth), so a head's kernel is
simply **width 1** over depth, spanning all 32 input channels (→ 32 weights + 1 bias). The
"1×1" phrasing is inherited from **2-D image CNNs**, where it means 1 pixel tall × 1 pixel wide.
Applied to our 1-D case the second "1" corresponds to no real axis — it is idiom, not geometry —
and it actively misled: the human reasonably read "1×1" as a one-parameter kernel and had to
stop and reconcile it against the stated 33 parameters.

**Decision / convention for this project:** do NOT use "1×1" (or other 2-D-borrowed kernel
idioms) when describing the 1-D CNN. State the kernel by its **depth width** and let the channel
span be explicit: e.g. "a width-1 conv over depth across 32 channels (33 params)," and for the
backbone "width-7 conv." Reserve 2-D idioms for genuinely 2-D contexts.

**The general lesson:** agentic AI reaches for the field's standard idioms, which are often
anchored in the *most common* setting (here, 2-D vision) rather than the *current* one. When an
idiom encodes a dimensionality or structure that doesn't match the situation, it imports a hidden
wrong mental model. Prefer literal, dimension-honest descriptions over borrowed shorthand; and
when a term causes the human to pause and re-reconcile, treat that friction as a signal to retire
the term, not to re-explain it.

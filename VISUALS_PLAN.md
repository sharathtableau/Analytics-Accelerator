# Visuals plan: enterprise dashboards at Claude-level design quality

Agreed with Sharath on 16 Oct 2026. Status of each phase is in `ENTERPRISE_TRACKER.md`, section R (rows VX0–VX4).

## Goal

Dashboards built by the accelerator should look as good as, or better than, the dashboards Claude builds by hand, while keeping what makes the product trustworthy: every number comes from a semantic view and is validated against the base tables.

## What makes Claude-built dashboards look better (and what we copy)

1. **One clear story per page.** A hero number or chart first, supporting tiles smaller, context last.
2. **Grey for context, colour for the point.** Most marks are muted; only what matters gets the accent colour.
3. **Annotation on the chart.** End labels on lines, callouts on peaks and drops, plan and target lines, shaded events; legends only when unavoidable.
4. **Typography and space.** A clear type scale, large numbers, generous whitespace, aligned grids.
5. **A chart shape that fits the question.** Slope, dumbbell, bump, river or calendar heatmap instead of always bars.
6. **Iteration.** Render, look, fix clipping and crowding. This is the step the product does not do today.

## Decisions

- **Two layers.**
  - **Layer 1, governed design system:** no AI involved; it raises the floor for every dashboard.
  - **Layer 2, Cortex Design Studio:** Claude Opus through Cortex `AI_COMPLETE`, used at build time for bespoke design.
- **AI-written code is acceptable when it comes from Cortex** (a Snowflake service), as long as controls replace human review:
  - a locked sandbox with no network or app access;
  - a code check before it runs;
  - every number on screen validated against governed data;
  - a frozen, versioned design;
  - a fallback to Layer 1.
- **Generated code never calculates.** It receives display-ready, already-validated values and only draws them.
- **Generate once, freeze, reuse.**
  - A design is generated at build time and saved with the dashboard version.
  - Refreshes and filters reuse it.
  - Published versions pin it.
  - A new design is generated only on an explicit Redesign.
- **Cost control.**
  - Opus is used for the first design; a cheaper Claude model handles small edits.
  - Viewing costs nothing extra.
  - Runs count against the existing per-person AI limits.
- **Not doing:** generating whole dashboards as code on every request. It is slow, cannot be tested, and would lose "every number verified".

## Layer 1: governed design system (every dashboard)

- **Page compositions instead of one tile grid:**

  | Composition | Shape |
  |---|---|
  | Hero + supporting | One big chart or number, smaller tiles around it |
  | Story scroll | Sections, each with a headline |
  | Board pack | Dense, made for print |
  | Command grid | Live operations view |
  | Compare | Side by side |

  Each composition is reviewed and chosen per page.
- **Annotation layer:** automatic labels on peaks, drops and anomalies (from the anomaly results already computed), plan and target lines, value labels at line ends, period shading.
- **Emphasis rules:** the focus series gets the theme accent; everything else is muted.
- **More chart types:**
  - Drop B: cash-flow river, daily pulse with annotations, cohort heatmap, new vs returning.
  - Later: slope, dumbbell, bump, bullet, calendar heatmap.
- **Motion and interaction:** a light reveal on load, a hover readout strip, click-to-filter.
- **Enterprise basics:**
  - Colour-blind-safe palettes.
  - A "show as table" alternative on every chart (screen readers).
  - Laptop, projector and phone layouts.
  - Print-quality PDF and PowerPoint board-pack export.

## Layer 2: Cortex Design Studio (build time)

1. **Art director.** Opus returns a JSON design spec, never code:
   - composition and hero tile;
   - tile sizes and emphasis;
   - which points to annotate and with what label;
   - section breaks and short section narrative.

   The validator checks it like layouts today. Every number in an annotation or narrative must be a computed fact (like QA-08).
2. **Design QA.** Automated checks after each render:
   - clipped or overlapping labels;
   - too many colours;
   - wasted space;
   - weak contrast;
   - an unclear hero.

   Together they give a design score.
3. **Self-critique loop.** The Design QA findings, plus a picture of the page when Cortex image input is available, go back to Opus, which revises the spec. At most 2 rounds.
4. **Generated components.** When a question needs a chart we do not have, Opus writes it once.
   - **Runs** in a sealed sandbox frame and receives only governed, display-ready data.
   - **Code check** rejects network access, parent-page access, cookies, storage, `eval`, and oversized code.
   - **On-screen numbers:** after rendering, the frame reports every visible number, which the validator checks against the governed data (new check **QA-09: rendered numbers**).
   - **Approval:** a person approves the component.
   - **Storage:** approved components are saved, versioned and fingerprinted, in a component library (AA_DESIGNS) and reused.
5. **Freeze and fallback.**
   - The design is stored with the dashboard version and pinned when published.
   - If any step fails, Layer 1 renders the page, so it is never worse than today.
   - Each dashboard can switch between Standard and Designed by Cortex.

Prompt injection (for example a column value containing instructions) is contained by the sandbox, and injected content is caught by the rendered-number check.

## Phases

| Phase | Scope | Exit criteria |
|---|---|---|
| **VX0 Probe** | Which Claude models `AI_COMPLETE` reaches on the account and its output-token limit · time and credits for one page design · sealed sandbox frame inside the Snowsight component · Cortex image input in the region | A one-page probe report; go / change / stop for VX2 and VX3 |
| **VX1 Design system v3** | Compositions · annotation layer · emphasis rules · chart Drop B · hover readout, reveal motion, click-to-filter | Mockup of 2–3 compositions on Harborline data shown side by side with today **before building**; then tests + screenshots |
| **VX2 Art director + Design QA** | Opus design spec (JSON) · validator for the spec · Design QA checks and score · critique loop (≤ 2 rounds) | Design score improves on the reference set; every annotation number validated |
| **VX3 Generated components** | Sandbox frame · code checks · QA-09 rendered numbers · approval · AA_DESIGNS library · Standard / Designed by Cortex switch | A new chart type generated, validated, approved and reused on a second dashboard |
| **VX4 Export + accessibility** | PDF and PowerPoint board pack · table alternative per chart · colour-blind palettes · laptop / projector / phone layouts | Board pack matches the screen; WCAG 2.1 AA review passes |

## How we judge "equivalent or better"

- Take 5 reference dashboards Claude built by hand and rebuild them with the accelerator on the same data.
- Run a blind side-by-side review with the team or Snowflake reviewers.
- Target: ours preferred or tied at least 70% of the time.
- Ours also carries "every number verified", which the hand-built ones do not.

## Already done (15–16 Oct)

- **Insight headlines:** a rule-written headline on each tile.
- **Themes:** Classic is the default, plus Company themes uploaded as brand colours, a token file or a logo, with WCAG checks.
- **Chart drop A:** bars + line, treemap, progress gauge, P&L table.
- **Settings group** in the left menu.

-----

## name: semantic-triple-transformation
description: Transforms deep research outputs from Gemini Deep Research, Grok DeepSearch, or ChatGPT Deep Research (containing STT-ANCHOR blocks) into four simultaneous deliverables: longform Substack journalism, four optimized infographic JSON flavors, X/LinkedIn social copy, and a Claude Code interactive HTML artifact prompt. Use when user says “Run the STT”, “Triple transformation”, “Four deliverables”, “Generate the JSON”, “Transform the research”, “Make the dispatch”, or asks to turn research into longform + JSONs + social + artifact.
license: Apache-2.0
metadata:
author: ACRA Insight LLC
version: 2.0.0
pipeline-stage: 2
repository: contextjamming.com

# Semantic Triple Transformation

**Stage 2 of the ACRA MoEA (Mixture of Expert Agents) production loop.**

You are a world-class tech journalist, information designer, social media strategist, and interactive experience architect operating as a unified production pipeline. Your job is to transform a single deep research output into simultaneous, distinct deliverables — each targeting a different medium, format, and cognitive register.

This skill accepts output from Gemini Deep Research, Grok DeepSearch, or ChatGPT Deep Research that contains **STT-ANCHOR** blocks. Those anchors are your structural map. Parse them before writing anything.

## What This Skill Does NOT Do

- Does not run the research (that requires Stage 1 + the target research model)
- Does not render the infographic (the JSON is the payload for a designer or pipeline)
- Does not post to X or Substack — produces publication-ready copy only
- Does not deploy the artifact — produces the Claude Code artifact prompt only

## Pre-flight: Input Normalization + STT-ANCHOR Parse

Before producing any deliverable, complete these steps in order.

### Step 0 — Detect input source and normalize

- **Gemini Deep Research**: Structured sections with inline citations and STT-ANCHOR blocks. No normalization needed.
- **Grok DeepSearch**: Denser tone, often sardonic. Citations appear as footnotes. Extract thesis claims from body before parsing anchors. If no STT-ANCHOR blocks exist, auto-generate from H2/H3 structure: `STRUCTURAL-THESIS` → first H2, `MARKET-INFLECTION` → largest data claim per section.
- **ChatGPT Deep Research**: More structured, frequently bullet-heavy. Auto-detect bullet-dominated sections → rewrite as prose seeds before populating `longform-seed` fields. Citations appear as numbered references at end.
- **Raw JSON input**: If only a JSON payload arrives (no research body), skip directly to Deliverable 4.

### Step 1 — Extract and route anchors

1. Extract all STT-ANCHOR blocks from the research input.
1. Identify each anchor’s label (`STRUCTURAL-THESIS`, `MARKET-INFLECTION`, `POWER-MAP`, `OPERATIONAL-INSIGHT`, `MARKET-GAP`, `VERTICAL-THESIS`, `COMPETITIVE-MOAT`).
1. Read the transformation map if present — it specifies which anchors feed which deliverable.
1. If no transformation map exists, apply the default routing table below.
1. Confirm anchor coverage for all deliverables before proceeding.
1. Note sections where anchors are absent — fill from body research, **not** inference.

**Coverage check**: If fewer than 3 STT-ANCHOR blocks are present, flag before proceeding: “I found [N] STT-ANCHOR blocks. The STT pipeline needs at least 5 for full coverage. Proceed with what’s available, or enrich the research first?”

### Default Anchor Routing Table

|ANCHOR LABEL         |D1 LONGFORM        |D2 JSON (4 Flavors)|D3 SOCIAL      |D4 ARTIFACT          |
|---------------------|-------------------|-------------------|---------------|---------------------|
|`STRUCTURAL-THESIS`  |Opening thesis     |Hero               |Primary hook   |Hero section         |
|`MARKET-INFLECTION`  |Section break      |Headline stat      |—              |Animated stat card   |
|`POWER-MAP`          |Structural reveal  |—                  |Subtweet       |Coalition diagram    |
|`OPERATIONAL-INSIGHT`|—                  |Callout box        |Standalone post|Sticky sidebar       |
|`MARKET-GAP`         |Closing argument   |White space viz    |—              |CTA card             |
|`VERTICAL-THESIS`    |Penultimate section|—                  |LinkedIn hook  |Scroll reveal section|
|`COMPETITIVE-MOAT`   |—                  |Strategy map       |Reply bait     |Final reveal         |

## Deliverable 1: Longform Journalism (Substack Dispatch)

**Persona**: World-class tech journalist with Michael Lewis narrative precision. Non-obvious lede. Scene-setting before thesis. Characters who carry arguments. The seam where conventional wisdom breaks.

### Format Requirements

- 1,200–2,500 words
- Opens with a scene or specific moment — **not** a summary of what you’re about to argue
- `STRUCTURAL-THESIS` anchor becomes the opening thesis paragraph (after the lede scene)
- Each major section corresponds to a research thread
- Section transitions use structural reveals, not topic sentences
- Closes with the `MARKET-GAP` or white space anchor
- **No bullet points in the body.** Prose throughout.
- Subheadings permitted between major sections — make them editorial, not descriptive

### Voice Calibration

- Write for a reader who is technically fluent but wants to be surprised
- Counterintuitive framing over confirmatory framing
- Specific named entities — companies, people, products, dollar figures — over generics
- Active voice. Short sentences when stakes are high. Long sentences when building complexity.
- The last sentence of every section should make the reader want to keep reading

### STT-ANCHOR Integration

- `longform-seed` from each anchor = the opening phrase or sentence of that section
- Do not reproduce the anchor verbatim — use it as the seed for your own prose
- The anchor’s `json-cluster` data should appear as specific facts embedded in the narrative

**Output label**:

```
--- DELIVERABLE 1: LONGFORM JOURNALISM ---
[Full piece here]
--- END DELIVERABLE 1 ---
```

## Deliverable 2: Four Flavors of Infographic JSON

**Purpose**: Provide four distinct JSON payloads optimized for different AI rendering engines or downstream systems. Deliverable 4 will automatically ingest Flavor 4.

### Design Parameters (embed as metadata in all flavors)

- `visual_logic`: Richard Scarry Busy Town — layered, dense, every element doing work
- `typography`: Paula Scher — oversized display type as structural element, bold hierarchies
- `sidebar_elements`: 90s SPY Magazine — sidebars with attitude, editorial stat clusters
- `color_palette`: Domain-derived (cybersecurity = black/red/amber; AI = electric blue/white/yellow)

### Flavor 1: Optimized for Gemini nano banana 2

- **Engine parameters**: `{"target_engine": "gemini-nano-banana-2", "schema_strictness": "high", "footprint": "ultra-lightweight"}`
- **Population Rules**: Flattened object hierarchy to support edge-compute constraints. Extract key variables (`headline`, `stat`) directly at the top level without deep nesting.

### Flavor 2: Optimized for Grok Imagine

- **Engine parameters**: `{"target_engine": "grok-imagine", "prompt_density": "high", "visual_style": "sardonic-editorial"}`
- **Population Rules**: Convert structural elements into deeply descriptive string arrays. Values should read like direct image generation prompts, embedding explicit lighting, composition, and sardonic aesthetic cues.

### Flavor 3: Optimized for GPT

- **Engine parameters**: `{"target_engine": "gpt-4", "context_window": "expanded", "format": "standard-dom"}`
- **Population Rules**: Standard document object model. Must include a clear `reasoning_trace` block explaining the logic behind the data layout, alongside explicit relationship mapping between stat nodes.

### Flavor 4: Optimized for Claude Code Interactive (Baseline Schema)

- **Engine parameters**: `{"target_engine": "claude-code", "target_output": "interactive-html", "aspect_ratio": "9x16"}`
- **Population Rules**:
  - `hero.headline`: compress `STRUCTURAL-THESIS` anchor’s `social-fragment` → 4–8 words, Paula Scher scale
  - `hero.deck`: expand `longform-seed` from `STRUCTURAL-THESIS` anchor → 1–2 sentences
  - Each section maps to one STT-ANCHOR
  - `stat_cluster` pulls directly from the anchor’s `json-cluster`
  - `sidebar.spy_label`: SPY Magazine-style kicker — editorial, slightly sharp, under 6 words
  - `visual_note`: plain-English description of what renders at that section (Scarry style)

**Baseline Schema (Flavor 4)**:

```json
{
  "meta": {
    "title": "",
    "subtitle": "",
    "byline": "",
    "date": "",
    "engine_parameters": {
      "target_engine": "claude-code",
      "target_output": "interactive-html",
      "aspect_ratio": "9x16"
    },
    "design_params": {
      "visual_logic": "richard-scarry-busy-town",
      "typography": "paula-scher",
      "sidebar_style": "spy-magazine-90s",
      "color_palette": []
    }
  },
  "hero": {
    "headline": "",
    "deck": "",
    "anchor_label": "STRUCTURAL-THESIS",
    "visual_note": ""
  },
  "sections": [
    {
      "id": "",
      "anchor_label": "",
      "heading": "",
      "body": "",
      "stat_cluster": {
        "headline_stat": "",
        "supporting": ["", "", ""]
      },
      "sidebar": {
        "type": "callout | stat | quote | definition",
        "content": "",
        "spy_label": ""
      },
      "visual_note": ""
    }
  ],
  "bottom_matter": {
    "white_space_gap": "",
    "call_to_action": "",
    "anchor_label": "MARKET-GAP"
  },
  "citations": []
}
```

**Output label**:

```
--- DELIVERABLE 2: FOUR JSON FLAVORS ---
[Flavor 1 JSON Here]

[Flavor 2 JSON Here]

[Flavor 3 JSON Here]

[Flavor 4 JSON Here]
--- END DELIVERABLE 2 ---
```

## Deliverable 3: X Platform Social Copy

**Audience**: SOTA AI research community, adjacent VC/PE, Lex Fridman fans, technically fluent generalists who follow AI discourse. Fast, skeptical, reward precision over enthusiasm.

### Format

- One **primary thread** (5–8 posts, numbered)
- One **standalone post** (OPERATIONAL-INSIGHT or POWER-MAP anchor compressed)
- One **reply-bait post** (POWER-MAP or COMPETITIVE-MOAT — designed to generate disagreement or engagement)
- Optional: one **LinkedIn variant** of the primary hook (under 150 words, slightly more formal, CISO/GTM audience)

### Voice Rules

- No em-dashes used as decoration
- No “game-changer”, “revolutionary”, “unprecedented”
- Specific over generic: name the company, name the number, name the person
- Hook post must work as a standalone claim
- Compression is the skill: if it can be shorter, it must be shorter
- Final post: leave the reader with an unanswered question or a direct call to read the full piece

### Thread Structure

|POST      |ANCHOR SOURCE                                                                               |
|----------|--------------------------------------------------------------------------------------------|
|Post 1    |`STRUCTURAL-THESIS` → compressed to the bifurcation thesis                                  |
|Posts 2–4 |`MARKET-INFLECTION`, `OPERATIONAL-INSIGHT`, `POWER-MAP` → one claim per post, backed by stat|
|Posts 5–6 |`VERTICAL-THESIS` or `MARKET-GAP` → sector-specific application or white space              |
|Final post|Link to full Substack piece + 1-sentence hook                                               |

**Output label**:

```
--- DELIVERABLE 3: X PLATFORM SOCIAL COPY ---

[PRIMARY THREAD]
1/N [post]
2/N [post]
...

[STANDALONE POST]
[post]

[REPLY-BAIT POST]
[post]

[LINKEDIN VARIANT — optional]
[post]

--- END DELIVERABLE 3 ---
```

## Deliverable 4: Claude Code Interactive Artifact

**Purpose**: A scrollytelling HTML artifact that renders the Deliverable 2 (Flavor 4) JSON as a mobile-first interactive experience. Produced by Claude Code from the D2-F4 JSON payload.

### Artifact Spec

- **Input**: JSON from Deliverable 2, Flavor 4
- **Output**: Single-file HTML (responsive-html production standard applies)
- **Scroll behavior**: Each `sections[].id` reveals on IntersectionObserver scroll trigger (threshold: 0.25)
- **Stat animation**: `stat_cluster.headline_stat` animates count-up on reveal (requestAnimationFrame, ~800ms duration)
- **Sidebar**: `spy_label` renders as rotated amber kicker in DM Mono; content below
- `visual_note`: Styled placeholder div with Scarry-style border, note text as caption
- **Bottom matter**: `white_space_gap` renders as an opportunity card; `call_to_action` renders as an amber CTA button
- **Copy button**: On each `stat_cluster.headline_stat` — uses legacyCopy clipboard fallback (iOS safe)
- **Reduced motion**: Skip count-up animations, instant reveal

### Design Tokens

```css
--color-bg: #0a0a0a;
--color-accent: #f5a524;
--color-cream: #f1ead8;
--font-display: 'Playfair Display';
--font-mono: 'DM Mono';
--font-body: 'Inter';
```

### Responsive Behavior

- Single-column on mobile, max-width 680px centered on desktop
- `viewport-fit=cover` required (iOS notch safe)
- Safe-area insets on all four body sides
- All touch targets min 44×44px
- Fonts: all via `clamp()` fluid type scale

**Output**: Deliverable 4 is a **Claude Code prompt** pre-loaded with the D2-F4 JSON payload, ready to copy-paste into Claude Code to generate the artifact file.

**Output label**:

```
--- DELIVERABLE 4: CLAUDE CODE ARTIFACT PROMPT ---
[Claude Code prompt with D2-F4 JSON embedded]
--- END DELIVERABLE 4 ---
```

## Production Sequence

Always produce deliverables in this exact order:

1. **Detect input source** → normalize → parse anchors → confirm coverage → note gaps
1. **Deliverable 1 (longform)** — this is the master document; the other three derive from it
1. **Deliverable 2 (JSONs)** — pull stats and seeds from the now-written longform for consistency. Output all four target flavors simultaneously.
1. **Deliverable 3 (social)** — compress from the longform, not from raw research
1. **Deliverable 4 (artifact prompt)** — Claude Code prompt pre-loaded with D2 Flavor 4 JSON + design tokens

This sequence ensures all deliverables are semantically consistent — they tell the same story at different compression ratios and interaction registers.

## Troubleshooting

**Anchors missing from input**

- If fewer than 3 STT-ANCHOR blocks: flag before proceeding.
- Do not fabricate anchor content — pull from research body with a note.

**Grok input: tone too contrarian in longform**

- Reframe sardonic conclusions as structural observations.
- Replace first-person provocation with third-person data claims.
- Anchor every editorial claim to a named json-cluster stat.

**ChatGPT input: deliverables feel like a report**

- Rewrite bullet-heavy sections as prose before populating longform-seed.
- Add scene-setting lede manually if absent from research.
- Compress the social hook from the rewritten prose, not the ChatGPT abstract.

**Deliverables feel disconnected**

- Confirm Deliverable 1 was written first and 2–4 derived from it.
- Headline stat in JSON and stat cited in longform must match exactly.
- Social hook must compress the longform lede, not the research abstract.

**JSON schema validation errors**

- Every section must have a valid `anchor_label`.
- `stat_cluster.supporting` must have exactly 3 items (use “[NEEDS DATA]” as placeholder).
- `visual_note` is required — do not leave blank.

**Social copy too long**

- Each X post: 280-character hard limit.
- If a claim requires more than 280 characters, split into two posts and renumber.
- LinkedIn variant: 150-word soft limit — trim ruthlessly.

**Artifact count-up not working on iOS**

- Confirm `requestAnimationFrame` fallback is present.
- Confirm `prefers-reduced-motion` media query skips animation.
- Use `legacyCopy` pattern for all clipboard operations.

## Examples

**Example 1: Holographic models & agentic intelligence research**

- User: “Run the STT on this Gemini deep research output about Maldacena, AdS/CFT, and architectural determinism in frontier AI.”
- Actions: Parse STT-ANCHOR blocks → write Michael Lewis-style longform opening with Franklin night-walk scene → generate 4 JSON flavors with Paula Scher typography and Scarry visual logic → craft 6-post X thread + standalone + reply-bait → produce Claude Code prompt for 9:16 scrollytelling artifact.
- Result: Full production package ready for Substack dispatch, X thread, investor deck JSON payload, and interactive demo artifact.

**Example 2: Market inflection in AI infrastructure**

- User: “Triple transformation on this Grok DeepSearch about NVIDIA SANA-WM shifts and capex wars.”
- Actions: Normalize sardonic tone → extract `MARKET-INFLECTION` and `POWER-MAP` anchors → produce longform with structural reveals → output four JSON flavors + X thread designed for VC/PE engagement.
- Result: Consistent narrative across longform authority piece, social leverage, and interactive artifact for Series A narrative support.

## Success Criteria

This skill is working when:

- All four deliverables are produced in a single pass with semantic consistency.
- Stats and claims match exactly between longform, JSON, and social copy.
- The interactive artifact prompt generates a production-ready 9:16 HTML scroller on first try in Claude Code.
- Output requires zero manual reformatting before it can be used in investor materials, Substack, or X.

*Skill authored by ACRA Insight LLC · contextjamming.com · @BretKerr*
*Semantic Triple Transformation v2.0.0 · May 2026*
*Apache 2.0 — open source*
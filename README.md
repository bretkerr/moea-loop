# MoEA Loop — Recursive Research Orchestrator (v0.2)

Drives your two ACRA skills (`gemini-deep-research-xml` → `semantic-triple-transformation`)
as a self-extending research tree. One brief in; an auditable derivation of longform +
JSON + X copy + artifact prompts out, branching in complementary directions until the
frontier saturates or the token budget runs out.

It does **not** reimplement your skills. It *invokes* them — your real `SKILL.md` files in
`skills/` are the single source of truth for every prompt.

-----

## The actual problem this solves

Your stated hard part: *“How to make the two follow-ups repeatable across subjects.”*

Grok’s answer was a fixed pair (Holographic + Antithesis) applied to everything. That’s
brittle — apply a boundary/bulk reframe to a GTM brief and you get nonsense — and it has
no stopping condition, so loop N drifts into restating loop 1 (the “disconnected sections”
failure your own STT troubleshooting already names).

The fix is to make forking a **typed function of the anchor set**, not a menu pick:

1. **Forking is a typed rewrite.** Each fork primitive declares which STT-ANCHOR labels
   make it *fire* and whether it **deepens** (convergent — press the load-bearing claim)
   or **diverges** (lateral — reframe, transplant, map the field). Your anchor taxonomy
   already classifies the research’s structure; we reuse it as the type system.
1. **Selection returns one best DEEPEN + one best DIVERGE.** The two children are
   complementary *by construction* — “different directions” guaranteed — while the
   selection function is identical for every subject. That is the repeatability you wanted:
   the *function* is fixed; the *forks* adapt to content. On your neural-symbolic artifact
   it derives `ANTITHESIS + HOLOGRAPHIC` on its own; on a cyber-GTM brief it derives
   `DEPTH + VERTICAL`. Same code.
1. **A novelty ledger gates recursion.** Before spawning a fork, its projected brief is
   scored against every thesis already in the tree. Below the floor → that primitive is
   dropped. Both pools empty → the branch is `SATURATED` and terminates. This is the
   difference between a self-improving loop and an expensive echo chamber — and it’s the
   piece that makes “scale to as many loops as you have tokens” actually safe to run.

The clean way to think about the whole thing: **briefs are terms, fork primitives are
typed rewrite rules, STT is the normalization step, the tree is the derivation.** That’s
the “agentic programming language” you were reaching for — the primitives below *are* the
language. Python over Unix because you need persistent tree state, resumability, and
parallel forks; pipes can’t hold that cleanly.

## Fork primitive library

|primitive    |role   |lens                                          |fires on                                                |
|-------------|-------|----------------------------------------------|--------------------------------------------------------|
|`ANTITHESIS` |deepen |Feynman steelman-the-objection                |OPERATIONAL-INSIGHT, COMPETITIVE-MOAT, STRUCTURAL-THESIS|
|`DEBATE`     |deepen |AI-safety-via-debate / Oxford two-sided       |POWER-MAP, MARKET-INFLECTION, STRUCTURAL-THESIS         |
|`DEPTH`      |deepen |drill one named open question to the studs    |OPERATIONAL-INSIGHT, MARKET-GAP                         |
|`HOLOGRAPHIC`|diverge|Maldacena boundary/bulk reframe               |STRUCTURAL-THESIS, OPERATIONAL-INSIGHT                  |
|`ANALOGICAL` |diverge|cross-domain isomorphism transplant           |STRUCTURAL-THESIS, VERTICAL-THESIS                      |
|`VERTICAL`   |diverge|applied instantiation (sector / GTM / product)|VERTICAL-THESIS, MARKET-GAP, COMPETITIVE-MOAT           |
|`POWER`      |diverge|coalition / incentive map                     |POWER-MAP, MARKET-INFLECTION                            |

Add your own by appending to `PRIMITIVES` — that’s the extension point. `DEBATE` maps
directly onto your GemClaw debate-society implementation if you want to route those forks there.

## Role → model mapping (your MoEA methodology, in config)

|role                                  |default model      |why                                                                          |
|--------------------------------------|-------------------|-----------------------------------------------------------------------------|
|`architect` — Stage 1 + fork synthesis|`claude-opus-4-7`  |the auditor/architect seat                                                   |
|`research` — Claude-native backend    |`claude-sonnet-4-6`|long synthesis (swap for a Gemini adapter to keep the adversarial-model role)|
|`transform` — Stage 2 STT             |`claude-sonnet-4-6`|the production membrane                                                      |
|`scorer` — novelty judge              |`claude-haiku-4-5` |cheap                                                                        |

Override any of them with `MOEA_MODEL_ARCHITECT`, `MOEA_MODEL_RESEARCH`, etc.

-----

## Quickstart — manual mode (works today, zero dependencies)

Matches your Gemini-by-hand habit. The orchestrator prints paste-ready blocks and ingests
what you paste back; it holds the tree, the ledger, and the fork logic.

```bash
python3 moea_loop.py init --brief "Your topic + the seam/tension" --domain neuro

python3 moea_loop.py prompt 0          # prints skill+brief -> paste into Claude, get XML
# run that XML in Gemini Deep Research, save the output as out.md
python3 moea_loop.py ingest 0 --file out.md     # parses anchors
python3 moea_loop.py stt 0             # prints skill+research -> paste into Claude
python3 moea_loop.py set-deliverables 0 --file deliverables.md

python3 moea_loop.py fork 0            # selects 2 typed forks -> nodes 0.1, 0.2
python3 moea_loop.py tree              # see the derivation
# repeat prompt/ingest/stt/fork on 0.1 and 0.2 ...
```

## Quickstart — auto mode (bounded autonomy)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...

# Claude-native research (no copy-paste); recurse 2 levels, stop at 400k tokens
python3 moea_loop.py run 0 --backend claude --native-research --depth 2 --budget 400000
```

Without `--native-research`, auto mode runs Stage 1 + STT via API but **pauses** at each
external-research step so you can run the prompt in Gemini and `ingest`, then `run` again
to resume. State is checkpointed after every node — kill it and resume anytime.

Bounds: `--depth`, `--budget` (cumulative tokens), `--novelty-floor` (0–1; higher = prunes
sooner). `status` and `tree` show where any campaign stands.

-----

## What’s real vs. stubbed

- **Real:** the tree + persistence + resume, the anchor parser (tested on your actual
  `deep-research-report_3.md`), the typed fork selector, the novelty/saturation gate, both
  backends, the full CLI. It runs.
- **Stubbed by design:** the *external* Gemini/Grok call. In manual mode that’s you. In
  auto mode `--native-research` uses Claude; to keep Gemini as the adversarial agent in
  your MoEA loop, replace `ClaudeBackend.research()` with a Gemini API call that returns
  anchored markdown — the rest of the pipeline doesn’t change.

## Files

```
moea_loop.py        the engine + CLI
skills/
  gemini-deep-research-xml.md          Stage 1 (replace with your canonical copy)
  semantic-triple-transformation.md    Stage 2 (your copy)
campaign/state.json  created on init — the full auditable derivation tree
```

*ACRA Insight LLC · contextjamming.com · @BretKerr · Apache 2.0*
#!/usr/bin/env python3
"""
moea_loop.py  --  ACRA MoEA Recursive Research Orchestrator (v0.2)

A typed rewrite system over deep-research artifacts.

    briefs            are terms
    fork primitives   are typed rewrite rules
    STT (Stage 2)     is the normalization / evaluation step
    the research tree is the derivation

It drives the two existing ACRA skills in a loop:

    brief --[Stage 1: gemini-deep-research-xml]--> XML prompt
          --[external/native deep research]------> artifact (STT-ANCHOR blocks)
          --[Stage 2: semantic-triple-transformation]--> 4 deliverables
          --[FORK: select 2 typed primitives from the anchor set + novelty ledger]-->
              two new briefs --> recurse

Two execution modes:
  * manual  (default, zero dependencies) -- prints ready-to-paste skill+input blocks,
            ingests pasted research files. Matches the Gemini-by-hand workflow.
  * auto    (--backend claude) -- calls the Anthropic API for Stage 1, optional
            Claude-native research, Stage 2, and novelty scoring. Requires `anthropic`
            and ANTHROPIC_API_KEY. Bounded by --depth / --budget / --novelty-floor.

Author: ACRA Insight LLC  -  contextjamming.com  -  @BretKerr  -  Apache 2.0
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import textwrap
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

# MoEA role -> model mapping. Honors the named methodology (Opus as auditor/architect,
# Sonnet as the production membrane, Haiku as the cheap scorer). Override via env.
MODELS = {
    "architect": os.environ.get("MOEA_MODEL_ARCHITECT", "claude-opus-4-7"),   # Stage 1 + fork synthesis
    "research":  os.environ.get("MOEA_MODEL_RESEARCH",  "claude-sonnet-4-6"), # Claude-native research backend
    "transform": os.environ.get("MOEA_MODEL_TRANSFORM", "claude-sonnet-4-6"), # Stage 2 STT
    "scorer":    os.environ.get("MOEA_MODEL_SCORER",    "claude-haiku-4-5-20251001"),  # novelty judge
}

SKILLS_DIR_DEFAULT = Path(__file__).parent / "skills"
STAGE1_SKILL = "gemini-deep-research-xml.md"
STAGE2_SKILL = "semantic-triple-transformation.md"

ANCHOR_LABELS = {
    "STRUCTURAL-THESIS", "MARKET-INFLECTION", "POWER-MAP", "OPERATIONAL-INSIGHT",
    "MARKET-GAP", "VERTICAL-THESIS", "COMPETITIVE-MOAT",
}

# --------------------------------------------------------------------------- #
# Fork primitive library  --  the answer to "repeatable forking across subjects"
# --------------------------------------------------------------------------- #
#
# The fork operator is NOT a fixed pair. It is a typed function of the anchor set.
# Each primitive declares which anchor labels make it FIRE and whether it DEEPENS
# (convergent: drill the load-bearing claim) or DIVERGES (lateral: reframe / transplant).
# Selection always returns exactly one best DEEPEN and one best DIVERGE primitive, so the
# two children are complementary by construction -- "different directions" guaranteed,
# while the selection function itself stays identical across every subject (repeatable).
#
# `rewrite` turns the parent thesis into a child brief. Keep these terse: a brief, per the
# Stage-1 skill, is a topic + a tension, not an essay.

@dataclass
class ForkPrimitive:
    id: str
    lens: str
    role: str  # "deepen" | "diverge"
    triggers: set            # anchor labels that make this primitive fire
    domains: set             # domain tags that boost affinity ("*" = any)
    rewrite_tmpl: str        # {thesis} {domain} substituted

    def fires_on(self, anchor_labels: set, domain: str) -> int:
        """Affinity score: trigger overlap (weighted x2) + domain match."""
        trig = len(self.triggers & anchor_labels) * 2
        dom = 1 if ("*" in self.domains or domain in self.domains) else 0
        # a primitive that triggers on nothing can still be a fallback (score 0/1 via domain)
        return trig + dom

    def rewrite(self, thesis: str, domain: str) -> str:
        return self.rewrite_tmpl.format(thesis=thesis.strip(), domain=domain or "the originating domain")


PRIMITIVES: list[ForkPrimitive] = [
    # ---- DEEPEN pool (convergent: press the seam until it breaks or holds) -------------
    ForkPrimitive(
        id="ANTITHESIS", lens="Feynman steelman ('the first principle is you must not fool yourself')",
        role="deepen", triggers={"OPERATIONAL-INSIGHT", "COMPETITIVE-MOAT", "STRUCTURAL-THESIS"},
        domains={"*"},
        rewrite_tmpl=(
            "Steelman the strongest case that the central claim is WRONG. Claim under attack: "
            "\"{thesis}\". Build the most rigorous, sympathetic, well-evidenced objection a domain "
            "expert would raise, then locate the precise condition under which the original claim "
            "survives or fails. Do not strawman. The deliverable is the failure boundary."
        ),
    ),
    ForkPrimitive(
        id="DEBATE", lens="AI-safety-via-debate / Oxford two-sided adversarial resolution",
        role="deepen", triggers={"POWER-MAP", "MARKET-INFLECTION", "STRUCTURAL-THESIS"},
        domains={"*"},
        rewrite_tmpl=(
            "Stage a structured debate over the unresolved tension inside: \"{thesis}\". Two adversarial "
            "research positions, each marshalling its strongest evidence, judged on which survives "
            "cross-examination. Output the adjudicated synthesis, not a both-sides summary."
        ),
    ),
    ForkPrimitive(
        id="DEPTH", lens="drill a single named open question to the studs",
        role="deepen", triggers={"OPERATIONAL-INSIGHT", "MARKET-GAP"},
        domains={"*"},
        rewrite_tmpl=(
            "Take the single most load-bearing OPEN QUESTION left unresolved by: \"{thesis}\". Ignore "
            "everything else. Go one level deeper than the parent research did -- mechanism, not "
            "description. What would it take to actually answer it, and what is the current best answer?"
        ),
    ),
    # ---- DIVERGE pool (lateral: reframe, transplant, map the field) --------------------
    ForkPrimitive(
        id="HOLOGRAPHIC", lens="Maldacena boundary/bulk reframe (AdS/CFT lens)",
        role="diverge", triggers={"STRUCTURAL-THESIS", "OPERATIONAL-INSIGHT"},
        domains={"physics", "ai", "neuro", "geometry", "ml", "*"},
        rewrite_tmpl=(
            "Reframe \"{thesis}\" entirely as a boundary/bulk duality. What is the low-dimensional "
            "boundary, what is the reconstructed bulk, and what plays the role of the holographic map? "
            "Press whether the duality is literal, analogical, or breaks -- and what that reveals."
        ),
    ),
    ForkPrimitive(
        id="ANALOGICAL", lens="cross-domain isomorphism transplant",
        role="diverge", triggers={"STRUCTURAL-THESIS", "VERTICAL-THESIS"},
        domains={"*"},
        rewrite_tmpl=(
            "Find a structurally isomorphic phenomenon in a DISTANT, unrelated field and transplant it "
            "onto \"{thesis}\". Map the correspondence precisely (what maps to what), then mine the "
            "analogy for a prediction the original framing could not have produced. Flag where it fails."
        ),
    ),
    ForkPrimitive(
        id="VERTICAL", lens="applied instantiation (concrete sector / GTM / product)",
        role="diverge", triggers={"VERTICAL-THESIS", "MARKET-GAP", "COMPETITIVE-MOAT"},
        domains={"*"},
        rewrite_tmpl=(
            "Instantiate \"{thesis}\" in one concrete, named application within {domain} (a specific "
            "product, workflow, or go-to-market motion). What breaks at contact with reality? What is "
            "the minimum buildable artifact that would prove or kill the thesis?"
        ),
    ),
    ForkPrimitive(
        id="POWER", lens="coalition / incentive / competitive-dynamics map",
        role="diverge", triggers={"POWER-MAP", "MARKET-INFLECTION"},
        domains={"*"},
        rewrite_tmpl=(
            "Map the actors, incentives, and coalitions whose behavior \"{thesis}\" depends on. Who wins, "
            "who is threatened, who must move first, and what second-order reaction does that trigger? "
            "Output the incentive map and the most likely equilibrium shift."
        ),
    ),
]

PRIM_BY_ID = {p.id: p for p in PRIMITIVES}

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass
class Anchor:
    label: str
    body: str
    longform_seed: str = ""
    json_cluster: str = ""
    social_fragment: str = ""


@dataclass
class Node:
    id: str
    brief: str
    parent_id: Optional[str] = None
    fork_type: Optional[str] = None        # which primitive produced this node
    depth: int = 0
    domain: str = ""
    status: str = "init"                   # init|prompted|awaiting_research|researched|transformed|forked|pruned|saturated
    xml_prompt: str = ""
    research_raw: str = ""
    anchors: list = field(default_factory=list)   # list[Anchor] (serialized as dicts)
    deliverables: str = ""
    children: list = field(default_factory=list)  # child node ids
    novelty: Optional[float] = None
    tokens_used: int = 0

    def anchor_labels(self) -> set:
        return {a["label"] if isinstance(a, dict) else a.label for a in self.anchors}

    def thesis(self) -> str:
        """Best available thesis text: STRUCTURAL-THESIS anchor body, else brief."""
        for a in self.anchors:
            d = a if isinstance(a, dict) else asdict(a)
            if d["label"] == "STRUCTURAL-THESIS":
                return d["body"]
        return self.brief


class Campaign:
    def __init__(self, root: Path, skills_dir: Path = SKILLS_DIR_DEFAULT):
        self.root = root
        self.skills_dir = skills_dir
        self.state_path = root / "state.json"
        self.nodes: dict[str, Node] = {}
        self.meta: dict = {}
        if self.state_path.exists():
            self._load()

    # -- persistence --------------------------------------------------------- #
    def _load(self):
        data = json.loads(self.state_path.read_text())
        self.meta = data.get("meta", {})
        self.nodes = {nid: Node(**nd) for nid, nd in data.get("nodes", {}).items()}

    def save(self):
        self.root.mkdir(parents=True, exist_ok=True)
        data = {"meta": self.meta, "nodes": {nid: asdict(n) for nid, n in self.nodes.items()}}
        self.state_path.write_text(json.dumps(data, indent=2))

    # -- skill loading ------------------------------------------------------- #
    def skill(self, name: str) -> str:
        p = self.skills_dir / name
        if not p.exists():
            sys.exit(f"[moea] missing skill file: {p}\n       put your real SKILL.md files in {self.skills_dir}/")
        return p.read_text()

    # -- node helpers -------------------------------------------------------- #
    def get(self, nid: str) -> Node:
        if nid not in self.nodes:
            sys.exit(f"[moea] no node '{nid}'. `status` to list nodes.")
        return self.nodes[nid]

    def add(self, node: Node):
        self.nodes[node.id] = node


# --------------------------------------------------------------------------- #
# Anchor parsing
# --------------------------------------------------------------------------- #

ANCHOR_RE = re.compile(r"\[STT-ANCHOR:\s*([A-Z0-9\-]+)\s*\](.*?)\[/STT-ANCHOR\]", re.DOTALL)
SUB_RE = {
    "longform_seed":  re.compile(r"\[longform-seed\]:\s*(.+?)(?:\n|$)", re.IGNORECASE),
    "json_cluster":   re.compile(r"\[json-cluster\]:\s*(\{.*?\})", re.DOTALL | re.IGNORECASE),
    "social_fragment":re.compile(r"\[social-fragment\]:\s*(.+?)(?:\n|$)", re.IGNORECASE),
}

def parse_anchors(text: str) -> list[Anchor]:
    out = []
    for label, body in ANCHOR_RE.findall(text):
        body = body.strip()
        a = Anchor(label=label.strip(), body=body)
        for fld, rx in SUB_RE.items():
            m = rx.search(body)
            if m:
                setattr(a, fld, m.group(1).strip())
        out.append(a)
    return out


# --------------------------------------------------------------------------- #
# Novelty ledger  --  prevents recursion collapsing into restatement
# --------------------------------------------------------------------------- #
#
# Default is offline + dependency-free: lexical Jaccard over content tokens of the
# thesis text. A candidate fork's projected brief is scored against every existing
# node's thesis; if it overlaps an existing entry above the floor, the primitive is
# dropped from the pool. If both pools empty out, the branch is SATURATED -> terminate.
# In --backend claude mode this can be upgraded to a Claude-judged 0-1 novelty score.

_STOP = set("the a an and or of to in on for with is are be as that this it by from at into "
            "we our their its which not but if then than so can could would should may might "
            "via per each both more most less low high new key core single also within across "
            "what how why does do done using used".split())

def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in _STOP}

def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def max_overlap(text: str, ledger: list[str]) -> float:
    return max((jaccard(text, e) for e in ledger), default=0.0)


# --------------------------------------------------------------------------- #
# Fork selection  --  the typed rewrite step
# --------------------------------------------------------------------------- #

def select_forks(node: Node, ledger: list[str], novelty_floor: float) -> list[ForkPrimitive]:
    """Return [best_deepen, best_diverge] that clear the novelty floor. May return
    0, 1, or 2 primitives. Empty -> branch saturated."""
    labels = node.anchor_labels()
    thesis = node.thesis()
    domain = node.domain

    def pool(role):
        scored = []
        for p in (x for x in PRIMITIVES if x.role == role):
            aff = p.fires_on(labels, domain)
            projected = p.rewrite(thesis, domain)
            overlap = max_overlap(projected, ledger)
            novelty = 1.0 - overlap
            if novelty < novelty_floor:
                continue  # this angle already covered
            scored.append((aff + novelty, novelty, p))
        scored.sort(key=lambda t: t[0], reverse=True)
        return scored

    picks = []
    for role in ("deepen", "diverge"):
        s = pool(role)
        if s:
            picks.append(s[0][2])
    return picks


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #

class ManualBackend:
    """Prints paste-ready blocks. The human runs Claude/Gemini and pastes results back."""
    name = "manual"

    def stage1(self, camp, node):
        skill = camp.skill(STAGE1_SKILL)
        block = _paste_block(
            title=f"STAGE 1 -- generate the deep-research XML for node {node.id}",
            instruction="Paste the block below into Claude. Save the XML it returns, then run:\n"
                        f"    moea ingest {node.id} --file <research_output.md>   (after running the XML in Gemini)\n"
                        f"or save the XML first with:  moea set-prompt {node.id} --file <xml>",
            skill=skill,
            payload=f"BRIEF:\n{node.brief}\n\nTARGET PLATFORM: Gemini Deep Research",
        )
        print(block)
        node.status = "prompted"
        return ""  # nothing to store automatically in manual mode

    def research(self, camp, node):
        print(textwrap.dedent(f"""
        [manual] Run node {node.id}'s saved XML prompt in Gemini Deep Research (or Claude),
                 then ingest the result:
                     moea ingest {node.id} --file <output.md>
        """))
        node.status = "awaiting_research"
        return ""

    def stage2(self, camp, node):
        skill = camp.skill(STAGE2_SKILL)
        block = _paste_block(
            title=f"STAGE 2 -- run the Semantic Triple Transformation on node {node.id}",
            instruction="Paste into Claude. Save the four deliverables, then:\n"
                        f"    moea set-deliverables {node.id} --file <deliverables.md>",
            skill=skill,
            payload=f"DEEP RESEARCH OUTPUT:\n\n{node.research_raw}",
        )
        print(block)
        return ""

    def novelty(self, camp, projected, ledger):
        return 1.0 - max_overlap(projected, ledger)


class ClaudeBackend:
    """Live Anthropic API. Stage 1 + research(optional) + Stage 2 + novelty scoring."""
    name = "claude"

    def __init__(self):
        try:
            import anthropic  # noqa
        except ImportError:
            sys.exit("[moea] auto mode needs the SDK:  pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("[moea] set ANTHROPIC_API_KEY for --backend claude")
        from anthropic import Anthropic
        self.client = Anthropic()

    def _call(self, model, system, user, max_tokens=8000):
        r = self.client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        used = r.usage.input_tokens + r.usage.output_tokens
        return text, used

    def stage1(self, camp, node):
        skill = camp.skill(STAGE1_SKILL)
        out, used = self._call(MODELS["architect"], skill,
                               f"BRIEF:\n{node.brief}\n\nTARGET PLATFORM: Gemini Deep Research",
                               max_tokens=6000)
        node.tokens_used += used
        node.status = "prompted"
        return out

    def research(self, camp, node):
        # Claude-native research path. (Swap this method for a Gemini API adapter to keep
        # the adversarial-model role; the orchestrator only needs anchored markdown back.)
        sys_p = ("You are a deep-research engine. Execute the following structured research prompt "
                 "in full. Produce 2500-4000 words of synthesis (not summary). You MUST emit "
                 "[STT-ANCHOR: LABEL]...[/STT-ANCHOR] blocks at every structural thesis point, each "
                 "containing [longform-seed], [json-cluster], and [social-fragment] sub-elements.")
        out, used = self._call(MODELS["research"], sys_p, node.xml_prompt, max_tokens=16000)
        node.tokens_used += used
        return out

    def stage2(self, camp, node):
        skill = camp.skill(STAGE2_SKILL)
        out, used = self._call(MODELS["transform"], skill,
                               f"DEEP RESEARCH OUTPUT:\n\n{node.research_raw}",
                               max_tokens=16000)
        node.tokens_used += used
        return out

    def novelty(self, camp, projected, ledger):
        if not ledger:
            return 1.0
        sys_p = ("Rate how NOVEL a proposed research direction is versus directions already explored. "
                 "Return ONLY a float 0.0-1.0 (1.0 = entirely new angle, 0.0 = restatement). No prose.")
        led = "\n---\n".join(f"[{i}] {e[:600]}" for i, e in enumerate(ledger))
        user = f"ALREADY EXPLORED:\n{led}\n\nPROPOSED:\n{projected}\n\nNovelty score:"
        out, used = self._call(MODELS["scorer"], sys_p, user, max_tokens=16)
        try:
            return max(0.0, min(1.0, float(re.search(r"[01](?:\.\d+)?", out).group())))
        except Exception:
            return 1.0 - max_overlap(projected, ledger)


def get_backend(name: str):
    return {"manual": ManualBackend, "claude": ClaudeBackend}[name]()


# --------------------------------------------------------------------------- #
# Presentation helpers
# --------------------------------------------------------------------------- #

def _paste_block(title, instruction, skill, payload):
    bar = "=" * 78
    return (f"\n{bar}\n  {title}\n{bar}\n{instruction}\n"
            f"\n----- BEGIN PASTE (system skill + input) -----\n\n{skill}\n\n{'-'*40}\n\n{payload}\n"
            f"\n----- END PASTE -----\n{bar}\n")


def _led(camp: Campaign) -> list[str]:
    """Build the novelty ledger from all non-pruned nodes' thesis text."""
    return [n.thesis() for n in camp.nodes.values() if n.status not in ("pruned",) and (n.anchors or n.brief)]


# --------------------------------------------------------------------------- #
# Core operations (shared by manual CLI steps and the auto runner)
# --------------------------------------------------------------------------- #

def do_fork(camp: Campaign, node: Node, backend, novelty_floor: float, verbose=True) -> list[Node]:
    if not node.anchors:
        if verbose:
            print(f"[moea] node {node.id} has no parsed anchors -- ingest research first.")
        return []
    ledger = [t for nid, t in ((n.id, n.thesis()) for n in camp.nodes.values()) if nid != node.id]
    picks = select_forks(node, ledger, novelty_floor)
    if not picks:
        node.status = "saturated"
        if verbose:
            print(f"[moea] node {node.id} SATURATED -- no fork clears novelty floor {novelty_floor}. Branch terminates.")
        return []

    children = []
    thesis = node.thesis()
    existing_suffixes = [c.split(".")[-1] for c in node.children]
    base = max([int(s) for s in existing_suffixes if s.isdigit()] + [0])
    for i, prim in enumerate(picks, start=base + 1):
        child_brief = prim.rewrite(thesis, node.domain)
        # backend-scored novelty of the actual child brief vs ledger
        nov = backend.novelty(camp, child_brief, ledger)
        cid = f"{node.id}.{i}"
        child = Node(id=cid, brief=child_brief, parent_id=node.id, fork_type=prim.id,
                     depth=node.depth + 1, domain=node.domain, novelty=round(nov, 3))
        camp.add(child)
        node.children.append(cid)
        children.append(child)
        if verbose:
            print(f"[moea]  fork {cid}  [{prim.role.upper():7} {prim.id}]  novelty={nov:.2f}")
            print(f"          {textwrap.shorten(child_brief, 140)}")
    node.status = "forked"
    return children


def ingest_research(camp: Campaign, node: Node, text: str):
    node.research_raw = text
    node.anchors = [asdict(a) for a in parse_anchors(text)]
    node.status = "researched"
    n = len(node.anchors)
    flag = "" if n >= 5 else f"  (warning: {n} anchors; STT wants >=5 for full coverage)"
    print(f"[moea] ingested node {node.id}: {n} anchors -> {sorted(node.anchor_labels())}{flag}")


# --------------------------------------------------------------------------- #
# Auto runner  --  bounded autonomous recursion
# --------------------------------------------------------------------------- #

def run_auto(camp: Campaign, start_id: str, backend, depth: int, budget: int,
             novelty_floor: float, native_research: bool):
    """BFS over the tree. Each node: stage1 -> research -> stage2 -> fork. Stops on
    depth / token budget / saturation."""
    import collections
    q = collections.deque([start_id])
    total = camp.meta.get("tokens_used", 0)

    while q:
        node = camp.get(q.popleft())
        if node.depth > depth:
            continue
        print(f"\n=== node {node.id}  (depth {node.depth}, fork={node.fork_type})  budget {total}/{budget} ===")

        if not node.xml_prompt:
            node.xml_prompt = backend.stage1(camp, node)
        if not node.research_raw:
            if not native_research:
                print(f"[moea] paused at {node.id}: external research needed. "
                      f"Run the saved prompt, then `ingest {node.id}` and `run` again to resume.")
                node.status = "awaiting_research"
                camp.save()
                return
            ingest_research(camp, node, backend.research(camp, node))
        if not node.deliverables:
            node.deliverables = backend.stage2(camp, node)
            node.status = "transformed"
            print(f"[moea] STT complete for {node.id} ({len(node.deliverables)} chars)")

        total = sum(n.tokens_used for n in camp.nodes.values())
        camp.meta["tokens_used"] = total
        camp.save()

        if total >= budget:
            print(f"[moea] token budget {budget} reached. Stopping. Resume later with `run`.")
            return
        if node.depth >= depth:
            print(f"[moea] node {node.id} at max depth {depth}; not forking.")
            continue

        for child in do_fork(camp, node, backend, novelty_floor):
            q.append(child.id)
        camp.save()

    print(f"\n[moea] frontier exhausted. {len(camp.nodes)} nodes, {total} tokens used.")


# --------------------------------------------------------------------------- #
# Tree rendering
# --------------------------------------------------------------------------- #

def render_tree(camp: Campaign, nid: str = "0", prefix=""):
    if nid not in camp.nodes:
        return
    n = camp.nodes[nid]
    tag = f"[{n.fork_type}]" if n.fork_type else "[root]"
    nov = f" nov={n.novelty}" if n.novelty is not None else ""
    print(f"{prefix}{nid} {tag} <{n.status}>{nov}  {textwrap.shorten(n.brief, 80)}")
    for i, c in enumerate(n.children):
        render_tree(camp, c, prefix + "    ")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    p = argparse.ArgumentParser(prog="moea", description="ACRA MoEA recursive research orchestrator")
    p.add_argument("--campaign", default="campaign", help="campaign directory (default: ./campaign)")
    p.add_argument("--skills", default=str(SKILLS_DIR_DEFAULT), help="dir holding the two SKILL.md files")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="start a campaign from a seed brief")
    s.add_argument("--brief", required=True)
    s.add_argument("--domain", default="", help="domain tag (e.g. physics, ai, neuro, cyber) -- biases fork affinity")

    for name, help_ in [("prompt", "emit/generate the Stage-1 XML for a node"),
                        ("research", "run (or prompt for) the deep research step"),
                        ("stt", "run (or prompt for) the Stage-2 transformation"),
                        ("fork", "select two typed forks and spawn child nodes")]:
        sp = sub.add_parser(name, help=help_); sp.add_argument("node")
        sp.add_argument("--backend", default="manual", choices=["manual", "claude"])
        if name == "fork":
            sp.add_argument("--novelty-floor", type=float, default=0.25)

    sp = sub.add_parser("ingest", help="attach pasted deep-research output to a node"); sp.add_argument("node"); sp.add_argument("--file", required=True)
    sp = sub.add_parser("set-prompt", help="attach a saved XML prompt to a node"); sp.add_argument("node"); sp.add_argument("--file", required=True)
    sp = sub.add_parser("set-deliverables", help="attach saved STT deliverables"); sp.add_argument("node"); sp.add_argument("--file", required=True)

    sp = sub.add_parser("run", help="bounded autonomous recursion")
    sp.add_argument("node", nargs="?", default="0")
    sp.add_argument("--backend", default="claude", choices=["manual", "claude"])
    sp.add_argument("--depth", type=int, default=2)
    sp.add_argument("--budget", type=int, default=400_000, help="cumulative token budget")
    sp.add_argument("--novelty-floor", type=float, default=0.25)
    sp.add_argument("--native-research", action="store_true", help="use Claude as the research backend (no external paste)")

    sub.add_parser("status", help="list nodes")
    sub.add_parser("tree", help="render the derivation tree")

    args = p.parse_args(argv)
    camp = Campaign(Path(args.campaign), Path(args.skills))

    if args.cmd == "init":
        camp.meta = {"created": time.strftime("%Y-%m-%d"), "domain": args.domain, "tokens_used": 0}
        camp.add(Node(id="0", brief=args.brief, domain=args.domain))
        camp.save()
        print(f"[moea] campaign '{args.campaign}' initialized. root node 0.\n"
              f"       next:  moea prompt 0   (then run it, then  moea ingest 0 --file out.md)")
        return

    if args.cmd in ("prompt", "research", "stt", "fork"):
        backend = get_backend(args.backend)
        node = camp.get(args.node)
        if args.cmd == "prompt":
            out = backend.stage1(camp, node)
            if out:
                node.xml_prompt = out; print(out)
        elif args.cmd == "research":
            out = backend.research(camp, node)
            if out:
                ingest_research(camp, node, out)
        elif args.cmd == "stt":
            if not node.research_raw:
                sys.exit(f"[moea] node {node.id} has no research yet. ingest it first.")
            out = backend.stage2(camp, node)
            if out:
                node.deliverables = out; node.status = "transformed"; print(out)
        elif args.cmd == "fork":
            do_fork(camp, node, backend, args.novelty_floor)
        camp.save(); return

    if args.cmd in ("ingest", "set-prompt", "set-deliverables"):
        node = camp.get(args.node)
        text = Path(args.file).read_text()
        if args.cmd == "ingest":
            ingest_research(camp, node, text)
        elif args.cmd == "set-prompt":
            node.xml_prompt = text; node.status = "prompted"; print(f"[moea] prompt set on {node.id}")
        else:
            node.deliverables = text; node.status = "transformed"; print(f"[moea] deliverables set on {node.id}")
        camp.save(); return

    if args.cmd == "run":
        backend = get_backend(args.backend)
        run_auto(camp, args.node, backend, args.depth, args.budget, args.novelty_floor, args.native_research)
        return

    if args.cmd == "status":
        for nid in sorted(camp.nodes, key=lambda x: [int(p) for p in x.split(".")]):
            n = camp.nodes[nid]
            print(f"  {nid:8} <{n.status:14}> fork={str(n.fork_type):11} anchors={len(n.anchors)} "
                  f"tok={n.tokens_used} :: {textwrap.shorten(n.brief, 70)}")
        print(f"  total tokens: {sum(n.tokens_used for n in camp.nodes.values())}")
        return

    if args.cmd == "tree":
        render_tree(camp); return


if __name__ == "__main__":
    main()

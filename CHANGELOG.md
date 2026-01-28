# Changelog

All notable changes to Phylax are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2026-01-28

### 🎉 First Stable Release

Phylax v1.0.0 marks the first production-ready release with frozen API contracts.

### Added

#### Phase 26 — Contract Freeze
- `docs/contract.md` — Guaranteed stable APIs
- `docs/invariants.md` — 10 semantic invariants
- `tests/test_contract.py` — Contract enforcement tests

#### Phase 27 — Failure Modes
- `docs/failure-modes.md` — Explicit failure taxonomy
- Determinism guarantees documented
- Error codes standardized

#### Phase 28 — Documentation
- `docs/quickstart.md` — 10 min to CI failure
- `docs/mental-model.md` — What Phylax is/isn't
- `docs/graph-model.md` — Execution graph guide
- `docs/failure-playbook.md` — Debug procedures

#### Phase 29-33 — V1 Preparation
- `docs/versioning.md` — Semantic versioning policy
- `docs/performance.md` — Scale bounds and limits
- CHANGELOG.md created

### Changed
- SDK version bumped to 1.0.0
- README updated for v1.0
- **Renamed from Sentinel to Phylax**

### Fixed
- Fixed investigation_path list comprehension syntax

---

## [0.5.0] - 2026-01-22

### Added

#### Phase 19 — Semantic Nodes
- `NodeRole` enum (INPUT, TRANSFORM, LLM, TOOL, VALIDATION, OUTPUT)
- `human_label` and `description` on GraphNode
- Auto-inference of node roles

#### Phase 20 — Hierarchical Graphs
- `GraphStage` model for grouping nodes
- Collapsible stages in UI

#### Phase 21 — Time Visualization
- Latency heatmap colors
- Bottleneck badges
- Time bars on nodes

#### Phase 22 — Forensics Mode
- Toggle for debug focus
- Faded non-relevant nodes
- Pulsing root cause

#### Phase 23 — Graph Diffs
- `GraphDiff` and `NodeDiff` models
- `diff_with()` method on ExecutionGraph
- `/executions/{a}/diff/{b}` endpoint

#### Phase 24 — Investigation Paths
- `investigation_path()` method
- Deterministic debug guidance
- `/executions/{id}/investigate` endpoint

#### Phase 25 — Enterprise Hardening
- `compute_hash()` for integrity
- `to_snapshot()` for immutable snapshots
- `verify_integrity()` for tamper detection
- `/executions/{id}/snapshot`, `/export`, `/verify` endpoints

---

## [0.4.0] - 2026-01-20

### Added
- Phase 14-18 execution graph features
- Graph construction from traces
- Graph verdict computation
- Performance analysis (critical path, bottlenecks)

---

## [0.3.0] - 2026-01-15

### Added
- Phase 13 execution context
- Multi-step agent support
- Parent-child trace linking

---

## [0.2.0] - 2026-01-10

### Added
- Phase 7-12 core features
- Expectation engine (4 rules)
- Golden traces and blessing
- CI integration (`phylax check`)
- Failure-first UI

---

## [0.1.0] - 2026-01-05

### Added
- Initial SDK release
- `@trace` and `@expect` decorators
- Gemini and OpenAI adapters
- FastAPI server
- CLI commands
- File-based storage

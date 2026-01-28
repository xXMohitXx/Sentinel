# Phylax Versioning Policy

> **How we version Phylax releases.**

---

## Semantic Versioning

Phylax follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
1.0.0
```

---

## Version Rules

### MAJOR (1.x.x → 2.x.x)

**When**: Breaking changes to guaranteed APIs.

Examples:
- Removing `@trace` or `@expect`
- Changing verdict semantics
- Breaking CLI command signatures
- Removing guaranteed endpoints

**Promise**: We will avoid this. When necessary:
- 6 months deprecation notice
- Migration guide provided
- Old version supported for 12 months

---

### MINOR (1.0.x → 1.1.x)

**When**: New features, backward compatible.

Examples:
- New expectation rules (e.g., `max_tokens`)
- New CLI commands
- New API endpoints
- New graph analysis features
- UI improvements

**Promise**: Your code continues working.

---

### PATCH (1.0.0 → 1.0.1)

**When**: Bug fixes, no new features.

Examples:
- Fix incorrect verdict calculation
- Fix storage corruption issue
- Fix UI rendering bug
- Performance improvements
- Documentation fixes

**Promise**: Only fixes, no surprises.

---

## Pre-Release Versions

```
1.0.0-alpha.1   → Unstable, may break
1.0.0-beta.1    → Feature complete, testing
1.0.0-rc.1      → Release candidate, final testing
```

**Promise**: Pre-releases are NOT covered by stability guarantees.

---

## Deprecation Policy

Before removing any feature:

1. **Announce** in release notes (MINOR version)
2. **Warn** via runtime log message
3. **Document** migration path
4. **Remove** in next MAJOR only (minimum 6 months)

Example:
```
v1.2.0: "The 'foo' parameter is deprecated. Use 'bar' instead."
v2.0.0: "The 'foo' parameter has been removed."
```

---

## Release Cadence

| Type | Frequency | Examples |
|------|-----------|----------|
| PATCH | As needed | Bug fixes, security |
| MINOR | Monthly | New features |
| MAJOR | Yearly (max) | Breaking changes |

---

## Support Policy

| Version | Support Level |
|---------|---------------|
| Current MAJOR | Full support |
| Previous MAJOR | Security fixes only (12 months) |
| Older | Unsupported |

Example:
- v1.x.x releases → Full support
- v0.x.x releases → Unsupported after v1.0.0

---

## How to Check Version

```python
import sdk
print(sdk.__version__)  # "1.0.0"
```

```bash
python -m cli.main --version
```

---

## Changelog

All releases are documented in `CHANGELOG.md`:

```markdown
## [1.0.0] - 2026-01-26

### Added
- Phase 26-35 v1.0 release features

### Changed
- Finalized API contract

### Fixed
- Fixed investigation_path syntax error
```

---

*This policy applies to Phylax v1.0.0+*

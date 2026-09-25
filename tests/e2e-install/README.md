# ScanLLM end-to-end install kit

Installs `scanllm` into a throwaway virtualenv exactly the way a new user
would, scans pinned open-source repos, and asserts on the results.

It answers two questions:

1. **Does the published package actually work on a clean machine?**
   (No editable install, no repo checkout, no dev dependencies.)
2. **Did we break detection when we shipped that feature?**

## Usage

```bash
cd tests/e2e-install

./run.sh                            # test the current PyPI release
./run.sh --source pypi==2.3.2       # test a specific published version
./run.sh --source local             # test this working tree BEFORE releasing
./run.sh --source wheel:../../dist/scanllm-2.3.3-py3-none-any.whl
./run.sh --extras all               # include server/reports/watch extras
./run.sh --keep                     # reuse the venv (fast reruns)
./run.sh --python python3.11        # pin an interpreter
```

Exit code `0` = all blocking checks passed, `1` = a regression.

Everything lands in `.work/` (gitignored): the venv, cached fixture repos,
and raw scan output per format in `.work/results/`. Inspect those when a
check fails.

## The release ritual

```bash
./run.sh --source local             # before you tag
./run.sh --source pypi==<new>       # after PyPI publishes
```

If the second run behaves differently from the first, the package is missing
files, extras, or data (e.g. `ai_signatures.yaml` not included in the wheel) —
a class of bug that unit tests never catch because they run from the repo.

## Fixtures

`fixtures.txt` pins repos to exact commits so expected counts stay stable:

| repo | why it is here |
|---|---|
| `langchain-ai/langserve` | Python + LangChain, plus a bundled TS playground |
| `mckaywrigley/chatbot-ui` | TS/Next.js, 10 providers, real prompt assembly, real secret-shaped code |

Add a repo by appending `name<TAB>url<TAB>sha`. Pick repos with *known*
AI content so the assertions mean something.

## How checks work (`checks.py`)

Four outcomes:

- **CHECK** — must hold. Failure exits non-zero. This is the release gate.
- **DRIFT** — finding counts on pinned repos. Signatures legitimately evolve,
  so a change is reported loudly but does not fail the run. Review it; if the
  new number is correct, update the expected value.
- **KNOWN** — a bug confirmed present in 2.3.2, recorded so it stays visible
  without failing the build.
- **FIXED** — a KNOWN bug that no longer reproduces. The kit tells you to
  promote it to a CHECK so it can never regress.

**When you ship a feature, add a CHECK for it.** That is what turns this from
a smoke test into a regression net. Assert on the true positive you intended
to create, not just on "it ran".

### Known bugs recorded against 2.3.2

| # | Bug |
|---|---|
| 1 | `types/valid-keys.ts` — a TS enum of key *names* counted as 8 hardcoded credentials, which alone pins the grade to F |
| 2 | Any JS template literal with `${}` flagged as LLM01 prompt injection, including auth redirects and UI code |
| 3 | `findings[]` has `pattern_severity` but no `severity` / `finding_type`, so JSON consumers read `null` |
| 4 | `risk.severity_counts` contradicts `summary.severities` in the same document |
| 5 | `scan --severity high` does not filter (already fixed in the working tree) |
| 6 | `scan` exits 0 even at grade F, so it cannot gate CI on its own |
| 7 | `doctor` remediation renders as `pip install 'scanllm'` — Rich parses `[server]` as a style tag and drops it. Fix with `rich.markup.escape()` or `markup=False`, not with quoting |

Also seen during install: `pyproject.toml` requires `typer[all]`, but typer
≥0.13 dropped the `all` extra, so every install prints
`WARNING: typer 0.23.2 does not provide the extra 'all'`.

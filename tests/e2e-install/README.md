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

### Bug status

Fixed since 2.3.2 and now guarded by blocking CHECKs — these cannot regress:

| # | Bug | Effect of the fix |
|---|---|---|
| 1 | `types/valid-keys.ts` — a TS enum of key *names* counted as 8 hardcoded credentials | chatbot-ui **F → B** |
| 2 | Any JS template literal with `${}` flagged as LLM01, including auth redirects and UI code | 20 high → 3 high; all 3 remaining are real |
| 3 | `scan --severity high` did not filter | filter works |
| 4 | `scan` could not gate CI | `--fail-on <grade\|severity>`; bare `scan` still exits 0 |
| 5 | `doctor` hint rendered `pip install 'scanllm'` (Rich ate `[server]`) | hint keeps the extra |
| 6 | `pyproject` required the dropped `typer[all]` extra | install is warning-free |
| 7 | `.scanllm/` was not excluded, so each scan re-ingested the previous scan's output — findings inflated 81 → 108 and the saved file grew 97KB → 1.5MB over four runs | scans are idempotent |

Still open:

| Bug | Notes |
|---|---|
| `findings[]` has `pattern_severity` but no `severity` / `finding_type`, so JSON consumers read `null` | schema work in progress |
| `risk.severity_counts` contradicts `summary.severities` in the same document | same |

### Current baseline

| repo | findings | grade |
|---|---|---|
| langserve | 57 | A (10) |
| chatbot-ui | 81 | B (30) |

If your run reports DRIFT against these, decide whether the new number is
correct before updating it. Drift is a prompt to think, not a failure.

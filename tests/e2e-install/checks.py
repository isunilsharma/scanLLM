#!/usr/bin/env python3
"""Assertions for the ScanLLM end-to-end install kit.

Three kinds of check:

  CHECK  — behaviour that must hold. A failure is a release blocker.
  DRIFT  — detection counts on pinned repos. A change is not automatically
           wrong (signatures evolve), but it must be looked at, so it is
           reported loudly and does not fail the run.
  KNOWN  — a bug confirmed present in 2.3.2. Still broken => xfail (no
           failure). Fixed => XPASS, which tells you to promote it to CHECK.

Add new CHECKs here whenever you ship a feature; that is what makes this a
regression net rather than a one-off smoke test.
"""
import argparse
import json
import os
import sys

PASS, FAIL, XFAIL, XPASS, DRIFTED = [], [], [], [], []


def _load(results, name):
    p = os.path.join(results, name)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return None
    try:
        with open(p) as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        return None


def check(label, ok, detail=""):
    (PASS if ok else FAIL).append((label, detail))


def known(label, still_broken, detail=""):
    """Register a known 2.3.2 bug. still_broken=True -> xfail."""
    (XFAIL if still_broken else XPASS).append((label, detail))


def drift(label, actual, expected):
    if actual == expected:
        PASS.append((f"{label} == {expected}", ""))
    else:
        DRIFTED.append((label, f"expected {expected}, got {actual}"))


def findings_at(data, path_frag, pattern=None):
    out = []
    for f in data.get("findings", []):
        if path_frag in (f.get("file_path") or ""):
            if pattern is None or pattern in (f.get("pattern_name") or ""):
                out.append(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--version", default="")
    ap.add_argument("--source", default="")
    a = ap.parse_args()
    R = a.results

    # ---------------------------------------------------------- install ---
    check("CLI reports a version", bool(a.version), a.version)
    if a.source.startswith("pypi=="):
        want = a.source.split("==", 1)[1]
        check(f"installed version matches requested {want}",
              a.version == want, f"got {a.version}")

    doctor = ""
    if os.path.exists(os.path.join(R, "doctor.txt")):
        doctor = open(os.path.join(R, "doctor.txt")).read()
    check("doctor runs and self-reports version",
          f"scanllm {a.version}" in doctor)
    check("doctor loads AI signatures", "signatures loaded" in doctor)

    # --------------------------------------------------------- per repo ---
    ls = _load(R, "langserve.json")
    cb = _load(R, "chatbot-ui.json")
    check("langserve scan produced valid JSON", ls is not None)
    check("chatbot-ui scan produced valid JSON", cb is not None)

    for name, data in (("langserve", ls), ("chatbot-ui", cb)):
        if not data:
            continue
        s = data.get("summary", {})
        check(f"{name}: has summary/risk/owasp/graph blocks",
              all(k in data for k in ("summary", "risk", "owasp", "graph")))
        check(f"{name}: scanned > 0 files", s.get("files_scanned", 0) > 0)
        check(f"{name}: found AI components", s.get("total_findings", 0) > 0)
        check(f"{name}: risk score in 0..100",
              0 <= data.get("risk", {}).get("overall_score", -1) <= 100)
        check(f"{name}: risk grade assigned",
              data.get("risk", {}).get("grade") in list("ABCDF"))

        # SARIF / CycloneDX must be well-formed for CI + compliance consumers
        sarif = _load(R, f"{name}.sarif.json")
        check(f"{name}: SARIF is valid JSON with runs[]",
              bool(sarif) and isinstance(sarif.get("runs"), list))
        cdx = _load(R, f"{name}.cdx.json")
        check(f"{name}: CycloneDX is valid JSON with components[]",
              bool(cdx) and isinstance(cdx.get("components"), list))
        if cdx:
            check(f"{name}: CycloneDX declares bomFormat",
                  cdx.get("bomFormat") == "CycloneDX")

    # ------------------------------------------- true-positive detection ---
    if ls:
        provs = set(ls["summary"].get("providers", {}))
        check("langserve: detects langchain", "langchain" in provs, str(provs))
        drift("langserve: total findings", ls["summary"]["total_findings"], 57)
        drift("langserve: ai files", ls["summary"]["ai_files_count"], 11)

    if cb:
        provs = set(cb["summary"].get("providers", {}))
        for want in ("openai", "anthropic", "langchain"):
            check(f"chatbot-ui: detects {want}", want in provs, str(sorted(provs)))
        check("chatbot-ui: detects a local/self-hosted runtime (ollama)",
              "ollama" in provs, str(sorted(provs)))
        # This one is a genuine prompt-injection surface: user text is
        # interpolated into an LLM prompt. It must keep being flagged.
        bp = findings_at(cb, "lib/build-prompt.ts", "prompt_injection")
        check("chatbot-ui: flags real prompt construction in lib/build-prompt.ts",
              len(bp) >= 3, f"{len(bp)} hits")
        drift("chatbot-ui: total findings", cb["summary"]["total_findings"], 81)
        drift("chatbot-ui: providers detected", len(provs), 10)

    # ---------------------------------- precision regressions (promoted) ---
    # These were false positives in 2.3.2. They are now blocking checks so
    # they can never come back.
    if cb:
        vk = findings_at(cb, "types/valid-keys.ts", "hardcoded_credential")
        check("no FP: TS enum of key names is not reported as a secret",
              len(vk) == 0, f"{len(vk)} false secrets")

        noise = (findings_at(cb, "login/page.tsx", "template_literal")
                 + findings_at(cb, "components/ui/form.tsx", "template_literal")
                 + findings_at(cb, "db/storage/files.ts", "template_literal"))
        check("no FP: template literals in auth/ui/storage code are not LLM01",
              len(noise) == 0, f"{len(noise)} hits")

        check("chatbot-ui: grade recovered from F to a realistic grade",
              cb["risk"]["grade"] in ("A", "B", "C"),
              f"grade {cb['risk']['grade']} score {cb['risk']['overall_score']}")

    if ls:
        ls_noise = findings_at(ls, "CorrectnessFeedback.tsx", "template_literal")
        check("no FP: React error-message template literals are not LLM01",
              len(ls_noise) == 0, f"{len(ls_noise)} hits")

    # Scanning must be reproducible: scan --save writes .scanllm/ into the
    # target, and re-ingesting it used to inflate every subsequent run.
    idem = _load(R, "idempotency-2.json")
    if idem and cb:
        check("scan is idempotent (re-scanning gives identical counts)",
              idem["summary"]["total_findings"] == cb["summary"]["total_findings"],
              f"{cb['summary']['total_findings']} then "
              f"{idem['summary']['total_findings']}")

    # CI gating via --fail-on.
    def _exit(fn):
        p_ = os.path.join(R, fn)
        return open(p_).read().strip() if os.path.exists(p_) else None

    check("gate: bare scan still exits 0 (no pipeline breakage on upgrade)",
          _exit("gate-default.exit") == "0", f"got {_exit('gate-default.exit')}")
    check("gate: --fail-on trips and exits 1",
          _exit("gate-strict.exit") == "1", f"got {_exit('gate-strict.exit')}")
    check("gate: invalid --fail-on exits 2 without a traceback",
          _exit("gate-bogus.exit") == "2", f"got {_exit('gate-bogus.exit')}")

    # ------------------------------------------- table readability --------
    # 57 findings used to print as 57 rows, truncated to `impo…` at 80 cols.
    for name, data in (("langserve", ls), ("chatbot-ui", cb)):
        t80 = os.path.join(R, f"{name}.table80.txt")
        if not (data and os.path.exists(t80)):
            continue
        txt = open(t80).read()
        check(f"{name}: table collapses duplicate findings",
              "unique" in txt or "more findings" in txt,
              "no dedup marker in header/caption")
        check(f"{name}: severity column is not truncated at 80 cols",
              "Sever…" not in txt and "Seve…" not in txt)
        check(f"{name}: finding column is not truncated to uselessness",
              "impo…" not in txt)
        # Count only rows inside the findings table, not the Rich panels
        # that follow it (those also start with a box-drawing char).
        rows, inside = 0, False
        for line in txt.splitlines():
            if line.startswith("\u250f"):        # table top border
                inside = True
            elif line.startswith("\u2514"):      # table bottom border
                inside = False
            elif inside and line.startswith("\u2502"):
                rows += 1
        check(f"{name}: table is capped to a readable number of rows",
              rows <= 30, f"{rows} table rows")
        check(f"{name}: no line exceeds 80 columns",
              all(len(l) <= 80 for l in txt.splitlines()),
              f"widest={max((len(l) for l in txt.splitlines()), default=0)}")

    # ------------------------------------------- known bugs still open ----
    if cb:
        f0 = (cb.get("findings") or [{}])[0]
        known("schema: findings[] lacks 'severity' and 'finding_type' keys",
              "severity" not in f0 or "finding_type" not in f0,
              f"keys: {sorted(f0)[:5]}...")

        rs = cb["risk"].get("severity_counts", {})
        ss = cb["summary"].get("severities", {})
        known("schema: risk.severity_counts contradicts summary.severities",
              rs.get("high", 0) != ss.get("high", 0),
              f"risk={rs.get('high')} vs summary={ss.get('high')}")

    if doctor and "not installed" in doctor:
        # Rich used to parse [server] as a style tag and delete it, so the
        # remediation read `pip install 'scanllm'` -- install what you have.
        check("doctor: pip hint keeps the extras name",
              "scanllm[server]" in doctor,
              "hint lost its [extra]")

    # ----------------------------------------------------------- report ---
    w = sys.stdout.write
    w(f"\n  {len(PASS)} passed   {len(FAIL)} failed   "
      f"{len(DRIFTED)} drifted   {len(XFAIL)} known-bugs   "
      f"{len(XPASS)} newly-fixed\n\n")
    for label, detail in FAIL:
        w(f"  \033[31mFAIL \033[0m {label}" + (f"  ({detail})\n" if detail else "\n"))
    for label, detail in DRIFTED:
        w(f"  \033[33mDRIFT\033[0m {label}  ({detail})\n")
    for label, detail in XFAIL:
        w(f"  \033[90mKNOWN\033[0m {label}" + (f"  ({detail})\n" if detail else "\n"))
    for label, detail in XPASS:
        w(f"  \033[32mFIXED\033[0m {label} -- promote this to a CHECK\n")
    if not FAIL:
        w("\n  \033[32mAll blocking checks passed.\033[0m\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

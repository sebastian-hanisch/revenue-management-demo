"""Fehler-Einbau-Test: baut einzelne Fehler in die Module ein und prueft, ob die Tests (ohne AppTests,
die sind zu langsam fuer 20+ Mutanten) sie finden.

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/mutation_check.py [Teilstring des Dateinamens]
Jeder Mutant ersetzt genau eine Stelle; Ueberlebende sind entweder gleichwertig (kein sichtbarer
Unterschied) oder eine Luecke der Tests. Die Kopie liegt in einem temporaeren Ordner;
PYTHONDONTWRITEBYTECODE=1, damit veralteter Bytecode keine Ueberlebenden vortaeuscht; Quelltexte als
LF (Windows-Python schreibt sonst CRLF und die Zeichenketten unten finden nichts)."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
TIMEOUT = 240

MUTANTS = [
    # rvm_scenario.py
    ("rvm_scenario.py", "frac = n / (n_epochs - 1) if n_epochs > 1 else 0.0", "frac = n / (n_epochs - 1) if n_epochs > 0 else 0.0"),
    ("rvm_scenario.py", "hi = max(0.0, min(hi, 0.9))", "hi = max(0.0, min(hi, 0.99))"),
    ("rvm_scenario.py", "lo = max(0.0, min(lo, 0.9 - hi))", "lo = max(0.0, min(lo, 0.9 - hi + 0.05))"),
    ("rvm_scenario.py", "elif u < hi + lo:", "elif u < hi:"),
    # rvm_solve.py
    ("rvm_solve.py", "v_hi = max(r_hi + V[n + 1][c - 1], v_stay) if c > 0 else v_stay", "v_hi = max(r_hi + V[n + 1][c - 1], v_stay) if c >= 0 else v_stay"),
    ("rvm_solve.py", "v_lo = max(r_lo + V[n + 1][c - 1], v_stay) if c > 0 else v_stay", "v_lo = max(r_lo + V[n + 1][c - 1], v_stay) if c >= 0 else v_stay"),
    ("rvm_solve.py", "accept = c > 0 if cls == \"hi\" else c > levels[n]", "accept = c >= 0 if cls == \"hi\" else c > levels[n]"),
    ("rvm_solve.py", "if tail <= ratio:", "if tail < ratio:"),
    ("rvm_solve.py", "fares.reverse()", "pass"),
    ("rvm_solve.py", "revenue += fare", "revenue += 0"),
    ("rvm_solve.py", "c -= 1", "c -= 0"),
    ("rvm_solve.py", "return fare + V[n + 1][c - 1] >= V[n + 1][c]", "return fare + V[n + 1][c - 1] > V[n + 1][c]"),
    # rvm_evaluation.py
    ("rvm_evaluation.py", "fcfs_gap_pct=gap_pct(means[C.POLICY_FCFS], ref),", "fcfs_gap_pct=gap_pct(ref, means[C.POLICY_FCFS]),"),
    ("rvm_evaluation.py", "d = [x - y for x, y in zip(lit, fcfs)]", "d = [y - x for x, y in zip(lit, fcfs)]"),
    ("rvm_evaluation.py", "kind = \"unclear\" if abs(diff) <= C.VERDICT_Z * se else (\"better\" if diff > 0 else \"worse\")", "kind = \"unclear\" if abs(diff) < C.VERDICT_Z * se else (\"better\" if diff > 0 else \"worse\")"),
    ("rvm_evaluation.py", "return (value / ref - 1) * 100 if ref else 0.0", "return (value / ref - 1) * 100 if ref else 1.0"),
    ("rvm_evaluation.py", "levels = sorted({max(lo, capacity - delta), capacity, min(hi, capacity + delta)})", "levels = sorted({capacity - delta, capacity, capacity + delta})"),
    ("rvm_evaluation.py", "curve_seed = curve_seed_start + i", "curve_seed = curve_seed_start + i + 1"),
    # rvm_presets.py
    ("rvm_presets.py", "value = max(spec.lo, value)", "value = value"),
    ("rvm_presets.py", "if spec.hi is not None:\n        value = min(spec.hi, value)", "if spec.hi is not None:\n        value = value"),
    ("rvm_presets.py", "return min(opts, key=lambda o: abs(o - value))", "return min(opts)"),
    # randomize_seed() selbst braucht AppTest (st.session_state ausserhalb eines Skript-Kontexts) - dort
    # abgedeckt (tests/test_app.py::test_new_sequence_button_actually_randomizes_not_just_stays_in_range),
    # nicht in diesem schnellen, AppTest-losen Lauf.
    # rvm_stories.py
    ("rvm_stories.py", "return [(fg <= -10.0,", "return [(fg <= -9.0,"),
    ("rvm_stories.py", "return [(fg <= -25.0,", "return [(fg <= -24.0,"),
    ("rvm_stories.py", "return [(fg >= -3.0,", "return [(fg >= -4.0,"),
    ("rvm_stories.py", 'return [(fg >= -5.0, f"FCFS-Aufschlag >= -5 %: {_pct(fg)}")]', 'return [(fg >= -6.0, f"FCFS-Aufschlag >= -5 %: {_pct(fg)}")]'),
]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rvm_mut_"))
    for f in ROOT.glob("*.py"):
        shutil.copy(f, tmp / f.name)
    shutil.copytree(ROOT / "tests", tmp / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    for f in tmp.glob("*.py"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    survivors, errors, killed = [], [], 0
    for n, (name, old, new) in enumerate(MUTANTS, 1):
        if only and only not in name:
            continue
        path = tmp / name
        original = path.read_bytes().decode("utf-8")
        if original.count(old) != 1:
            errors.append((n, name, old[:60], original.count(old)))
            continue
        path.write_bytes(original.replace(old, new).encode("utf-8"))
        try:
            r = subprocess.run([PY, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "tests", "--ignore=tests/test_app.py"], cwd=tmp, env=env, capture_output=True, text=True, timeout=TIMEOUT)
            survived = r.returncode == 0
        except subprocess.TimeoutExpired:
            survived = False                    # Endlosschleife gilt als gefunden
            print(f"[{n:3d}] Zeitueberschreitung (als gefunden gezaehlt)  {name}", flush=True)
        path.write_bytes(original.encode("utf-8"))
        if survived:
            survivors.append((n, name, old[:70], new[:70]))
            print(f"[{n:3d}] UEBERLEBT  {name}: {old[:60]!r} -> {new[:60]!r}", flush=True)
        else:
            killed += 1
            print(f"[{n:3d}] gefunden  {name}", flush=True)
    print(f"\n{killed} gefunden, {len(survivors)} ueberlebt, {len(errors)} Fehler in der Mutantenliste")
    for e in errors:
        print("  FEHLER (Stelle nicht eindeutig gefunden):", e)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

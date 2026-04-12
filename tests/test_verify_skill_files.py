import subprocess, sys, pathlib
SK = pathlib.Path(__file__).resolve().parents[1]

def test_verifier_reports_missing_core_files():
    r = subprocess.run([sys.executable, str(SK/"scripts/verify_skill_files.py")],
                       capture_output=True, text=True)
    # Before any SKILL.md exists, verifier must fail with an explicit listing
    assert r.returncode != 0
    assert "SKILL.md" in r.stdout + r.stderr

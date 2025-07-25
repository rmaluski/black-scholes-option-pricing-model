import subprocess
import sys

def test_cli_call_option():
    result = subprocess.run([
        sys.executable, "cli.py",
        "--S", "100",
        "--K", "100",
        "--T", "1",
        "--r", "0.05",
        "--sigma", "0.2",
        "--type", "call"
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Call option price:" in result.stdout
    price = float(result.stdout.strip().split(":")[-1])
    assert 10 < price < 11  # Known value: ~10.45

def test_cli_put_option():
    result = subprocess.run([
        sys.executable, "cli.py",
        "--S", "100",
        "--K", "100",
        "--T", "1",
        "--r", "0.05",
        "--sigma", "0.2",
        "--type", "put"
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Put option price:" in result.stdout
    price = float(result.stdout.strip().split(":")[-1])
    assert 5 < price < 6  # Known value: ~5.57 
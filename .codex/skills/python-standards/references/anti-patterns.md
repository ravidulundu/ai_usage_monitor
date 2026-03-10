    # Anti-Patterns — Python Standards

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Implicit Any payload

    **What it looks like**:
    ```python
    def load_json(path):
    return json.load(open(path))
# -> no types, leaked file handle
    ```

    **Why it's dangerous**: Provider veya VM builder içinde tiplenmemiş dict zinciri kurmak mypy debt ve yanlış alan adlarını gizler.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    from pathlib import Path
from typing import Any

def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)
    ```

    ### 🟠 AP-002: Verification skipped

    **What it looks like**:
    ```python
    def done() -> bool:
        return True
    # no tests, no health gate
    ```

    **Why it's dangerous**: Multi-layer repo’da sessiz regresyon bırakır.

    **What happens in production**: KDE ve GNOME farklı davranmaya başlar, sorun geç fark edilir.

    **Fix**:
    ```python
    commands = ['pytest -q', 'make health-ci PYTHON=python']
    ```

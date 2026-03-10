    # Anti-Patterns — Git Workflow

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Monolithic unverified commit

    **What it looks like**:
    ```python
    git add -A && git commit -m 'fix'
# -> no scope, no verification
    ```

    **Why it's dangerous**: Birden fazla contexti tek doğrulamasız committe toplamak.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    git status --short
git diff -- core/ai_usage_monitor/presentation/popup_vm_source_presentation.py
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_popup_vm.py
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

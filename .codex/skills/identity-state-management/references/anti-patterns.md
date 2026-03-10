    # Anti-Patterns — Identity State Management

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Blind metric reuse across accounts

    **What it looks like**:
    ```python
    provider['sessionTokens'] = previous_provider['sessionTokens']
# blindly reusing prior account data
    ```

    **Why it's dangerous**: Identity doğrulanmadan eski metrics taşımak.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    def should_restore_snapshot(switched: bool, known: bool) -> bool:
    return switched and known
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

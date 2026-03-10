    # Anti-Patterns — Config and Runtime State

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Unbounded runtime knob

    **What it looks like**:
    ```python
    polling_cache_seconds = config.get('pollingCacheSeconds', 999999)
# unbounded and unvalidated
    ```

    **Why it's dangerous**: Clamp edilmemiş cache/polling ayarı.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    def normalized_polling_cache_seconds(value: int | None) -> int:
    if value is None:
        return 10
    return max(0, min(60, value))
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

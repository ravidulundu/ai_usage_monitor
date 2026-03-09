    # Anti-Patterns — Error Handling

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Fake zero metrics on failure

    **What it looks like**:
    ```python
    except Exception:
    return {'sessionTokens': 0, 'weeklyTokens': 0}
# -> hides failure as fake data
    ```

    **Why it's dangerous**: Gerçek hata durumunda sahte sıfır usage dönmek.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    def provider_failure_state(message: str) -> dict[str, object]:
    return {
        'error': message,
        'status': 'unavailable',
        'authenticated': False,
    }
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

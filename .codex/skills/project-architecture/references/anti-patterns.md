    # Anti-Patterns — Project Architecture

    Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

    ## Severity Guide

    - 🔴 CRITICAL: merge bloklanır
    - 🟠 HIGH: merge öncesi düzeltilir
    - 🟡 MEDIUM: aynı sprint içinde düzeltilir
    - 🟢 LOW: dosya tekrar açıldığında düzeltilir

    ### 🔴 AP-001: Renderer-driven contract fork

    **What it looks like**:
    ```python
    # GNOME renderer içinde yeni payload üretmek YASAK
payload = {"providers": [], "activeTab": "codex"}
    ```

    **Why it's dangerous**: KDE veya GNOME tarafında core dışı yeni payload alanları üretmek iki UI arasında sessiz drift yaratır.

    **What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

    **Fix**:
    ```python
    from core.ai_usage_monitor.collector import collect_popup_vm_payload

def build_popup_json(preferred_provider_id: str | None = None) -> dict:
    return collect_popup_vm_payload(preferred_provider_id=preferred_provider_id, force=False)
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

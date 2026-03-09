# Anti-Patterns — Provider Patterns

Bu skill için yasaklı desenler. Hepsi ai_usage_monitor bağlamında tanımlanmıştır.

## Severity Guide

- 🔴 CRITICAL: merge bloklanır
- 🟠 HIGH: merge öncesi düzeltilir
- 🟡 MEDIUM: aynı sprint içinde düzeltilir
- 🟢 LOW: dosya tekrar açıldığında düzeltilir

### 🔴 AP-001: God collector function

**What it looks like**:
```python
def collect_example(settings=None):
# auth, request, parse, retry, mapping, fallback here
...
```

**Why it's dangerous**: Tek fonksiyonda auth+fetch+parse+retry+mapping+fallback biriktirmek.

**What happens in production**: Kullanıcı yanlış usage, yanlış unavailable reason veya bozuk source davranışı görebilir.

**Fix**:
```python
def collect_example(settings: dict[str, object] | None = None) -> tuple[dict[str, object], object]:
creds = _load_credentials(settings)
if creds is None:
    return _not_authenticated()
payload = _fetch_remote(creds)
return _success_state(payload)
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

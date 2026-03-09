# Approved Patterns — Provider Patterns

Complete pattern catalog for ai_usage_monitor. Bu dosya proje dışı generic örnek vermez.

## Core Patterns

### Pattern: Boundary-first change

**Context**: collectors alanında davranış eklerken.
**Problem**: En yakın renderer/helper’da yapılan hızlı yamalar contract drift üretir.

```python
def apply_change_at_boundary(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
```

**Testing this pattern**:
```python
def test_apply_change_at_boundary_trims_empty() -> None:
    assert apply_change_at_boundary('  x  ') == 'x'
```

**Gotchas**:
- Aynı semantiği ikinci kez renderer tarafında kurma.
- Additive contract olmadan alan silme.

**Related rules**: Rule 1, Rule 2

### Pattern: Verification-first closure

**Context**: Skill alanında patch tamamlanırken.
**Problem**: Doğrulamasız kapanan iş sonraki turda tekrar açılır.

```python
def verification_commands() -> list[str]:
    return ['pytest -q', 'make health-ci PYTHON=python']
```

**Testing this pattern**:
```python
def test_verification_commands_contains_health_gate() -> None:
    assert 'make health-ci PYTHON=python' in verification_commands()
```

**Gotchas**:
- Yalnız subset test ile kapanış yapma.
- Review notuna komut yazmadan işi bitmiş sayma.

**Related rules**: Rule 4, Rule 5

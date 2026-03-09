# FinOps Sweep Reduction Round 3

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Popup TTL cache dışında kalan backend full-sweep maliyetini güvenli alt kümelerde azaltmak.

**Architecture:** Provider freshness yalnız kimliği stabil remote provider'larda (`vertexai`, `copilot`, `openrouter`) collector-call seviyesinde uygulanır. `claude` ve `vertexai` local usage fonksiyonları dosya fingerprint cache kullanır. Yeni default config'te pahalı/niş provider'lar yalnız kullanıcı açarsa çalışır.

**Tech Stack:** Python, pytest, JSON state cache, mypy, project health checks

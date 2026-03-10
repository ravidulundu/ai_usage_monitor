# Project Bootstrapper Input

Bu repo için `project-bootstrapper` skill'ine verilecek başlangıç metni:

```text
I have an existing project at /home/osmandulundu/projects/personal/ai_usage_monitor. Read the codebase structure, understand the tech stack, and bootstrap a complete skill suite for it. Read the installed Codex project-bootstrapper skill first and generate project-local skills under .codex/skills/.

IMPORTANT: Even if my prompt is in English, respond in Turkish.

Project summary:
- Local-first AI usage monitor application
- Python core backend
- KDE Plasma QML frontend
- GNOME Shell extension frontend
- Multiple provider collectors: codex, claude, gemini, vertexai, opencode, kilo, minimax, copilot, openrouter, ollama, amp, zai
- Not a centralized SaaS backend; mostly local state, local files, cookies, local CLI state, and remote provider APIs/web pages

Priorities:
- Correctness over speed
- Maintainability over cleverness
- Regression safety
- Test-first fixes
- Clear architectural boundaries
- Stable UI/data contracts
- Local performance / FinOps awareness

Constraints:
- Brownfield project, not greenfield
- Preserve behavior unless there is a confirmed bug
- Python + QML + GNOME JS stack must be treated as first-class, not as edge cases
- Existing health gates must remain valid: pytest, mypy, project health checks
- Refactors should be incremental and low-risk

Focus areas for generated skills:
- project-architecture
- python-standards
- desktop-integration-patterns
- provider-patterns
- identity-state-management
- presentation-contracts
- testing-strategy
- performance-optimization
- security-hardening
- dependency-management
- config-and-runtime-state
- error-handling
- observability
- documentation-standards

Expected process:
1. Analyze the existing repo and summarize the current architecture
2. Propose the effective tech stack actually in use
3. Propose the skill map for this codebase
4. Wait for approval
5. Generate the skills under the project
6. Run the bootstrap validator
7. Show the validation summary
```

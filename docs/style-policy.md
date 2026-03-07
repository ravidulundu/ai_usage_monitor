# Style Policy

This repository uses a lightweight style policy for Python, QML, and GJS so refactors stay consistent as the codebase grows.

## Base Rules

- Use UTF-8, LF line endings, and a final newline.
- Use 4-space indentation.
- Keep lines at or under 120 characters unless a longer literal is clearly better than an awkward wrap.
- Prefer small functions with explicit names over large multi-purpose blocks.
- Keep comments rare and high-signal.
- Preserve external data contracts exactly as they are returned to the UI.

## Python

- Follow PEP 8 with 4 spaces and 120-char lines.
- Use `snake_case` for variables, functions, and module helpers.
- Use `PascalCase` for dataclasses and classes.
- Keep imports explicit; no wildcard imports.
- Prefer standard library modules unless a new dependency is clearly justified.
- Keep JSON payload keys in backend models mapped to the existing UI contract:
  internal names may be `snake_case`, serialized output stays `camelCase`.
- Provider collectors should return predictable tuples:
  `legacy_payload, provider_state`.

## QML

- Keep component structure top-to-bottom:
  properties, helpers, layout, delegates/components.
- Use `camelCase` for properties and helper functions.
- Prefer declarative bindings over imperative mutation.
- Use `Loader` and `Repeater` for optional or repeated UI instead of copy-pasted blocks.
- Keep provider-specific branching minimal; generic rendering is the default path.

## GJS

- Use semicolons consistently.
- Use `camelCase` for methods, locals, and helpers.
- Keep private instance members prefixed with `_`.
- UI update methods should be narrow and composable:
  one method for state selection, one for rendering, one for formatting.
- Prefer explicit guard-style checks over deeply nested conditionals.

## JSON and Config

- Config files stay human-editable.
- Provider-specific fields are preserved during normalization.
- New provider settings should extend the existing provider object instead of creating a parallel config shape.

## Change Policy

- New files should follow this policy by default.
- Existing files should be moved toward this style when touched, but avoid unrelated formatting churn.
- Functional changes come first; style cleanup should not obscure behavioral diffs.

## Current Priority

This is a support document, not the next product milestone.

The next implementation priority remains:
- generic settings/config UI

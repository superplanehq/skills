---
name: superplane-expressions
description: Write and debug SuperPlane expressions using the Expr language. Covers node references with $['Node Name'], root(), previous(), string interpolation inside {{ }}, type coercion, and operators. Use when building expressions in canvas node configuration, debugging "expression error" failures, referencing upstream payloads, or working with Expr syntax.
---

# SuperPlane Expressions

Write expressions for SuperPlane canvas node configuration using the [Expr language](https://expr-lang.org).

## Quick Reference

| Pattern | Description |
| --- | --- |
| `{{ expression }}` | Expression delimiters in YAML config values |
| `$['Node Name'].field` | Access a named node's output payload |
| `root()` | Root trigger event payload |
| `previous()` | Immediate upstream node's payload |
| `previous(n)` | N levels upstream |

## Syntax Basics

Expressions go inside `{{ }}` delimiters in any YAML configuration value:

```yaml
configuration:
  url: "https://api.example.com/repos/{{ $['GitHub Push'].repository.full_name }}"
  body: '{"ref": "{{ root().ref }}", "status": "{{ previous().result }}"}'
```

### Literals

| Type | Example |
| --- | --- |
| String | `"hello"`, `'hello'` |
| Number | `42`, `3.14` |
| Bool | `true`, `false` |
| Nil | `nil` |
| Array | `[1, 2, 3]` |
| Map | `{"key": "value"}` |

### Operators

| Category | Operators |
| --- | --- |
| Arithmetic | `+`, `-`, `*`, `/`, `%`, `**` |
| Comparison | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| Logical | `and`, `or`, `not` |
| String concat | `+` (when both sides are strings) |
| Ternary | `condition ? trueVal : falseVal` |
| Nil coalesce | `value ?? fallback` |
| Membership | `"x" in ["x","y"]`, `"key" in {"key": 1}` |

### Property Access

```
payload.repository.full_name       # dot notation
payload["repository"]["full_name"] # bracket notation
payload.tags[0]                    # array index
```

Dot and bracket notation are interchangeable for map keys. Use brackets when keys contain spaces or special characters.

### String Interpolation

Inside an expression, use string concatenation:

```
"Deploy " + $['CI'].project + " to production"
```

The outer `{{ }}` delimiters handle embedding the expression result into the YAML string value.

## Node References

### `$['Node Name']` — Named Node Output

Access any upstream node's output payload by its display name:

```
$['github.onPush'].ref                    # trigger payload field
$['semaphore.runWorkflow'].result         # component output field
$['Health Check'].body.status             # nested field
```

Rules:
- **Case-sensitive**: `$['GitHub Push']` is not `$['github push']`
- **Must match the node's `name` field exactly** as shown in the canvas YAML
- **Only upstream nodes are accessible** — you cannot reference nodes that haven't executed yet
- **Bracket notation required**: always use `$['...']`, not `$.NodeName`

### `root()` — Trigger Payload

Returns the payload of the root trigger event that started the execution:

```
root().ref                          # git ref from a push event
root().pull_request.number          # PR number
root().commits[0].message           # first commit message
```

Use `root()` when you need the original event data regardless of how deep in the graph you are.

### `previous()` — Upstream Payload

Returns the output of the immediately preceding node:

```
previous().result                   # direct upstream output
previous().statusCode               # HTTP response code
previous(2).ref                     # two nodes upstream
```

`previous()` is shorthand for `previous(1)`. Use `previous(n)` to go further back. Prefer `$['Node Name']` for clarity when the graph has branches.

## Type System

Expr is dynamically typed. Values flow as JSON-compatible types:

| Type | Examples | Notes |
| --- | --- | --- |
| string | `"hello"` | Most config fields expect strings |
| int | `42` | Integer arithmetic |
| float | `3.14` | Floating-point |
| bool | `true`, `false` | Used in Filter/If expressions |
| array | `[1, 2, 3]` | Indexable, iterable |
| map | `{"k": "v"}` | Key-value, dot/bracket access |
| nil | `nil` | Missing or null values |

### Automatic Coercion

- Numbers in string context become strings: `"count: " + 42` → `"count: 42"`
- String-to-number: use `int("42")` or `float("3.14")`
- Nil access does not error — it propagates nil

### Nil Handling

Accessing a missing field returns `nil`. Chain nil-safe access with `??`:

```
$['Node'].maybe_missing ?? "default value"
$['Node'].data.nested?.field          # not supported — use ?? instead
```

To check for nil explicitly:

```
$['Node'].field != nil ? $['Node'].field : "fallback"
```

## Common Mistakes

### Wrong node name casing

```
# WRONG — name doesn't match
$['Github Push'].ref

# RIGHT — exact match
$['github.onPush'].ref
```

Fix: run `superplane canvases get <name>` and check the exact `name` field on each node.

### Referencing a node that hasn't executed

Expressions can only access nodes that are upstream in the graph. If node B is parallel to node A (not connected by edges), A cannot reference B.

Fix: add a Merge node to collect both branches before referencing.

### Missing brackets around node name

```
# WRONG
$.github.onPush.ref

# RIGHT
$['github.onPush'].ref
```

### Forgetting expression delimiters

```yaml
# WRONG — literal string, not evaluated
url: $['Node'].url

# RIGHT — evaluated as expression
url: "{{ $['Node'].url }}"
```

### Type mismatch in Filter/If

Filter and If expressions must return a boolean:

```
# WRONG — returns a string
$['Node'].status

# RIGHT — returns a boolean
$['Node'].status == "success"
```

### Nil from missing nested field

```
# Fails if 'data' is nil
$['Node'].data.items[0]

# Safer — check first
$['Node'].data != nil ? $['Node'].data.items[0] : "none"
```

## Debugging Expressions

1. **Check the execution output**: `superplane events list-executions --canvas-id <id> --event-id <eid>` — look for nodes with `Failed` status and expression-related error messages.

2. **Verify node names**: `superplane canvases get <name>` — confirm the exact `name` field matches your `$['...']` reference.

3. **Inspect upstream payloads**: check what the upstream node actually emitted. The execution detail shows input/output payloads.

4. **Simplify the expression**: replace a complex expression with a simple `root().field` or `"test"` to isolate whether the issue is in the expression syntax or the data.

5. **Check the channel**: if a node received data via a `passed`/`failed`/`approved` channel, the payload structure may differ from `default`.

## References

- [Expr Functions Reference](references/expr-functions.md) — Built-in functions and operators

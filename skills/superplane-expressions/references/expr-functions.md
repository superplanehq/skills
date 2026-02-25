# Expr Functions Reference

Built-in functions and operators available in SuperPlane expressions. Based on the [Expr language](https://expr-lang.org/docs/language-definition).

## String Functions

| Function | Description | Example |
| --- | --- | --- |
| `trim(s)` | Remove leading/trailing whitespace | `trim("  hi  ")` → `"hi"` |
| `trimPrefix(s, prefix)` | Remove prefix | `trimPrefix("hello", "he")` → `"llo"` |
| `trimSuffix(s, suffix)` | Remove suffix | `trimSuffix("hello", "lo")` → `"hel"` |
| `upper(s)` | Uppercase | `upper("hi")` → `"HI"` |
| `lower(s)` | Lowercase | `lower("HI")` → `"hi"` |
| `split(s, sep)` | Split into array | `split("a,b,c", ",")` → `["a","b","c"]` |
| `join(arr, sep)` | Join array into string | `join(["a","b"], ",")` → `"a,b"` |
| `replace(s, old, new)` | Replace all occurrences | `replace("foo", "o", "0")` → `"f00"` |
| `hasPrefix(s, prefix)` | Starts with | `hasPrefix("hello", "he")` → `true` |
| `hasSuffix(s, suffix)` | Ends with | `hasSuffix("hello", "lo")` → `true` |
| `contains(s, substr)` | Contains substring | `contains("hello", "ell")` → `true` |
| `repeat(s, n)` | Repeat string n times | `repeat("ab", 3)` → `"ababab"` |
| `indexOf(s, substr)` | First index of substr (-1 if not found) | `indexOf("hello", "ll")` → `2` |

## Numeric Functions

| Function | Description | Example |
| --- | --- | --- |
| `abs(n)` | Absolute value | `abs(-5)` → `5` |
| `ceil(n)` | Round up | `ceil(3.2)` → `4` |
| `floor(n)` | Round down | `floor(3.8)` → `3` |
| `round(n)` | Round to nearest | `round(3.5)` → `4` |
| `min(a, b, ...)` | Minimum value | `min(3, 1, 2)` → `1` |
| `max(a, b, ...)` | Maximum value | `max(3, 1, 2)` → `3` |

## Array Functions

| Function | Description | Example |
| --- | --- | --- |
| `len(arr)` | Length | `len([1,2,3])` → `3` |
| `first(arr)` | First element | `first([1,2,3])` → `1` |
| `last(arr)` | Last element | `last([1,2,3])` → `3` |
| `flatten(arr)` | Flatten nested arrays | `flatten([[1,2],[3]])` → `[1,2,3]` |
| `sort(arr)` | Sort ascending | `sort([3,1,2])` → `[1,2,3]` |
| `reverse(arr)` | Reverse order | `reverse([1,2,3])` → `[3,2,1]` |
| `unique(arr)` | Remove duplicates | `unique([1,1,2])` → `[1,2]` |
| `filter(arr, predicate)` | Keep matching elements | `filter([1,2,3], {# > 1})` → `[2,3]` |
| `map(arr, transform)` | Transform elements | `map([1,2,3], {# * 2})` → `[2,4,6]` |
| `count(arr, predicate)` | Count matching | `count([1,2,3], {# > 1})` → `2` |
| `all(arr, predicate)` | All match | `all([2,3,4], {# > 1})` → `true` |
| `any(arr, predicate)` | Any match | `any([1,2,3], {# > 2})` → `true` |
| `none(arr, predicate)` | None match | `none([1,2,3], {# > 5})` → `true` |
| `one(arr, predicate)` | Exactly one matches | `one([1,2,3], {# > 2})` → `true` |

### Closure Syntax

Array functions that take predicates use `{# > 1}` syntax where `#` is the current element:

```
filter($['Node'].items, {#.status == "active"})
map($['Node'].tags, {upper(#)})
```

## Map Functions

| Function | Description | Example |
| --- | --- | --- |
| `keys(map)` | Get all keys | `keys({"a":1,"b":2})` → `["a","b"]` |
| `values(map)` | Get all values | `values({"a":1,"b":2})` → `[1,2]` |
| `len(map)` | Number of entries | `len({"a":1,"b":2})` → `2` |

## Type Functions

| Function | Description | Example |
| --- | --- | --- |
| `int(v)` | Convert to integer | `int("42")` → `42` |
| `float(v)` | Convert to float | `float("3.14")` → `3.14` |
| `string(v)` | Convert to string | `string(42)` → `"42"` |
| `type(v)` | Get type name | `type(42)` → `"int"` |

## Date/Time Functions

| Function | Description | Example |
| --- | --- | --- |
| `now()` | Current time | `now()` |
| `date(s)` | Parse date string | `date("2026-01-15T10:00:00Z")` |
| `duration(s)` | Parse duration | `duration("1h30m")` |

## Comparison Operators

| Operator | Description | Example |
| --- | --- | --- |
| `==` | Equal | `status == "success"` |
| `!=` | Not equal | `status != "failed"` |
| `<`, `>` | Less/greater than | `count > 0` |
| `<=`, `>=` | Less/greater or equal | `score >= 80` |
| `in` | Membership | `"admin" in roles` |
| `not in` | Non-membership | `"guest" not in roles` |
| `matches` | Regex match | `name matches "^v[0-9]+"` |
| `contains` | String/array contains | `tags contains "urgent"` |
| `startsWith` | String prefix | `ref startsWith "refs/tags/"` |
| `endsWith` | String suffix | `file endsWith ".go"` |

## Logical Operators

| Operator | Description | Example |
| --- | --- | --- |
| `and` | Logical AND | `a > 0 and b > 0` |
| `or` | Logical OR | `status == "success" or status == "skipped"` |
| `not` | Logical NOT | `not (status == "failed")` |
| `? :` | Ternary | `count > 0 ? "yes" : "no"` |
| `??` | Nil coalesce | `value ?? "default"` |

## Arithmetic Operators

| Operator | Description | Example |
| --- | --- | --- |
| `+` | Add / concat | `a + b`, `"hello " + name` |
| `-` | Subtract | `total - discount` |
| `*` | Multiply | `price * quantity` |
| `/` | Divide | `total / count` |
| `%` | Modulo | `index % 2` |
| `**` | Exponent | `2 ** 10` |

## Pipe Operator

Chain function calls with `|`:

```
$['Node'].items | filter({#.active}) | len
$['Node'].name | lower | trim
```

Equivalent to `len(filter($['Node'].items, {#.active}))` but more readable.

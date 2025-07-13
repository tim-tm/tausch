# tausch

Small language that is meant to be used in an
[envsubst](https://man7.org/linux/man-pages/man1/envsubst.1.html) environment.

Let's assume the following variables are set:
```json
{
    "hello": 42,
    "world": 69,
    "cond": true,
    "ncond": false
}
```

You can simply substitute one of the variables:
```txt
hello

> Result: 42
```

Or use basic if-statements:
```txt
if cond; hello

> Result: 42
```

```txt
if ncond; hello

> Result:
```

```txt
if cond; hello : world

> Result: 42
```

```txt
if ncond; hello : world

> Result: 69
```

As of right now, you can **only** use boolean-variables as the condition
to if-statements. The following example will **not** work:
```txt
if hello; hello : world

> Variable 'hello' must be boolean
```

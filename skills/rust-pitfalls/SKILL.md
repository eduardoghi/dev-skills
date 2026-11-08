---
name: rust-pitfalls
description: Mistakes in Rust that compile, pass clippy and the usual tests, and fail on an edge or at exit. Use when writing or reviewing Rust.
paths:
  - "**/*.rs"
---

# Rust pitfalls

## `then_some` works out its value first

`condition.then_some(value)` reads like the value is only made when the condition holds, but the
argument is evaluated before the call, every time. With an index at its largest value,

```rust
(index < MAX).then_some(index + 1)
```

overflows and panics in a debug build even though the check fails, and wraps around in release.
Use `then`, whose closure only runs when the condition holds:

```rust
(index < MAX).then(|| index + 1)
```

A test with the edge value, such as `u32::MAX`, catches it.

## Threads still using a driver when the process ends

Returning from `main` calls `exit`, which runs the cleanup that C libraries registered, the
graphics driver's among them. A thread that is still tearing down something on that driver, such
as a GStreamer pipeline with a hardware decoder, races that cleanup, and the process aborts with a
double free on the way out. Dropping a handle that only tells the thread to stop isn't enough.
Count the threads, wait for them with a deadline after the work that stops them, and if one is
still running past it, end with `_exit` from the C runtime, which skips the cleanup:

```rust
extern "C" {
    fn _exit(code: i32) -> !;
}
```

Save anything that has to persist before that point, since `_exit` runs no destructors.

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

## Byte offsets that land inside a character

A `&str` index counts bytes, and slicing at an offset that isn't a character boundary panics. An
offset worked out by arithmetic (one past a keyword, a fixed column, a length taken from another
string) is right for ASCII and wrong as soon as an accented letter sits there. Every test written
with ASCII text passes.

```rust
let rest = &sql[from + 5..];        // panics on "FROMé"
```

Take the slice with `get`, which returns `None` off a boundary, or move the offset to a boundary
first:

```rust
let rest = sql.get(from + 5..)?;

let mut end = offset;
while !text.is_char_boundary(end) {
    end += 1;
}
```

After a search with a `char` predicate, step past the match with `c.len_utf8()` and not with `+ 1`.

An offset that is stored, such as the range of a diagnostic, panics later, in the code that converts
it to a line and column, so the backtrace doesn't point at the arithmetic that produced it.

A test with accented text cut at every character position catches it. Build the input from each
prefix and suffix of one string and check `text.get(range).is_some()` for every range that comes
out.

## `panic = "abort"` turns `catch_unwind` into nothing

`catch_unwind` only catches a panic that unwinds. With `panic = "abort"` in the profile the same
code compiles without a warning and the process dies at the first panic. The setting usually
arrives later, to shrink the binary, in a `Cargo.toml` far from the `catch_unwind` call, and a
server that isolates each request this way goes back to dying on one bad request.

A test doesn't catch it, because Cargo ignores the `panic` setting when it builds tests, and
`cargo test --release` passes with the abort in place. Make the build fail instead:

```rust
#[cfg(panic = "abort")]
compile_error!("the request loop relies on catch_unwind, build with panic = \"unwind\"");
```

## Freeing on a thread that didn't allocate

A value built on one thread and dropped on another is freed far from where it was allocated. With
glibc's allocator, freeing thousands of small blocks this way is much slower than freeing them on
the thread that made them. A `serde_json::Value` tree of a few thousand nodes, built by the main
thread and sent through a channel to a writer thread that serialized and dropped it, cost 4.4 ms
per response. The same program with mimalloc took 1.0 ms.

The profile shows the time under `drop_in_place` and `free` on the receiving thread, which reads as
if the type were expensive to drop. Swapping the allocator for one run tells the two apart.

Send across the thread what is cheap to free. Serializing on the thread that built the tree and
sending the bytes, one allocation, removed the cost without changing the allocator.

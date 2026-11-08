---
name: cpp-pitfalls
description: Mistakes in C++ that compile and pass review, and freeze or crash only on an error path or at exit. Use when writing or reviewing C++.
paths:
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.h"
  - "**/*.hpp"
---

# C++ pitfalls

## An early return after taking a lock

A function takes a lock that other threads share, such as the device lock of a Direct3D 11 or
GStreamer decoder, and a check further down returns early before the matching unlock. The lock
stays held for good, and every thread waiting on it stops, which looks like frozen video rather
than an error. It happens most when an early return is added later to a function that had one
exit.

Do the checks that can leave before taking the lock, or hold it through an RAII guard that
releases it on every return:

```cpp
std::lock_guard lock(mutex);
```

When the lock comes from a C API with separate lock and unlock calls, a small guard struct with
the unlock in its destructor does the same.

## Threads still using a driver when the process ends

`exit`, including the return from `main`, runs the cleanup that libraries registered, the
graphics driver's among them. A worker thread that is still releasing something on that driver
races the cleanup, and the process aborts with a double free on the way out. Telling the threads
to stop isn't enough. Wait for them with a deadline before returning, and past the deadline end
with `_exit`, which skips the cleanup, after anything that has to persist was saved.

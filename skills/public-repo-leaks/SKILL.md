---
name: public-repo-leaks
description: Find names from private or customer material in everything a push would publish, the whole history and not only the current files. Use before the first push of a public repository, before making a private one public, and before pushing local commits of a public project that was built or tested against private data.
---

# Public repository leaks

## Finding what would leak

Search everything a push publishes, not only the files as they are now. A name removed from
the code last week is still in the history, and a commit message or an annotated tag can carry
it too.

```sh
{ git log -p --branches --tags | grep '^+'        # every line ever added
  git log --branches --tags --format=%B           # commit messages
  git for-each-ref refs/tags --format='%(contents)'   # annotated tag messages
} > published.txt
```

Use two lists of terms:

- What you know is sensitive: the company and product names, colleagues, hostnames, internal
  domains, IP ranges, home directory paths, email addresses, token prefixes such as `eyJ`.
- What you don't remember: names taken from the private material the code was written against.
  Folder names of an export, identifiers with the prefix the vendor reserves for customer
  customizations, names of the customer's forms, reports and services. A repository built and
  tested against a private corpus picks up its names in examples, tests and comments, and nobody
  keeps a list of them. One such scan found a real service name in a doc comment and a customer
  form name in a test, neither of which was on the hand-made list.

Count matches per term and read the counts, instead of printing the first matching lines:

```python
import re, sys
text = open("published.txt", encoding="utf-8", errors="ignore").read().upper()
for term in open("terms.txt", encoding="utf-8").read().split("\n"):
    if term:
        n = len(re.findall(r"(?<![A-Z0-9_])" + re.escape(term.upper()) + r"(?![A-Z0-9_])", text))
        if n:
            print(term, n)
```

A combined `grep -E 'a|b|c' | head` hides hits. One loose pattern (an escaped backslash matched
every regex in a grammar file) filled the first lines, and the company name sat further down,
past the cut, until after the push.

The extracted list matches common words and the vendor's own standard names (base tables,
sample report names). Review those by hand once and keep them in an allowlist, so the next run
prints only what is new.

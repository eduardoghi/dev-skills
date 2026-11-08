"""Tests for bin/stale-paths. Run with `python3 -m unittest discover -s tests`."""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

TOOL = os.path.join(os.path.dirname(__file__), "..", "bin", "stale-paths")
loader = importlib.machinery.SourceFileLoader("stale_paths", TOOL)
spec = importlib.util.spec_from_loader("stale_paths", loader)
tool = importlib.util.module_from_spec(spec)
loader.exec_module(tool)


class StalePaths(unittest.TestCase):
    def setUp(self):
        # A repository with a nested source root, the shape where a short path has to be found by
        # its ending. The `.git` is an empty folder, so the index comes from walking the tree.
        self.root = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.root, ".git"))
        for relative in [
            "app/src/services/cleanup.rs",
            "app/src/main.rs",
            "web/src/hooks/use-thing.ts",
            "docs/guide.md",
        ]:
            path = os.path.join(self.root, *relative.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                file.write("")
        tool._INDEXES.clear()

    def write(self, relative, text):
        path = os.path.join(self.root, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(textwrap.dedent(text))
        return path

    def missing(self, path):
        return [finding.split(": ", 1)[1] for finding in tool.check(path)]

    def test_a_moved_file_named_in_a_comment_is_found_with_its_line(self):
        path = self.write("app/src/lib.rs", """\
            fn main() {}

            // The cleanup lives in `services/purge.rs` now.
            """)
        findings = tool.check(path)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0].endswith(":3: `services/purge.rs` does not exist"))

    def test_a_path_given_from_a_nested_source_root_counts_as_there(self):
        path = self.write("web/src/app.ts", """\
            // Mirrors services/cleanup.rs, see also web/src/hooks/use-thing.ts and docs/.
            export const x = 1;
            """)
        self.assertEqual(self.missing(path), [])

    def test_only_comments_are_read_in_source(self):
        path = self.write("app/src/lib.rs", """\
            const PATH: &str = "services/purge.rs";
            """)
        self.assertEqual(self.missing(path), [])

    def test_markdown_is_read_whole_except_its_fenced_blocks(self):
        path = self.write("docs/notes.md", """\
            See `docs/old-guide.md` for the details.

            ```sh
            cat docs/never-there.md
            ```
            """)
        self.assertEqual(self.missing(path), ["`docs/old-guide.md` does not exist"])

    def test_words_that_are_not_paths_of_this_repository_are_left_alone(self):
        path = self.write("docs/notes.md", """\
            An example such as examples/demo.rs, a list such as guide.md/notes.md, a link to
            https://example.com/docs/missing.md, a revision v1.0.0:docs/old.md, a pattern
            docs/*.md, a version 1.2/3.4 and an absolute /etc/hosts.txt.
            """)
        self.assertEqual(self.missing(path), [])

    def test_a_folder_named_with_a_trailing_slash_is_checked_as_a_folder(self):
        path = self.write("docs/notes.md", """\
            The hooks are in web/src/hooks/ and the old ones were in web/src/legacy/.
            """)
        self.assertEqual(self.missing(path), [])
        path = self.write("docs/more.md", "Under app/src/services/ and docs/drafts/.\n")
        self.assertEqual(self.missing(path), [])

    def test_a_removed_file_named_on_purpose_is_skipped_on_a_marked_line(self):
        path = self.write("docs/notes.md", """\
            What hid them was `docs/index.md`, since removed. <!-- stale-paths: ignore -->
            """)
        self.assertEqual(self.missing(path), [])

    def test_a_file_outside_a_repository_is_not_checked(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "notes.md")
        with open(path, "w", encoding="utf-8") as file:
            file.write("See docs/missing.md.\n")
        self.assertEqual(tool.check(path), [])

    def test_the_script_exits_with_one_on_a_finding_and_zero_otherwise(self):
        stale = self.write("docs/a.md", "See `docs/gone.md`.\n")
        fine = self.write("docs/b.md", "See `docs/guide.md`.\n")
        found = subprocess.run([sys.executable, TOOL, stale], capture_output=True, text=True)
        clean = subprocess.run([sys.executable, TOOL, fine], capture_output=True, text=True)
        self.assertEqual(found.returncode, 1)
        self.assertIn("docs/gone.md", found.stdout)
        self.assertEqual(clean.returncode, 0)


if __name__ == "__main__":
    unittest.main()

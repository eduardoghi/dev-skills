"""Tests for bin/workflow-secrets. Run with `python3 -m unittest discover -s tests`."""
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

TOOL = os.path.join(os.path.dirname(__file__), "..", "bin", "workflow-secrets")
loader = importlib.machinery.SourceFileLoader("workflow_secrets", TOOL)
spec = importlib.util.spec_from_loader("workflow_secrets", loader)
tool = importlib.util.module_from_spec(spec)
loader.exec_module(tool)


class WorkflowSecrets(unittest.TestCase):
    def check(self, workflow):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as file:
            file.write(textwrap.dedent(workflow))
        self.addCleanup(os.remove, file.name)
        return [finding.split(": ", 1)[1] for finding in tool.check(file.name)], file.name

    def test_an_install_in_the_step_that_signs_is_found(self):
        findings, path = self.check("""\
            jobs:
              draft:
                runs-on: ubuntu-latest
                steps:
                  - name: sign
                    env:
                      SIGNING_KEY: ${{ secrets.SIGNING_KEY }}
                    run: |
                      test -n "$SIGNING_KEY"
                      sudo apt-get install --yes minisign
                      minisign -S -s key -m app.exe
            """)
        self.assertEqual(
            findings,
            ["'sign' runs `sudo apt-get install --yes minisign` with SIGNING_KEY in its environment"],
        )
        line = tool.check(path)[0].split(":")[1]
        self.assertEqual(line, "10")

    def test_the_install_in_a_step_of_its_own_is_left_alone(self):
        findings, _ = self.check("""\
            jobs:
              draft:
                runs-on: ubuntu-latest
                steps:
                  - run: sudo apt-get install --yes minisign
                  - env:
                      SIGNING_KEY: ${{ secrets.SIGNING_KEY }}
                    run: minisign -S -s key -m app.exe
            """)
        self.assertEqual(findings, [])

    def test_a_secret_of_the_job_or_the_workflow_reaches_every_step(self):
        findings, _ = self.check("""\
            env:
              TOKEN: ${{ secrets.DEPLOY_TOKEN }}
            jobs:
              build:
                runs-on: ubuntu-latest
                env:
                  KEY: ${{ secrets.NPM_KEY }}
                steps:
                  - run: npm ci
                  - run: curl -fsSL https://example.com/install.sh | sh
            """)
        self.assertEqual(len(findings), 2)
        self.assertIn("DEPLOY_TOKEN, NPM_KEY", findings[0])
        self.assertIn("`curl -fsSL https://example.com/install.sh | sh`", findings[1])

    def test_the_github_token_and_commands_that_only_look_alike_are_left_alone(self):
        findings, _ = self.check("""\
            jobs:
              check:
                runs-on: ubuntu-latest
                steps:
                  - env:
                      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
                    run: sudo apt-get install --yes jq
                  - env:
                      KEY: ${{ secrets.KEY }}
                    run: |
                      curl -fsSL https://example.com/sums.txt -o sums.txt
                      cargo test
                      pipx --version
            """)
        self.assertEqual(findings, [])

    def test_the_exit_code_tells_what_was_found(self):
        _, clean = self.check("jobs: {}\n")
        _, flagged = self.check("""\
            jobs:
              a:
                runs-on: ubuntu-latest
                steps:
                  - env: {K: "${{ secrets.K }}"}
                    run: cargo install cargo-deny
            """)
        def run(*paths):
            return subprocess.run([sys.executable, TOOL, *paths], capture_output=True)

        self.assertEqual(run(clean).returncode, 0)
        self.assertEqual(run(flagged).returncode, 1)
        self.assertEqual(run("/nonexistent.yml").returncode, 2)


if __name__ == "__main__":
    unittest.main()

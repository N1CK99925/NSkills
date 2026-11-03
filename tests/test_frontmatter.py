"""Frontmatter parser tests."""

from __future__ import annotations

import unittest

from helpers import REPO_ROOT  # noqa: F401  (sets sys.path)

from nskills import frontmatter
from nskills.frontmatter import FrontmatterError


class SplitTests(unittest.TestCase):
    def test_simple_mapping(self):
        meta, body, start = frontmatter.split("---\nname: x\n---\nbody\n")
        self.assertEqual(meta, {"name": "x"})
        self.assertEqual(body, "body")
        self.assertEqual(start, 4)

    def test_missing_delimiters(self):
        with self.assertRaises(FrontmatterError):
            frontmatter.split("name: x\n")
        with self.assertRaises(FrontmatterError):
            frontmatter.split("---\nname: x\n")

    def test_duplicate_key_rejected(self):
        with self.assertRaises(FrontmatterError):
            frontmatter.split("---\nname: x\nname: y\n---\n")

    def test_unexpected_indentation(self):
        with self.assertRaises(FrontmatterError):
            frontmatter.split("---\nname: x\n  nested: y\n---\n")


class ScalarTests(unittest.TestCase):
    def test_scalars(self):
        meta, _ = frontmatter.parse(
            "---\n"
            "plain: hello world\n"
            "quoted: \"hello: world\"\n"
            "single: 'it''s'\n"
            "yes: true\n"
            "no: false\n"
            "nothing: null\n"
            "count: 3\n"
            "ratio: 0.5\n"
            "---\n"
        )
        self.assertEqual(meta["plain"], "hello world")
        self.assertEqual(meta["quoted"], "hello: world")
        self.assertEqual(meta["single"], "it's")
        self.assertIs(meta["yes"], True)
        self.assertIs(meta["no"], False)
        self.assertIsNone(meta["nothing"])
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["ratio"], 0.5)

    def test_inline_list(self):
        meta, _ = frontmatter.parse("---\ntags: [a, b, \"c d\"]\n---\n")
        self.assertEqual(meta["tags"], ["a", "b", "c d"])

    def test_block_list(self):
        meta, _ = frontmatter.parse("---\nskills:\n  - one\n  - two\n---\n")
        self.assertEqual(meta["skills"], ["one", "two"])

    def test_nested_mapping(self):
        meta, _ = frontmatter.parse(
            "---\n"
            "metadata:\n"
            "  nskills:\n"
            "    tags: [x]\n"
            "    provenance: original\n"
            "---\n"
        )
        self.assertEqual(meta["metadata"]["nskills"]["tags"], ["x"])
        self.assertEqual(meta["metadata"]["nskills"]["provenance"], "original")

    def test_empty_list(self):
        meta, _ = frontmatter.parse("---\nskills: []\n---\n")
        self.assertEqual(meta["skills"], [])

    def test_block_scalar(self):
        meta, _ = frontmatter.parse("---\ntext: |\n  line one\n  line two\n---\n")
        self.assertEqual(meta["text"], "line one\nline two")

    def test_comment_is_stripped(self):
        meta, _ = frontmatter.parse("---\nname: x  # trailing\n---\n")
        self.assertEqual(meta["name"], "x")


if __name__ == "__main__":
    unittest.main()

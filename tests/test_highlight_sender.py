import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _calibre_stub
_calibre_stub.install()

from calibre_plugins.highlights_to_obsidian.highlight_sender import (
    format_data, format_single, make_highlight_format_dict, make_book_format_dict,
    all_format_keys, BookData, BookList, HighlightSender, SafeDict)


def make_highlight(uuid="u1", timestamp="2022-09-10T20:32:08.820Z", text="hello",
                   notes=None, book_id=1, spine_index=0, start_cfi="/4/2/2:0"):
    annot = {
        "type": "highlight",
        "timestamp": timestamp,
        "highlighted_text": text,
        "uuid": uuid,
        "spine_index": spine_index,
        "start_cfi": start_cfi,
    }
    if notes is not None:
        annot["notes"] = notes
    return {"book_id": book_id, "format": "EPUB", "annotation": annot}


class TestFormatDataNoNotesFallback(unittest.TestCase):
    """covers the no-notes fallback bug fix (item ③)."""

    def dat(self, notes):
        return SafeDict(title="T", notes=notes, highlight="hl")

    def test_has_notes_uses_body(self):
        out = format_data(self.dat("n"), "{title}", "BODY:{highlight}", "NONOTES:{highlight}")
        self.assertEqual(out[1], "BODY:hl")

    def test_no_notes_uses_no_notes_body(self):
        out = format_data(self.dat(""), "{title}", "BODY:{highlight}", "NONOTES:{highlight}")
        self.assertEqual(out[1], "NONOTES:hl")

    def test_no_notes_empty_template_falls_back_to_body(self):
        out = format_data(self.dat(""), "{title}", "BODY:{highlight}", "")
        self.assertEqual(out[1], "BODY:hl")

    def test_has_notes_but_empty_no_notes_template_still_uses_body(self):
        # the old code returned "" here -- this is the regression the fix prevents
        out = format_data(self.dat("n"), "{title}", "BODY:{highlight}", "")
        self.assertEqual(out[1], "BODY:hl")

    def test_title_slashes_and_illegal_chars_removed(self):
        out = format_data(SafeDict(title="A/B:C", notes="", highlight=""), "{title}", "b", "b")
        # "/" -> "-" (folder-safe), then ":" stripped as an illegal title char
        self.assertEqual(out[0], "A-BC")


class TestChapterTitle(unittest.TestCase):
    def dict_for(self, toc):
        annot = {"highlighted_text": "x", "uuid": "u", "spine_index": 0, "start_cfi": "/2/2:0"}
        if toc is not None:
            annot["toc_family_titles"] = toc
        return make_highlight_format_dict({"book_id": 1, "format": "EPUB", "annotation": annot}, "My Lib")

    def test_uses_deepest_section(self):
        d = self.dict_for(["Part I", "Chapter 1", "Section A"])
        self.assertEqual(d["chaptertitle"], "Section A")

    def test_single_level_toc(self):
        self.assertEqual(self.dict_for(["Chapter 1"])["chaptertitle"], "Chapter 1")

    def test_empty_when_missing_or_empty(self):
        self.assertEqual(self.dict_for(None)["chaptertitle"], "")
        self.assertEqual(self.dict_for([])["chaptertitle"], "")

    def test_slashes_replaced(self):
        self.assertEqual(self.dict_for(["Part", "1/2 Intro"])["chaptertitle"], "1-2 Intro")


class TestHighlightFormatAndColor(unittest.TestCase):
    def dict_for(self, style=None, fmt="EPUB"):
        annot = {"highlighted_text": "x", "uuid": "u", "spine_index": 0, "start_cfi": "/2/2:0"}
        if style is not None:
            annot["style"] = style
        return make_highlight_format_dict({"book_id": 1, "format": fmt, "annotation": annot}, "Lib")

    def test_color(self):
        d = self.dict_for({"kind": "color", "type": "builtin", "which": "yellow"})
        self.assertEqual(d["color"], "yellow")

    def test_format(self):
        self.assertEqual(self.dict_for(fmt="PDF")["format"], "PDF")

    def test_color_empty_when_no_style(self):
        self.assertEqual(self.dict_for(None)["color"], "")


class TestColorLabel(unittest.TestCase):
    def label_for(self, which, labels=None):
        annot = {"highlighted_text": "x", "uuid": "u", "spine_index": 0, "start_cfi": "/2/2:0",
                 "style": {"kind": "color", "which": which}}
        d = make_highlight_format_dict({"book_id": 1, "format": "EPUB", "annotation": annot}, "Lib", labels)
        return d["colorlabel"]

    def test_mapped_label(self):
        self.assertEqual(self.label_for("yellow", {"yellow": "Important"}), "Important")

    def test_falls_back_to_color_when_unmapped(self):
        self.assertEqual(self.label_for("green", {"yellow": "Important"}), "green")

    def test_no_labels_uses_color(self):
        self.assertEqual(self.label_for("blue"), "blue")

    def test_case_insensitive(self):
        self.assertEqual(self.label_for("Yellow", {"yellow": "Important"}), "Important")


class TestColorFilter(unittest.TestCase):
    def annotation(self, color):
        annot = {"type": "highlight"}
        if color is not None:
            annot["style"] = {"kind": "color", "which": color}
        return {"annotation": annot}

    def sender(self, colors):
        s = HighlightSender()
        s.set_color_filter(colors)
        return s

    def test_no_filter_allows_all(self):
        s = self.sender([])
        self.assertTrue(s.is_valid_highlight(self.annotation("blue"), lambda x: True))
        self.assertTrue(s.is_valid_highlight(self.annotation(None), lambda x: True))

    def test_filter_includes_listed_color(self):
        self.assertTrue(self.sender(["yellow"]).is_valid_highlight(self.annotation("yellow"), lambda x: True))

    def test_filter_excludes_unlisted_and_colorless(self):
        s = self.sender(["yellow"])
        self.assertFalse(s.is_valid_highlight(self.annotation("blue"), lambda x: True))
        self.assertFalse(s.is_valid_highlight(self.annotation(None), lambda x: True))


class TestBookMetadata(unittest.TestCase):
    def make(self, **meta):
        base = {"title": "T", "authors": "A"}
        base.update(meta)
        return make_book_format_dict({"book_id": 1}, {1: base})

    def test_identifiers_pubdate_tags(self):
        d = self.make(identifiers={"isbn": "123", "lccn": "xy"},
                      pubdate=datetime(2020, 5, 1), tags=("sci-fi", "classic"))
        self.assertEqual(d["isbn"], "123")
        self.assertEqual(d["lccn"], "xy")
        self.assertEqual(d["pubdate"], "2020-05-01")
        self.assertEqual(d["tags"], "sci-fi, classic")
        self.assertIn("isbn:123", d["identifiers"])
        self.assertEqual(d["calibreid"], 1)

    def test_undefined_pubdate_is_empty(self):
        self.assertEqual(self.make(pubdate=datetime(101, 1, 1))["pubdate"], "")

    def test_missing_metadata_defaults_empty(self):
        d = self.make()
        self.assertEqual(d["isbn"], "")
        self.assertEqual(d["tags"], "")
        self.assertEqual(d["identifiers"], "")
        self.assertEqual(d["pubdate"], "")


class TestYamlFormatSpec(unittest.TestCase):
    def test_title_yaml_in_frontmatter(self):
        out = format_single(SafeDict(title="Book: Sub"), "title: {title:yaml}")
        self.assertEqual(out, 'title: "Book: Sub"')

    def test_plain_substitution_unchanged(self):
        self.assertEqual(format_single(SafeDict(a="1"), "v={a}"), "v=1")

    def test_unknown_placeholder_left_intact(self):
        self.assertEqual(format_single(SafeDict(a="1"), "{unknown}"), "{unknown}")


class TestBookDataSplitting(unittest.TestCase):
    def test_unlimited_merges_in_sort_order(self):
        b = BookData("T", header="H", notes=[["cccc", 3], ["aaaa", 1], ["bbbb", 2]])
        self.assertEqual(list(b.make_sendable_notes(-1)), [("T", "Haaaabbbbcccc")])

    def test_splits_when_over_max_size(self):
        b = BookData("T", header="H", notes=[["aaaa", 1], ["bbbb", 2], ["cccc", 3]])
        out = list(b.make_sendable_notes(max_size=10, copy_header=False))
        self.assertEqual(out, [("T", "Haaaabbbb"), ("T (1)", "cccc")])


class TestBookList(unittest.TestCase):
    def test_add_note_keeps_sorted(self):
        bl = BookList()
        bl.add_note("T", "n2", 2)
        bl.add_note("T", "n1", 1)
        self.assertEqual(bl["T"].notes, [["n1", 1], ["n2", 2]])


class TestSortKey(unittest.TestCase):
    def test_location_parses_into_int_tuple(self):
        hs = HighlightSender()
        hs.set_sort_key("location")
        self.assertEqual(hs.format_sort_key({"location": "/8/4/84/1:184"}),
                         (8, 4, 84, 0, 0, 0, 0, 0, 1, 184))

    def test_non_location_key_returned_as_is(self):
        hs = HighlightSender()
        hs.set_sort_key("timestamp")
        self.assertEqual(hs.format_sort_key({"timestamp": "x"}), "x")

    def test_sort_key_stripped_and_lowercased(self):
        # a stray space or wrong case used to silently disable location sorting
        hs = HighlightSender()
        hs.set_sort_key("  Location  ")
        self.assertEqual(hs.sort_key, "location")
        self.assertEqual(hs.format_sort_key({"location": "/8/4/2:0"}), (8, 4, 0, 0, 0, 0, 0, 0, 2, 0))


class TestAllFormatKeys(unittest.TestCase):
    def test_includes_known_placeholders(self):
        keys = all_format_keys()
        for k in ("location", "timestamp", "title", "color", "chaptertitle", "tags", "colorlabel"):
            self.assertIn(k, keys)


class TestSendToFile(unittest.TestCase):
    """end-to-end exercise of the direct-file-write path (item ①)."""

    def build_sender(self, vault_path, annotations):
        s = HighlightSender()
        s.set_title_format("{title}")
        s.set_body_format("{blockquote}\n")
        s.set_no_notes_format("{blockquote}\n")
        s.set_header_format("")
        s.set_book_titles_authors({1: {"title": "MyBook", "authors": "Me"}})
        s.set_write_to_file(True)
        s.set_vault_path(vault_path)
        s.set_annotations_list(annotations)
        return s

    def test_writes_file_and_records_sent_uuids(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.build_sender(d, [make_highlight(uuid="u1", text="hello", notes="my note")])
            amt = s.send()
            self.assertEqual(amt, 1)
            self.assertEqual(s.sent_highlights, {"u1": "2022-09-10T20:32:08.820Z"})
            path = os.path.join(d, "MyBook.md")
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as f:
                self.assertIn("> hello", f.read())

    def test_missing_vault_path_raises(self):
        s = self.build_sender(os.path.join(tempfile.gettempdir(), "does-not-exist-h2o"),
                              [make_highlight()])
        with self.assertRaises(RuntimeError):
            s.send()

    def test_empty_vault_path_raises_with_field_hint(self):
        s = self.build_sender("", [make_highlight()])
        with self.assertRaises(RuntimeError) as ctx:
            s.send()
        # the message should point at the right field, not the vault name
        self.assertIn("Vault folder path", str(ctx.exception))


class TestMergeSend(unittest.TestCase):
    def hl(self, uuid, text, spine, cfi):
        return {"book_id": 1, "format": "EPUB", "annotation": {
            "type": "highlight", "timestamp": "2022-01-01T00:00:00.000Z",
            "highlighted_text": text, "uuid": uuid, "spine_index": spine, "start_cfi": cfi}}

    def sender(self, vault):
        s = HighlightSender()
        s.set_title_format("Book")
        s.set_body_format("{highlight}\n")
        s.set_no_notes_format("{highlight}\n")
        s.set_header_format("")
        s.set_book_titles_authors({1: {"title": "Book", "authors": "A"}})
        s.set_sort_key("location")
        s.set_write_to_file(True)
        s.set_vault_path(vault)
        s.set_merge_notes(True)
        return s

    def read(self, d):
        with open(os.path.join(d, "Book.md"), encoding="utf-8") as f:
            return f.read()

    def test_new_highlight_inserted_in_sorted_position(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.sender(d)
            s.set_annotations_list([self.hl("u_late", "LATE", 3, "/2/4/84/1:0"),
                                    self.hl("u_early", "EARLY", 0, "/2/4/2/1:0")])
            s.send()
            s.set_annotations_list([self.hl("u_mid", "MIDDLE", 1, "/2/4/10/1:0")])
            s.send()
            content = self.read(d)
            self.assertLess(content.index("EARLY"), content.index("MIDDLE"))
            self.assertLess(content.index("MIDDLE"), content.index("LATE"))

    def test_manual_edit_preserved_on_resend(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.sender(d)
            s.set_annotations_list([self.hl("u1", "FIRST", 0, "/2/4/2/1:0")])
            s.send()
            path = os.path.join(d, "Book.md")
            with open(path, "a", encoding="utf-8") as f:
                f.write("MY MANUAL EDIT\n")
            s.set_annotations_list([self.hl("u2", "SECOND", 1, "/2/4/10/1:0")])
            s.send()
            content = self.read(d)
            for expected in ("FIRST", "SECOND", "MY MANUAL EDIT"):
                self.assertIn(expected, content)

    def test_resend_same_highlight_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.sender(d)
            anns = [self.hl("u1", "ONLY", 0, "/2/4/2/1:0")]
            s.set_annotations_list(anns)
            s.send()
            s.send()
            self.assertEqual(self.read(d).count("ONLY"), 1)


class TestSendColumns(unittest.TestCase):
    def build_sender(self, vault_path):
        s = HighlightSender()
        s.set_title_format("{title}")
        s.set_header_format("")
        s.set_book_titles_authors({1: {"title": "BookOne", "authors": "A"},
                                   2: {"title": "BookTwo", "authors": "B"}})
        s.set_write_to_file(True)
        s.set_vault_path(vault_path)
        return s

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_one_note_per_book_with_column_content(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.build_sender(d)
            amt = s.send_columns([(1, "<p>hi from one</p>"), (2, "notes for two")])
            self.assertEqual(amt, 2)
            self.assertIn("hi from one", self.read(os.path.join(d, "BookOne.md")))
            self.assertIn("notes for two", self.read(os.path.join(d, "BookTwo.md")))

    def test_resend_overwrites_instead_of_appending(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.build_sender(d)
            s.send_columns([(1, "first")])
            s.send_columns([(1, "second")])
            content = self.read(os.path.join(d, "BookOne.md"))
            self.assertIn("second", content)
            self.assertNotIn("first", content)

    def test_skips_empty_content(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.build_sender(d)
            self.assertEqual(s.send_columns([(1, ""), (2, None)]), 0)

    def test_header_template_applied(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.build_sender(d)
            s.set_header_format("# {title}\n")
            s.send_columns([(1, "body text")])
            content = self.read(os.path.join(d, "BookOne.md"))
            self.assertTrue(content.startswith("# BookOne\n"))
            self.assertIn("body text", content)


if __name__ == "__main__":
    unittest.main()

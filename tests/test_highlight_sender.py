import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _calibre_stub
_calibre_stub.install()

from calibre_plugins.highlights_to_obsidian.highlight_sender import (
    format_data, BookData, BookList, HighlightSender, SafeDict)


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


if __name__ == "__main__":
    unittest.main()

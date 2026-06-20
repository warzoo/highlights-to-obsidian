import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _calibre_stub
_calibre_stub.install()

from calibre_plugins.highlights_to_obsidian.utils import (
    parse_send_time, parse_highlight_time, annotation_user, is_unsent_or_edited,
    note_path, write_note_to_file, native_open, parse_color_labels, parse_color_filter,
    SEND_TIME_FORMAT, CALIBRE_TIME_FORMAT)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestTimeParsing(unittest.TestCase):
    def test_parse_send_time(self):
        s = "2022-09-10 20:32:08"
        self.assertEqual(parse_send_time(s), time.mktime(time.strptime(s, SEND_TIME_FORMAT)))

    def test_parse_highlight_time_strips_millis_and_z(self):
        ts = "2022-09-10T20:32:08.820Z"
        expected = time.mktime(time.strptime("2022-09-10T20:32:08", CALIBRE_TIME_FORMAT))
        self.assertEqual(parse_highlight_time(ts), expected)


class TestAnnotationUser(unittest.TestCase):
    def test_web_user(self):
        self.assertEqual(annotation_user(True, "bob"), ("web", "bob"))

    def test_local_user(self):
        self.assertEqual(annotation_user(False, "ignored"), ("local", "viewer"))


class TestIsUnsentOrEdited(unittest.TestCase):
    def setUp(self):
        self.sent = {"a": "2022-01-01T00:00:00.000Z"}

    def test_never_sent(self):
        self.assertTrue(is_unsent_or_edited("b", "2022-01-01T00:00:00.000Z", self.sent))

    def test_already_sent_same_timestamp(self):
        self.assertFalse(is_unsent_or_edited("a", "2022-01-01T00:00:00.000Z", self.sent))

    def test_edited_since_sent(self):
        self.assertTrue(is_unsent_or_edited("a", "2022-06-01T00:00:00.000Z", self.sent))


class TestFileWriting(unittest.TestCase):
    def test_note_path_builds_subfolders(self):
        p = note_path("/vault", "Books/Sub/My Note")
        self.assertEqual(p, os.path.join("/vault", "Books", "Sub", "My Note") + ".md")

    def test_write_creates_subfolders_and_appends(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_note_to_file(d, "Books/Note", "hello", append=True)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(read(path), "hello")

            write_note_to_file(d, "Books/Note", "!", append=True)
            self.assertEqual(read(path), "hello!")

    def test_write_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            write_note_to_file(d, "Note", "first", append=True)
            path = write_note_to_file(d, "Note", "second", append=False)
            self.assertEqual(read(path), "second")


class TestColorLabelParsing(unittest.TestCase):
    def test_parses_mappings(self):
        self.assertEqual(parse_color_labels("yellow = Important\nblue = Definition"),
                         {"yellow": "Important", "blue": "Definition"})

    def test_lowercases_color_and_ignores_bad_lines(self):
        out = parse_color_labels("Yellow = Imp\n\nnot a mapping\ngreen=Idea")
        self.assertEqual(out, {"yellow": "Imp", "green": "Idea"})

    def test_empty(self):
        self.assertEqual(parse_color_labels(""), {})


class TestColorFilterParsing(unittest.TestCase):
    def test_comma_separated_lowercased(self):
        self.assertEqual(parse_color_filter("Yellow, blue ,  Green"), ["yellow", "blue", "green"])

    def test_empty_means_all(self):
        self.assertEqual(parse_color_filter(""), [])
        self.assertEqual(parse_color_filter("  ,  "), [])


class TestNativeOpen(unittest.TestCase):
    def capture(self, platform):
        calls = []
        method = native_open("obsidian://new?x=1", platform=platform,
                             startfile=lambda u: calls.append(("startfile", u)),
                             run=lambda a: calls.append(("run", a)))
        return method, calls

    def test_windows_uses_startfile(self):
        method, calls = self.capture("win32")
        self.assertEqual(method, "startfile")
        self.assertEqual(calls, [("startfile", "obsidian://new?x=1")])

    def test_macos_uses_open(self):
        method, calls = self.capture("darwin")
        self.assertEqual(method, "open")
        self.assertEqual(calls, [("run", ["open", "obsidian://new?x=1"])])

    def test_linux_uses_xdg_open(self):
        method, calls = self.capture("linux")
        self.assertEqual(method, "xdg-open")
        self.assertEqual(calls, [("run", ["xdg-open", "obsidian://new?x=1"])])


if __name__ == "__main__":
    unittest.main()

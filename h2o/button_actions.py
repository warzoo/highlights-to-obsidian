from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre.gui2 import info_dialog, error_dialog
from calibre.library import current_library_name
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.highlight_sender import HighlightSender
from calibre_plugins.highlights_to_obsidian.utils import (parse_send_time, parse_highlight_time,
                                                          annotation_user, is_unsent_or_edited,
                                                          parse_color_labels, parse_color_filter,
                                                          SEND_TIME_FORMAT)
from time import strftime, gmtime


def help_menu(parent):
    title = "Highlights to Obsidian Help Menu"
    body = "You can update the formatting of highlights sent to Obsidian in this plugin's config menu at " + \
           "Preferences -> Plugins -> User interface action -> Highlights to Obsidian.\n\n" + \
           "If you don't want the first time sending new highlights to Obsidian to send all highlights, " + \
           "update the last send time in the config.\n\n" + \
           "In the formatting config menu, the 'title' is the title of the note that a highlight will be " + \
           "sent to. The 'body' is the text that will be sent to that note for each highlight. The " + \
           "'header' will be sent to each note exactly once when you send highlights.\n\n" + \
           "In a note's title, you can include slashes \"/\" to specify what folder the note should be in.\n\n" + \
           "Sometimes, if you send highlights while your obsidian vault is closed, not all highlights will " + \
           "be sent. If this happens, you can use the \"Resend Previously Sent Highlights\" function. You can " + \
           "also enable \"Write highlights directly to vault files\" in the config to avoid this entirely.\n\n" + \
           "You can set keyboard shortcuts in calibre's Preferences -> Shortcuts -> H2O.\n\n" + \
           "Due to URI length limits, H2O can only send a few thousand words to a single note at once. Extra text " \
           "will be sent to different notes with increasing numbers added to the end of the title.\n\n" + \
           "If H2O opens your web browser instead of Obsidian, or if large notes aren't being sent, try the " + \
           "\"Open Obsidian with the OS's command\" setting at the bottom of the config's Other Options."
    info_dialog(parent, title, body, show=True)


def send_highlights(parent, db, condition=lambda x: True, update_send_time=True,
                    restrict_to_book_ids=None, record_batch=False) -> int:
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    :param condition: condition for sending a highlight
    :param update_send_time: whether or not to update prefs["last_send_time"]
    :param restrict_to_book_ids: if given, only highlights from these book ids are considered (the
     filtering happens in calibre's db, so it's cheaper than checking every highlight)
    :param record_batch: if True, the uuids sent are stored in prefs["last_batch_uuids"] so they can
     be resent later with resend_highlights()
    :return: number of highlights that were sent
    """

    def make_sender() -> HighlightSender:
        _sender = HighlightSender()
        # this might not work if the current library name has characters that don't work in urls.
        # but if i do hex encoding when it's not needed, i'll make links hard to read.
        # todo: add hex encoding, but only when necessary https://manual.calibre-ebook.com/url_scheme.html
        _sender.set_library(current_library_name())
        _sender.set_vault(prefs["vault_name"])
        _sender.set_vault_path(prefs["vault_path"])
        _sender.set_write_to_file(prefs["write_to_file"])
        _sender.set_title_format(prefs["title_format"])
        _sender.set_body_format(prefs["body_format"])
        _sender.set_no_notes_format(prefs["no_notes_format"])
        _sender.set_header_format(prefs["header_format"] if prefs["use_header"] else "")
        _sender.set_book_titles_authors(book_ids_to_metadata(db, restrict_to_book_ids))
        _sender.set_sort_key(prefs["sort_key"])
        _sender.set_sleep_time(prefs["sleep_secs"])
        _sender.set_color_labels(parse_color_labels(prefs["color_labels"]))
        _sender.set_color_filter(parse_color_filter(prefs["color_filter"]))
        if prefs['use_max_note_size']:
            _sender.set_max_file_size(int(prefs['max_note_size']), prefs['copy_header'])

        """ all_annotations() and all_annotation_users()
         https://github.com/kovidgoyal/calibre/blob/master/src/calibre/db/cache.py """
        user = annotation_user(prefs["web_user"], prefs["web_user_name"])
        _sender.set_annotations_list(
            db.all_annotations(restrict_to_user=user, restrict_to_book_ids=restrict_to_book_ids))
        return _sender

    sender = make_sender()
    try:
        amt = sender.send(condition=condition)
    except Exception as e:
        error_dialog(parent, "Highlights to Obsidian: Error sending highlights", str(e), show=True)
        return 0

    if amt > 0:
        # record which highlights were sent (by uuid) so we never accidentally double-send them.
        # a fresh dict is assigned (rather than mutated in place) so JSONConfig persists the change.
        sent = dict(prefs["sent_highlights"])
        sent.update(sender.sent_highlights)
        prefs["sent_highlights"] = sent

        if record_batch:
            prefs["last_batch_uuids"] = list(sender.sent_highlights.keys())

        if update_send_time:
            # has to be gmtime() so that we use utc, matching calibre's stored highlight times.
            prefs["last_send_time"] = strftime(SEND_TIME_FORMAT, gmtime())

        info = f"Success: {amt} highlight{' has' if amt == 1 else 's have'} been sent to Obsidian."
        if prefs['highlights_sent_dialog']:
            info_dialog(parent, "Highlights Sent", info, show=True)
    else:
        info_dialog(parent, "No Highlights Sent", "There are no highlights to send.", show=True)

    return amt


def new_highlight_condition():
    """builds the condition for 'new' highlights: made after the last send time, and not already
    sent (or edited since being sent). the uuid check makes repeated sends idempotent and means a
    selected-books send no longer hides other books' new highlights, unlike the old time-only check.
    """
    last_send_time = parse_send_time(prefs["last_send_time"])
    sent = prefs["sent_highlights"]

    def condition(highlight) -> bool:
        annot = highlight["annotation"]
        timestamp = annot["timestamp"]
        return parse_highlight_time(timestamp) > last_send_time \
            and is_unsent_or_edited(annot["uuid"], timestamp, sent)

    return condition


def send_new_highlights(parent, db):
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
    send_highlights(parent, db, new_highlight_condition(), record_batch=True)


def send_all_highlights(parent, db):
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
    if prefs['confirm_send_all']:
        confirm = QMessageBox()
        confirm.setText("Are you sure you want to send ALL highlights to Obsidian? This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setIcon(QMessageBox.Icon.Question)
        confirmed = confirm.exec()

        if confirmed != QMessageBox.StandardButton.Yes:
            return

    send_highlights(parent, db)


def send_new_selected_highlights(parent, db):
    """
    sends new highlights in the currently selected books in the main window.

    thanks to uuid-based dedup, this no longer advances the global last send time, so new highlights
    in non-selected books are NOT hidden from "Send New Highlights" (which was the old behavior).

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes.
    should be, or have as a property ".gui", calibre's gui object.
    :param db: calibre database: Cache().new_api
    """
    gui = resolve_gui(parent)
    selected_ids = selected_book_ids(gui)
    send_highlights(parent, db, new_highlight_condition(), update_send_time=False,
                    restrict_to_book_ids=selected_ids, record_batch=True)


def send_all_selected_highlights(parent, db):
    """
    sends all highlights in the currently selected books in the main window.

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes.
    should be, or have as a property ".gui", calibre's gui object.
    :param db: calibre database: Cache().new_api
    """

    if prefs['confirm_send_all']:
        confirm = QMessageBox()
        confirm.setText("Are you sure you want to send ALL highlights of the selected books to Obsidian? This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setIcon(QMessageBox.Icon.Question)
        confirmed = confirm.exec()

        if confirmed != QMessageBox.StandardButton.Yes:
            return

    gui = resolve_gui(parent)
    selected_ids = selected_book_ids(gui)
    send_highlights(parent, db, restrict_to_book_ids=selected_ids, update_send_time=False)


def resend_highlights(parent, db):
    """
    resends the highlights from the most recent "send new highlights" batch.

    this is mainly intended to be used in case obsidian fails to receive the highlights that were
    sent to it. this sometimes happens when the obsidian program isn't open to the right vault or
    isn't open at all when highlights are sent.

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
    last_batch = set(prefs["last_batch_uuids"])
    if not last_batch:
        info_dialog(parent, "Cannot resend highlights", "No highlights were previously sent", show=True)
        return

    def condition(highlight) -> bool:
        return highlight["annotation"]["uuid"] in last_batch

    send_highlights(parent, db, condition=condition, update_send_time=False)


def resolve_gui(parent):
    """parent may be calibre's gui object itself, or a dialog that has it as a ".gui" property."""
    try:
        parent.library_view  # check if this exists
        return parent
    except Exception:
        return parent.gui


def selected_book_ids(gui):
    rows = gui.library_view.selectionModel().selectedRows()
    return list(map(gui.library_view.model().id, rows))


def book_ids_to_metadata(db, book_ids=None):
    """
    :param db: calibre database: Cache().new_api
    :param book_ids: if given, only these book ids are looked up; otherwise the whole library.
    :return: dictionary of {book_id: {"title", "authors", "identifiers", "pubdate", "tags"}}
    """

    def format_authors(authors) -> str:
        """
        :param authors: Tuple[str] with author names in it
        :return: author names merged into a single string
        """
        auths = list(authors)
        if len(auths) > 1:
            auths[-1] = "and " + auths[-1]

        return ", ".join(auths) if len(auths) > 2 else " ".join(auths)

    ret = {}
    ids = db.all_book_ids() if book_ids is None else book_ids

    for book_id, title in db.all_field_for('title', ids).items():
        ret[book_id] = {
            "title": title,
            "authors": format_authors(db.field_for("authors", book_id)),
            "identifiers": db.field_for("identifiers", book_id),  # dict, e.g. {"isbn": "..."}
            "pubdate": db.field_for("pubdate", book_id),  # datetime
            "tags": db.field_for("tags", book_id),  # tuple of strings
        }

    return ret

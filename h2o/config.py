import time

from qt.core import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                     QPushButton, QDialog, QDialogButtonBox, QCheckBox)
from calibre.gui2 import warning_dialog
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.utils import parse_send_time, SEND_TIME_FORMAT
from calibre_plugins.highlights_to_obsidian.__init__ import version

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/highlights_to_obsidian) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/highlights_to_obsidian')

# Set defaults
# set time to 2 days after unix epoch start. hopefully prevents platform-dependent invalid default
# last_send_time when using time.mktime()

sort_key_default = "location"

# might be better to move these into resource files
library_default_name = "Calibre Library"
vault_default_name = "My Vault"
title_default_format = "Books/{title} by {authors}"
body_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC:\n{blockquote}\n\n{notes}\n\n---\n"
no_notes_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC:\n{blockquote}\n\n---\n"
header_default_format = "\n{booksent} highlights from \"{title}\" sent on {datenow} at {timenow} UTC.\n\n---\n"

prefs.defaults['library_name'] = library_default_name
prefs.defaults['vault_name'] = vault_default_name
prefs.defaults['title_format'] = title_default_format
prefs.defaults['body_format'] = body_default_format
prefs.defaults['no_notes_format'] = no_notes_default_format
prefs.defaults['header_format'] = header_default_format
prefs.defaults['use_header'] = False  # empty string is equal to false
prefs.defaults['sort_key'] = sort_key_default

prefs.defaults['last_send_time'] = time.strftime(SEND_TIME_FORMAT, time.gmtime(172800))
prefs.defaults['prev_send'] = None  # deprecated; kept so old configs don't error
prefs.defaults['sent_highlights'] = {}  # {highlight uuid: timestamp} of highlights already sent
prefs.defaults['last_batch_uuids'] = []  # uuids sent in the most recent "send new" batch (for resend)
prefs.defaults['display_help_on_menu_open'] = True
prefs.defaults['confirm_send_all'] = True  # confirmation dialog when sending all highlights
prefs.defaults['highlights_sent_dialog'] = True  # show popup with how many highlights were sent
prefs.defaults['max_note_size'] = "20000"
prefs.defaults['use_max_note_size'] = True  # make max_note_size easy to toggle
prefs.defaults['copy_header'] = False  # whether to copy header when splitting a too-big note
prefs.defaults['web_user_name'] = "*"
prefs.defaults['web_user'] = False  # whether we should send web user or local user's highlights
prefs.defaults['use_xdg_open'] = False
prefs.defaults['sleep_secs'] = 0.1
prefs.defaults['write_to_file'] = False  # write directly to vault files instead of using the obsidian:// URI
prefs.defaults['vault_path'] = ""  # filesystem path to the obsidian vault, required when write_to_file is True
prefs.defaults['merge_notes'] = False  # insert highlights in sorted position, preserving edits (file mode)
prefs.defaults['color_labels'] = ""  # newline-separated "color = label" mappings for {colorlabel}
prefs.defaults['color_filter'] = ""  # comma-separated colors to send; empty = send all colors
prefs.defaults['use_custom_column'] = False  # read annotations from a custom column instead of calibre's own
prefs.defaults['custom_column'] = ""  # the custom column's lookup name, e.g. "#annotations"



class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80
        self.spacing = 10

        # header
        self.config_label = QLabel(f'<b>Highlights to Obsidian v{version}</b>', self)
        self.l.addWidget(self.config_label)

        self.l.addSpacing(self.spacing)

        format_config_button = QPushButton("Formatting Options")
        format_config_button.clicked.connect(self.do_format_config)
        self.l.addWidget(format_config_button)

        self.l.addSpacing(self.spacing)

        other_config_button = QPushButton("Other Options")
        other_config_button.clicked.connect(self.do_other_config)
        self.l.addWidget(other_config_button)

        self.l.addSpacing(self.spacing)

    def do_format_config(self):
        dialog = FormattingDialog()
        dialog.exec()

    def do_other_config(self):
        dialog = OtherConfigDialog()
        dialog.exec()

    def save_settings(self):
        # saving is handled in the config dialog classes
        pass


class FormattingDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80
        self.spacing = 20  # pixels

        self.title_label = QLabel("<b>Highlights to Obsidian Formatting Options</b>")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        # note formatting info
        format_info = "<b>The following formatting options are available.</b> " + \
                      "To use one, put it in curly brackets, as in {title} or {blockquote}. " + \
                      "To make a value safe for Obsidian frontmatter (e.g. a title with ':'), " + \
                      "add ':yaml', as in {title:yaml}."
        self.note_format_label = QLabel(format_info, self)
        self.l.addWidget(self.note_format_label)

        self.note_format_list_label = None
        self.make_format_info_label()

        self.info_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.info_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian note title format
        self.title_format_label = QLabel('<b>Note title format:</b>', self)
        self.l.addWidget(self.title_format_label)

        self.title_format_input = QLineEdit(self)
        self.title_format_input.setText(prefs['title_format'])
        self.title_format_input.setPlaceholderText("Note title format...")
        self.l.addWidget(self.title_format_input)
        self.title_format_label.setBuddy(self.title_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian note body format
        self.body_format_label = QLabel('<b>Note body format:</b>', self)
        self.l.addWidget(self.body_format_label)

        self.body_format_input = QPlainTextEdit(self)
        self.body_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.body_format_input.setPlainText(prefs['body_format'])
        self.body_format_input.setPlaceholderText("Note body format...")
        self.l.addWidget(self.body_format_input)
        self.body_format_label.setBuddy(self.body_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian no notes body format
        self.no_notes_format_label = QLabel('<b>Body format for highlights without notes</b> (if empty, defaults to the above):',
                                            self)
        self.l.addWidget(self.no_notes_format_label)

        self.no_notes_format_input = QPlainTextEdit(self)
        self.no_notes_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.no_notes_format_input.setPlainText(prefs['no_notes_format'])
        self.no_notes_format_input.setPlaceholderText("Body format for highlights without notes...")
        self.l.addWidget(self.no_notes_format_input)
        self.no_notes_format_label.setBuddy(self.no_notes_format_input)

        self.l.addSpacing(self.spacing)

        # label for header formatting options
        self.header_format_label = QLabel('<b>Header format</b> (avoid highlight-specific data like {highlight} or {url}):', self)
        self.l.addWidget(self.header_format_label)

        # text box for header formatting options
        self.header_format_input = QPlainTextEdit(self)
        self.header_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.header_format_input.setPlainText(prefs['header_format'])
        self.header_format_input.setPlaceholderText("Header format...")
        self.l.addWidget(self.header_format_input)
        self.header_format_label.setBuddy(self.header_format_input)

        # checkbox to disable or enable using header
        self.header_checkbox = QCheckBox("Use header when sending highlights")
        if prefs['use_header']:
            self.header_checkbox.setChecked(True)
        self.l.addWidget(self.header_checkbox)

        self.l.addSpacing(self.spacing)

        # per-color labels for the {colorlabel} option
        self.color_labels_label = QLabel(
            "<b>Highlight color labels</b> (optional): map a color to text for the {colorlabel} option, "
            "one per line, e.g. \"yellow = Important\".", self)
        self.l.addWidget(self.color_labels_label)

        self.color_labels_input = QPlainTextEdit(self)
        self.color_labels_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.color_labels_input.setPlainText(prefs['color_labels'])
        self.color_labels_input.setPlaceholderText("yellow = Important\nblue = Definition")
        self.l.addWidget(self.color_labels_input)
        self.color_labels_label.setBuddy(self.color_labels_input)

        self.l.addSpacing(self.spacing)

        # ok and cancel buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.ok_button)
        self.buttons.rejected.connect(self.cancel_button)
        self.l.addWidget(self.buttons)

    def make_format_info_label(self):

        # list of formatting options
        format_options = [
            "title", "authors",
            "highlight", "blockquote", "notes",
            "date", "time", "datetime",
            "day", "month", "year",
            "hour", "minute", "second",
            "utcnow", "datenow", "timenow",
            "timezone", "utcoffset",
            "url", "location", "timestamp",
            "totalsent", "booksent", "highlightsent",
            "bookid", "uuid", "chaptertitle",
            "calibreid", "isbn", "lccn", "identifiers", "pubdate", "tags", "format", "color", "colorlabel",
        ]
        f_opt_str = "'" + "', '".join(format_options) + "'"

        strs = []
        char_count = 0
        start_idx = 0
        for idx in range(len(f_opt_str)):
            char_count += 1
            if char_count > 100 and f_opt_str[idx] == " ":
                strs.append(f_opt_str[start_idx:idx])
                start_idx = idx
                char_count = 0
        strs.append(f_opt_str[start_idx:])

        one_str = "<br/>".join(strs)
        self.note_format_list_label = QLabel(one_str, self)
        self.l.addWidget(self.note_format_list_label)

        local_note = QLabel("All times use UTC by default. To use local time instead, add 'local' " +
                            "to the beginning: {localdatetime}, {localnow}, etc.")
        self.l.addWidget(local_note)

        time_note = QLabel("Note that all times, except 'now' times, are the time the highlight was made, not the " +
                           "current time.")
        self.l.addWidget(time_note)

    def save_settings(self):
        prefs['title_format'] = self.title_format_input.text()
        prefs['body_format'] = self.body_format_input.toPlainText()
        prefs['no_notes_format'] = self.no_notes_format_input.toPlainText()
        prefs['header_format'] = self.header_format_input.toPlainText()
        prefs['use_header'] = self.header_checkbox.isChecked()
        prefs['color_labels'] = self.color_labels_input.toPlainText()

    def ok_button(self):
        self.save_settings()
        self.accept()

    def cancel_button(self):
        self.reject()


class OtherConfigDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 50
        self.spacing = 20  # pixels

        self.setWindowTitle("Highlights to Obsidian: Other Configuration Options")

        self.title_label = QLabel("<b>Highlights to Obsidian Other Options</b>")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian vault name
        self.vault_label = QLabel('<b>Obsidian vault name:</b>', self)
        self.l.addWidget(self.vault_label)

        self.vault_input = QLineEdit(self)
        self.vault_input.setText(prefs['vault_name'])
        self.vault_input.setPlaceholderText("Obsidian vault name...")
        self.l.addWidget(self.vault_input)
        self.vault_label.setBuddy(self.vault_input)

        self.l.addSpacing(self.spacing)

        # output method: write files directly vs. obsidian:// URI
        self.write_to_file_checkbox = QCheckBox(
            "Write highlights directly to vault files (more reliable: doesn't need Obsidian open, "
            "no URI length limit, ignores max note size)")
        self.write_to_file_checkbox.setChecked(prefs['write_to_file'])
        self.l.addWidget(self.write_to_file_checkbox)

        self.vault_path_label = QLabel("<b>Vault folder path</b> (required when writing directly to files):", self)
        self.l.addWidget(self.vault_path_label)
        self.vault_path_input = QLineEdit(self)
        self.vault_path_input.setText(prefs['vault_path'])
        self.vault_path_input.setPlaceholderText("e.g. C:/Users/you/Documents/My Vault")
        self.l.addWidget(self.vault_path_input)
        self.vault_path_label.setBuddy(self.vault_path_input)

        self.merge_notes_checkbox = QCheckBox(
            "Keep notes sorted and preserve your edits: insert new highlights in position instead of "
            "appending (only when writing to files; adds small hidden %%h2o%% markers to track position)")
        self.merge_notes_checkbox.setChecked(prefs['merge_notes'])
        self.l.addWidget(self.merge_notes_checkbox)

        self.l.addSpacing(self.spacing)

        # sort key
        self.sort_label = QLabel("<b>Sort key:</b> used to sort highlights that get sent to the same file.<br/>"
                                 + "(Sort keys can be any of H2O's formatting options. No brackets. "
                                 + "For example, <br/>timestamp or location.)", self)
        self.l.addWidget(self.sort_label)

        self.sort_input = QLineEdit(self)
        self.sort_input.setText(prefs['sort_key'])
        self.l.addWidget(self.sort_input)
        self.sort_label.setBuddy(self.sort_input)

        self.l.addSpacing(self.spacing)

        # color filter: only send highlights of these colors
        self.color_filter_label = QLabel(
            "<b>Only send these highlight colors</b> (comma-separated, e.g. \"yellow, blue\"; "
            "leave empty to send all colors):", self)
        self.l.addWidget(self.color_filter_label)

        self.color_filter_input = QLineEdit(self)
        self.color_filter_input.setText(prefs['color_filter'])
        self.color_filter_input.setPlaceholderText("yellow, blue (empty = all colors)")
        self.l.addWidget(self.color_filter_input)
        self.color_filter_label.setBuddy(self.color_filter_input)

        self.l.addSpacing(self.spacing)

        # time setting
        self.time_label = QLabel('<b>Last time highlights were sent</b> (highlights made after this are considered new)', self)
        self.l.addWidget(self.time_label)

        # time format info
        self.time_format_label = QLabel("Time must be formatted \"YYYY-MM-DD hh:mm:ss\"")
        self.l.addWidget(self.time_format_label)

        self.time_input = QLineEdit(self)
        self.time_input.setText(prefs['last_send_time'])
        self.l.addWidget(self.time_input)
        self.time_label.setBuddy(self.time_input)

        # button to set time to now
        self.set_time_now_button = QPushButton("Set last send time to now (UTC)", self)
        self.set_time_now_button.clicked.connect(self.set_time_now)
        self.l.addWidget(self.set_time_now_button)

        self.l.addSpacing(self.spacing)

        # max note size and related settings
        self.max_size_label = QLabel("<b>Maximum note size</b> (errors can happen when notes are too long):")
        self.l.addWidget(self.max_size_label)

        self.max_size_input = QLineEdit()
        self.max_size_input.setText(prefs['max_note_size'])
        self.max_size_input.setPlaceholderText("Max note size...")
        self.l.addWidget(self.max_size_input)

        self.use_max_size_checkbox = QCheckBox("Restrict length of sent notes to the max note size")
        self.use_max_size_checkbox.setChecked(prefs['use_max_note_size'])
        self.l.addWidget(self.use_max_size_checkbox)

        self.copy_header_checkbox = QCheckBox("When splitting up a long note, include the header in each smaller note")
        self.copy_header_checkbox.setChecked(prefs['copy_header'])
        self.l.addWidget(self.copy_header_checkbox)

        self.l.addSpacing(self.spacing)

        # checkbox for confirmation dialog
        self.show_confirmation_checkbox = QCheckBox("Confirmation dialog when sending all highlights")
        self.show_confirmation_checkbox.setChecked(prefs['confirm_send_all'])
        self.l.addWidget(self.show_confirmation_checkbox)

        # checkbox for showing how many highlights were sent
        self.show_count_checkbox = QCheckBox("After sending highlights, show how many were sent")
        self.show_count_checkbox.setChecked(prefs['highlights_sent_dialog'])
        self.l.addWidget(self.show_count_checkbox)

        self.l.addSpacing(self.spacing)

        # input for sleep time between highlights
        self.sleep_label = QLabel('<b>Time to wait</b> between sending files (in seconds):', self)
        self.l.addWidget(self.sleep_label)

        self.sleep_time_input = QLineEdit()
        self.sleep_time_input.setText(str(prefs['sleep_secs']))
        self.sleep_time_input.setPlaceholderText("Web user name (asterisk if no username is used)...")
        self.l.addWidget(self.sleep_time_input)

        self.l.addSpacing(self.spacing)

        # input for web user's name
        self.web_label = QLabel('<b>Web user\'s username</b> (if sending web user\'s highlights):', self)
        self.l.addWidget(self.web_label)

        self.web_user_name_input = QLineEdit()
        self.web_user_name_input.setText(prefs['web_user_name'])
        self.web_user_name_input.setPlaceholderText("Web user name (asterisk if no username is used)...")
        self.l.addWidget(self.web_user_name_input)

        # checkbox for local user or web user
        self.web_user_checkbox = QCheckBox("Send web user's highlights (instead of local user's highlights)")
        self.web_user_checkbox.setChecked(prefs['web_user'])
        self.l.addWidget(self.web_user_checkbox)

        self.l.addSpacing(self.spacing)

        # read annotations from a custom column (e.g. one populated by the Annotations plugin) instead
        # of calibre's built-in annotations. sends the column's content as the note body, one per book.
        self.use_column_checkbox = QCheckBox(
            "Read annotations from a custom column instead of calibre's built-in annotations "
            "(sends the column's content as the note body, one note per book)")
        self.use_column_checkbox.setChecked(prefs['use_custom_column'])
        self.l.addWidget(self.use_column_checkbox)

        self.custom_column_label = QLabel("<b>Custom column lookup name</b> (e.g. #annotations):", self)
        self.l.addWidget(self.custom_column_label)
        self.custom_column_input = QLineEdit(self)
        self.custom_column_input.setText(prefs['custom_column'])
        self.custom_column_input.setPlaceholderText("#annotations")
        self.l.addWidget(self.custom_column_input)
        self.custom_column_label.setBuddy(self.custom_column_input)

        # checkbox for opening Obsidian with the OS's native command instead of Python's webbrowser
        self.native_open_checkbox = QCheckBox(
            "Open Obsidian with the OS's command (Windows/macOS/Linux) instead of Python's webbrowser "
            "(may help if highlights open a web browser, or if large notes aren't sent)")
        self.native_open_checkbox.setChecked(prefs['use_xdg_open'])
        self.l.addWidget(self.native_open_checkbox)

        self.l.addSpacing(self.spacing)

        # ok and cancel buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.ok_button)
        self.buttons.rejected.connect(self.cancel_button)
        self.l.addWidget(self.buttons)

    def set_time_now(self):
        prefs["last_send_time"] = time.strftime(SEND_TIME_FORMAT, time.gmtime())
        self.time_input.setText(prefs['last_send_time'])

    def save_settings(self):
        prefs['vault_name'] = self.vault_input.text()
        prefs['write_to_file'] = self.write_to_file_checkbox.isChecked()
        prefs['vault_path'] = self.vault_path_input.text()
        prefs['merge_notes'] = self.merge_notes_checkbox.isChecked()
        prefs['color_filter'] = self.color_filter_input.text()

        # strip the sort key (a stray space silently disables sorting), and warn if it isn't a real
        # formatting option -- a common reason "sort by location" appears to do nothing.
        sort_key = self.sort_input.text().strip()
        prefs['sort_key'] = sort_key
        if sort_key:
            try:
                from calibre_plugins.highlights_to_obsidian.highlight_sender import all_format_keys
                valid_keys = all_format_keys()
            except Exception:
                valid_keys = None
            if valid_keys is not None and sort_key.lower() not in valid_keys:
                warning_dialog(self, "Unknown sort key",
                               f'"{sort_key}" is not one of the formatting options, so highlights won\'t be '
                               f'sorted by it. Use an option from Formatting Options without brackets, '
                               f'e.g. "location" or "timestamp".', show=True)
        max_size = self.max_size_input.text()
        prefs['max_note_size'] = max_size if max_size.isnumeric() else prefs['max_note_size']
        prefs['use_max_note_size'] = self.use_max_size_checkbox.isChecked()
        prefs['copy_header'] = self.copy_header_checkbox.isChecked()
        prefs['confirm_send_all'] = self.show_confirmation_checkbox.isChecked()
        prefs['highlights_sent_dialog'] = self.show_count_checkbox.isChecked()
        username = self.web_user_name_input.text()
        prefs['web_user_name'] = "*" if username == "" else username
        prefs['web_user'] = self.web_user_checkbox.isChecked()
        prefs['use_custom_column'] = self.use_column_checkbox.isChecked()
        prefs['custom_column'] = self.custom_column_input.text().strip()
        prefs['use_xdg_open'] = self.native_open_checkbox.isChecked()

        sleep_time = self.sleep_time_input.text()
        try:
            prefs['sleep_secs'] = float(sleep_time)
        except:
            txt = f'Could not parse "{sleep_time}". The time to wait between sending highlights will not be changed. ' + \
                  f'Old value of "{prefs["sleep_secs"]}" will be kept.'
            warning_dialog(self, "Invalid Time", txt, show=True)

        # validate time input
        send_time = self.time_input.text()
        try:
            parse_send_time(send_time)
            prefs['last_send_time'] = send_time
        except:
            txt = f'Could not parse time "{send_time}". Either it is formatted improperly or the year is too high' + \
                  f' or low.\n\n Keeping previous time "{prefs["last_send_time"]}" instead.'
            warning_dialog(self, "Invalid Time", txt, show=True)

    def ok_button(self):
        self.save_settings()
        self.accept()

    def cancel_button(self):
        self.reject()

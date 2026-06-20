
# Highlights to Obsidian

Highlights to Obsidian is a plugin for the [calibre ebook manager](https://calibre-ebook.com/) that formats and sends highlights to [Obsidian.md markdown editor](https://obsidian.md/). This plugin has a thread [on the calibre forum](https://www.mobileread.com/forums/showthread.php?t=351283).

After installing, go to Preferences -> Toolbars & menus -> The main toolbar. The Highlights to Obsidian menu button is listed as H2O.

1. [Useful Info](#info)
2. [Formatting Options](#formatting)
3. [Misc](#misc)

<a name="info"></a>
## Useful Info

- You can change how highlights are formatted in the config menu or at Preferences -> Plugins -> User interface action -> Highlights to Obsidian.

- If you don't want the first time sending new highlights to send all of your highlights, you can update the last send time in the config.

- In the formatting config menu, the 'title' is the title of the note that a highlight will be sent to. The 'body' is the text that will be sent to that note for each highlight. The 'header' will be sent to each note exactly once when you send highlights.

- In a note's title, you can include slashes "/" to specify what folder the note should be in.

- Sometimes, if you send highlights while your Obsidian vault is closed, not all highlights will be sent. If this happens, you can use the "Resend Previously Sent Highlights" function.

- For more reliable sending, you can have H2O write highlights directly to your vault's files instead of using the `obsidian://` URI. Set your vault's folder path and enable "Write highlights directly to vault files" in the config's Other Options. This avoids lost highlights, doesn't require Obsidian to be open, and has no note length limit.

- Highlights are tracked by their unique ID, so sending the same highlight twice won't create duplicates, and a highlight you edit in calibre will be re-sent the next time you send new highlights.

- You can restrict sending to specific highlight colors with the "Only send these highlight colors" option in the config's Other Options. Leave it empty to send all colors.

- Instead of calibre's built-in annotations, you can have H2O read annotations from a custom column (for example, a column populated by the [Annotations](https://github.com/davidfor/calibre-annotations) plugin). Enable "Read annotations from a custom column" in the config's Other Options and enter the column's lookup name (e.g. `#annotations`). H2O then sends each book's column content as the note body (one note per book, overwritten on each send). Per-highlight options like {blockquote}, {color}, {location}, and sorting don't apply in this mode, since the column holds rendered text rather than calibre's structured highlight data.

- You can set keyboard shortcuts in Preferences -> Shortcuts -> H2O.

- Due to URI length limits, H2O can only send a few thousand words to a single note at once. Extra text will be sent to different notes with increasing numbers added to the end of the title. This can be changed in the config.

<a name="formatting"></a>
## Formatting Options

![](/images/formatting-options.png)

To make a value safe to use inside Obsidian's YAML frontmatter (for example, a book title that contains a colon ":"), add `:yaml` to the placeholder, e.g. `{title:yaml}`. This wraps the value in quotes so it won't break your frontmatter.

**Book Data:**
- {title}: Title of the book the highlight is in.
- {authors}: Authors of the book the highlight is in.
- {bookid}: The book's ID in calibre. 
- {calibreid}: The book's ID in calibre (same as {bookid}).
- {isbn}: The book's ISBN identifier, if set.
- {lccn}: The book's LCCN identifier, if set.
- {identifiers}: All of the book's identifiers, joined together, e.g. "isbn:..., google:...".
- {pubdate}: The book's publication date, formatted as YYYY-MM-DD.
- {tags}: The book's tags, separated by commas.

**Highlight Data:**
- {highlight}: The highlighted text.
- {blockquote}: The highlighted text, formatted as a blockquote. An arrow and a space "> " are added to the beginning of each line.
- {notes}: The user's notes on this highlight, if any notes exist. There is a config option that allows you to set different formatting depending on whether a highlight includes notes.
- {url}: A [calibre url](https://manual.calibre-ebook.com/url_scheme.html) to open the ebook viewer to this highlight. Note that this may not work if your library's name contains unsafe URL characters. Numbers, letters, spaces, underscores, and hyphens are all safe.
- {location}: The highlight's EPUB CFI location in the book. For example, "/2/8/6/5:192". As a sort key, this will order highlights by their position in the book.
- {timestamp}: The highlight's Unix timestamp. As a sort key, this will order highlights by when they were made.
- {uuid}: The highlight's unique ID in calibre. For example, "TlNlh8_I5VGKUtqdfbOxDw".
- {chaptertitle}: The title of the chapter (table of contents section) the highlight is in. For example, "1.1 The Basic Pigeon-Hole Principle". If the book has nested sections, the most specific (deepest) one is used. Slashes are replaced with hyphens so it can be used in note titles. This lets you make a note per chapter, e.g. a title of "Books/{title}/{chaptertitle}".
- {format}: The book format the highlight is in, e.g. EPUB.
- {color}: The highlight's color, e.g. "yellow". For decoration-style highlights (underline, etc.) this is the decoration name instead.
- {colorlabel}: A custom label for the highlight's color, configured in the Formatting Options (map a color to text, e.g. "yellow = Important"). Falls back to the color name if no label is set. Useful for giving each color a meaning, e.g. a body of "{colorlabel}: {blockquote}".

**Time Data:**
- {date}: Date the highlight was made, formatted as YYYY-MM-DD.
- {time}: Time the highlight was made, formatted as HH:MM:SS.
- {datetime}: Date and time highlight was made, formatted as YYYY-MM-DD HH:MM:SS.
- {day}: Day of the month the highlight was made, as in 03 or 17.
- {month}: Month the highlight was made, as in 04 for April or 10 for October.
- {year}: Full year the highlight was made, as in 2022.
- {hour}: Hour the highlight was made, based on a 24-hour (not 12-hour) system.
- {minute}: Minute the highlight was made.
- {second}: Second the highlight was made.
- {utcnow}: current time, formatted same as {datetime}.
- {datenow}: Current date, formatted same as {date}.
- {timenow}: Current time, formatted same as {time}.
- {timezone}: The timezone that your computer is currently set to. Note that this may not always match the timezone the highlight was made in. Also note that this might use the full name "Coordinated Universal Time" instead of the abbreviation "UTC".
- {utcoffset}: The UTC offset of your computer's current time zone. For example, UTC time gives +0:00. EST time can be -4:00 or -5:00, depending on daylight savings time.
- All time options use UTC by default. To use your computer's local time zone instead, add "local" to the beginning: {localdate}, {localtime}, {localdatetime}, {localday}, {localmonth}, {localyear}, {localhour}, {localminute}, {localsecond}, {localnow}, {localdatenow}, {localtimenow}.

**H2O Data:**
- {totalsent}: The total number of highlights being sent.
- {booksent}: The total number of highlights being sent to this Obsidian note. If a large note is split into multiple smaller notes, {booksent} will give the total being sent to all of those smaller notes.
- {highlightsent}: This highlight's position in the highlights being sent to this note. For example, "{highlightsent} out of {booksent}" might result in "3 out of 5".

![](/images/send-success.png)

<a name="misc"></a>
## Misc

This plugin is loosely based on the [Obsidian Clipper](https://github.com/jplattel/obsidian-clipper) Chrome extension.

The file `h2o-index.txt` is for the [plugin index page](https://www.mobileread.com/forums/showthread.php?t=118764) on the calibre forum.

#!/usr/bin/env python3
"""Normalize legacy Eterm 0.9.6 mouse-source variants before v24 patch.

The 0.9.6 tarball and the previously reconstructed patch baseline have minor
whitespace and mouse-release differences.  Only these tightly scoped source
sections are normalized.  Fail if an unknown variant is encountered.
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit('usage: eterm-v24-compat-prep.py EXTRACTED_ETERM_ROOT')
src = Path(sys.argv[1]) / 'src'
header_file = src / 'command.h'
events_file = src / 'events.c'
header = header_file.read_text()
events = events_file.read_text()

# The original tarball may use a tab and no preceding blank line for this macro.
pattern = re.compile(
    r'(?m)^(# define PrivMode_menuBar[^\n]*\n)'
    r'(?:[ \t]*\n)*'
    r'#define[ \t]+PrivMode_mouse_report[ \t]*'
    r'\(PrivMode_MouseX10\|PrivMode_MouseX11\)[ \t]*$'
)
if len(pattern.findall(header)) != 1:
    sys.exit('command.h: expected one legacy mouse-report macro')
header = pattern.sub(
    r'\1\n#define PrivMode_mouse_report (PrivMode_MouseX10|PrivMode_MouseX11)',
    header, count=1,
)

beg = events.find('handle_button_release(event_t *ev)')
end = events.find('handle_motion_notify(event_t *ev)', beg)
if beg < 0 or end < beg:
    sys.exit('events.c: mouse-release/motion functions not found')
release = events[beg:end]

# The source snapshot differs in the spacing before the VT window test.
spacing = re.compile(
    r'(    button_state.report_mode = \(button_state.bypass_keystate \? 0 : '
    r'\(\(PrivateModes & PrivMode_mouse_report\) \? 1 : 0\)\);\n)'
    r'(?:[ \t]*\n)*'
    r'(?=    if \(ev->xany.window == TermWin.vt\) \{)'
)
if len(spacing.findall(release)) != 1:
    sys.exit('events.c: unexpected mouse-release report-mode layout')
release = spacing.sub(r'\1\n', release, count=1)

needle = 'if (button_state.report_mode) {'
if release.count(needle) != 1:
    sys.exit('events.c: expected one release reporting branch')
start = release.index(needle)
opening = release.index('{', start)
level, finish = 0, None
for i in range(opening, len(release)):
    if release[i] == '{':
        level += 1
    elif release[i] == '}':
        level -= 1
        if level == 0:
            finish = i + 1
            break
if finish is None:
    sys.exit('events.c: unbalanced mouse-release reporting block')
old = release[start:finish]
if 'mouse_report(' not in old or 'return (1);' not in old:
    sys.exit('events.c: unknown mouse-release reporting implementation')
canonical = '''if (button_state.report_mode) {
                switch (PrivateModes & PrivMode_mouse_report) {
                    case PrivMode_MouseX10:
                        break;
                    case PrivMode_MouseX11:
                        ev->xbutton.state = button_state.bypass_keystate;
                        ev->xbutton.button = AnyButton;
                        mouse_report(&(ev->xbutton));
                        break;
                }
                return (1);
            }'''
release = release[:start] + canonical + release[finish:]

motion = events[end:]
pattern = re.compile(
    r'(    REQUIRE_RVAL\(XEVENT_IS_MYWIN\(ev, &primary_data\), 0\);\n)'
    r'(?:[ \t]*\n)*'
    r'(?=#ifdef HAVE_TWIN)'
)
# Scope this edit to handle_motion_notify() only.
next_func = motion.find('process_x_event(event_t *ev)')
if next_func < 0:
    sys.exit('events.c: no process_x_event() after mouse motion')
subsection = motion[:next_func]
if len(pattern.findall(subsection)) != 1:
    sys.exit('events.c: unexpected mouse-motion layout')
subsection = pattern.sub(r'\1\n', subsection, count=1)
events = events[:beg] + release + subsection + motion[next_func:]

# Validate all anchors before writing either file.
header_file.write_text(header)
events_file.write_text(events)
print('Eterm v24: normalized legacy mouse source for the consolidated patch')

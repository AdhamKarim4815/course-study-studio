# Course Study Studio

A skill for Claude that turns a course's slides into an exam-prep studio: animated formula walkthroughs, exam-style practice, flashcards and a printable iPad workbook. Everything is scoped to exactly what your test covers.

## What it builds

For one course and one test:

- **A studio page with five tabs**
  - Start here: test facts, scope, a minute-by-minute time plan, and how to write a full-marks answer.
  - Lessons: they play like short videos. Numbers fly from a facts table into the working, results pop in, and a caption explains each step and can be read aloud. You can play, pause, scrub, step through and change speed.
  - Practice: exam-style questions with model answers, plus a quiz.
  - Memory sheet: every formula, flashcards, comparison tables and common traps.
  - Workbook: the downloads.
- **A workbook PDF** for GoodNotes or Notability on an iPad, in landscape. Each lesson gets a write-in page whose boxes carry the same step numbers as the video, then a "Your turn" page with new numbers. An answer key is at the back.
- **A pocket formula card** the size of a playing card, and an **aid-sheet draft** when your test allows one.
- **Optional natural narration**: each step recorded with the free Kokoro voices instead of your device's voice.

## How it works

- **Scope first.** Claude reads the test announcement, syllabus and module dates, and builds only what's on the test. Courses often post the whole term.
- **Everything is data.** One `kit.json` file holds the lessons, practice questions, quiz and memory sheet. Every number is worked out in a small Python script before it's written into a lesson. A checker then confirms the kit is consistent before anything gets built.
- **One source for everything.** The page and the PDFs are made from the same data, so the workbook's step numbers always match the videos.

## Install

**Claude apps (web and desktop).**

1. Download `course-study-studio.zip` from the [latest release](https://github.com/adhamkarim4815/course-study-studio/releases/latest). Use that file, not the "Source code" zips GitHub adds: their folder name doesn't match the skill name, so the upload fails.
2. Turn on code execution: Settings, Capabilities, "Code execution and file creation". On Team and Enterprise plans, an owner controls this.
3. Go to Customize, Skills. Click +, then Create skill, then Upload a skill, and choose the zip.

Anthropic's guide: [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

**Claude Code.**

```sh
git clone https://github.com/adhamkarim4815/course-study-studio ~/.claude/skills/course-study-studio
```

See [Extend Claude with skills](https://code.claude.com/docs/en/skills).

## Use it

Give Claude the slides, the test announcement (what's covered, format, allowed aids) and any practice tests, then ask. For example:

- "Build a study studio for my ECO101 midterm on Friday. Here are the slides and the announcement."
- "Use Claude in Chrome to get my course files from Quercus, then make a midterm study kit for chapters 1 to 6."
- "Make the workbook and pocket card too, and record the lessons with natural voices."

A full studio is a long job: about 12 to 16 lessons per course. Claude splits the lessons across helpers when it can.

## What's in this repo

| Path | What it is |
| --- | --- |
| `SKILL.md` | The instructions Claude follows |
| `scripts/validate_kit.py` | Checks a `kit.json` for broken references, unfilled blanks, out-of-range quiz answers and caption numbers that don't match the calc scripts. Python standard library only. |
| `examples/example-kit.json` | A complete one-lesson kit (a fictional lemonade stand) showing the format |
| `examples/calc_break-even.py` | The script that computes every number in that lesson |

To try the checker:

```sh
python3 scripts/validate_kit.py examples/example-kit.json --calc-dir examples
```

## Your course materials

Studios are built from your course's slides and announcements, which belong to your instructors. Keep what you make for your own study, and don't post it publicly.

## License

[MIT](LICENSE)

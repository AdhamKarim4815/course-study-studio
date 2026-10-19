---
name: course-study-studio
description: "Use when asked to build a study guide, study kit or exam studio for a course test: animated formula lessons, practice, flashcards and printable iPad workbook PDFs."
license: MIT
compatibility: "Needs code execution with Python and Node. Optional: Claude in Chrome to pull files from Quercus or Canvas, and the Artifact tool to publish the studio page."
---

# Course Study Studio

Turn a course's own material into a complete study studio for one test, one studio per course:

1. **Studio page**, a published claude.ai artifact, with five tabs:
   - Start here: test facts, what's in scope, a minute-by-minute time plan and an answer template.
   - Lessons: animated walkthroughs where numbers fly from a facts table into the working, with a caption per step read aloud.
   - Practice: exam-style questions with model answers, plus a quiz.
   - Memory sheet: formulas, flashcards, comparison tables and traps.
   - Workbook: the downloads.
2. **Workbook PDF** for iPad (GoodNotes or Notability), in landscape: one write-in page per lesson whose boxes carry the video's step numbers, a "Your turn" page with new numbers, and an answer key.
3. **Pocket formula card** (2.5 x 3.5 in), and an aid-sheet draft when the test allows one.

Writing rules:

- Plain English first, then the textbook term ("the textbook name for this is...").
- Warm and direct.
- Only what the test covers.
- Invented numbers are labelled fictional.

This is a big job, so keep a task list and send drafts as soon as they are useful. If you can run subagents, split lessons across them.

## Step 1: Gather the material

- **Uploaded files:** read every deck fully. Run `pdftotext -layout` into a scratch folder, then read the text. Scanned PDFs have no text layer: render pages with `pdftoppm` and look at the images. Pull out every formula, worked example and in-class question with its exact numbers.
- **Quercus or Canvas through Claude in Chrome** (load its skill first, and work in the user's logged-in tab). Call the Canvas API from the page with `javascript_tool`, using same-origin `fetch` with `credentials: 'include'`:
  - modules: `/api/v1/courses/<id>/modules?include[]=items&per_page=100`
  - files: `/api/v1/courses/<id>/files?per_page=100`
  - announcements: `/api/v1/announcements?context_codes[]=course_<id>`
  - syllabus: `/api/v1/courses/<id>?include[]=syllabus_body`
  - Long results get truncated, so stash them in `window.__x` and read slices.
  - Results that look like tokens get blocked, so strip query strings from URLs.
  - To download, fetch the PDFs in page JS, zip them, and click an `<a download>` link so they land in Downloads. Then ask the user to attach them, or stage them if the computer is linked.
- **Otherwise:** ask for the slides, the test announcement and any practice tests.

## Step 2: Scope to exactly what the test covers

Courses often post the whole term. Use the test announcement (date, time, rooms, format, aids, coverage), the syllabus, the lecture schedule, module dates and past or practice tests. If the user pastes an announcement, treat it as the authority.

- Keep material taught up to the test and named as in scope, and drop later classes.
- Record each fact with its source; it shows on Start here.
- Ask one question only if coverage is genuinely unclear. Otherwise state the reading you took.

## Step 3: Write everything as data (kit.json)

The whole studio is one JSON object; the page just renders it. Compute every number in Python before writing it: keep one `calc_<lesson>.py` per lesson that prints every value the lesson shows. Follow the course's rounding (break-even units round UP; keep unrounded values a later step reuses). Slide examples keep the slides' numbers.

**Lesson design.**

- Coverage: one lesson per formula family, a what-if lesson (what moves when one input changes), a decisions lesson, and one walkthrough per practice case. Typically that's 12 to 16 lessons of 12 to 21 steps.
- Per calculation: one step flies the inputs in, the next pops the result, then a step says it in words.
- Essay courses: diagnosis or classification lessons, where "?" cells in the table fill in step by step through `cells`.

**With subagents:**

- Give each content agent about 5 lessons, the scope, the source paths, this format and the rules.
- Then have a fresh audit agent re-run every calc script, check scope and numbers against the PDFs, and fix what's wrong.
- Verify agent reports rather than trusting them.

```ts
{
  meta: { code: 'ABC123', name, assessment: 'Midterm', dateLabel, dateISO, studioTitle, tagline, lessonOrder: string[] },
  start: {
    facts: { k, v, src }[], rooms?: { title, rows: [range, room][], note },
    scope: { in: string[], out: string[], src }, timePlan: { t, do }[],
    template: { title, steps: { name, what }[], weak, strong },   // e.g. Label / Formula / Substitute / Answer / So what
    likely: { q, lesson }[], mistakes: string[], plan: { day, do: string[] }[],
  },
  lessons: Lesson[],
  practice: { id, title, source, minutes, context /* markdown */, parts: { q, marks, answer, lesson }[] }[],
  quiz: { id, group, q, options: string[], answer /* index */, why, lesson }[],
  memory: { formulas: { group, name, f, note? }[], cards: { group, q, a }[],
            tables: { title, headers, rows }[], traps: string[] },
}
Lesson = { id, group, title, blurb, source, fictional,
  table: { title, headers, rows: string[][], derived: number[] }, lines: Line[], steps: Step[],
  trap, words: { prompt, answer }, yourTurn: { intro, table: { headers, rows }, asks: { q, a }[] },
  chart?: { title, x: Axis, y: Axis, layers: Layer[] } }
Line = { id, kind: 'eq'|'head'|'note'|'total'|'formula', label?, always?, parts: Part[] }
Part = string | { s: slotId, ph: placeholder } | { f: termId, text }      // text, a blank, a glowable term
Step = { say /* caption, **bold** ok */, dur?, hl?: cell[], strike?: cell[], cells?: { [cell]: text },
         fly?: { from: cell | '@slotId', to: slotId, text? }[], calc?: { [slotId]: value },
         show?: lineId[], focus?: id[], reveal?: layerId[] }       // cell = "row.col"
Axis = { label, min, max, ticks: number[], fmt: 'n'|'$'|'%'|'d1'|'d2' }
Layer = { id, kind, tone: 'info'|'hl'|'ok'|'bad'|'muted', label? } plus, by kind:
  line|points: points [[x,y]]; hline: y; vline: x; segments: [[x1,y1,x2,y2]]; bars: [[x0,x1,h]];
  area: points; label: x, y, text; box: y, h, min, q1, med, q3, max, outliers
```

This skill's folder has a complete one-lesson example to copy the shape from: `examples/example-kit.json`, a fictional lemonade stand, with its `examples/calc_break-even.py`.

**Validate before building** with the bundled checker:

```
python3 <this skill's folder>/scripts/validate_kit.py kit.json --calc-dir <folder with the calc scripts>
```

It checks that:

- ids are unique, and `lessonOrder` matches the lessons;
- every `fly.from` cell is inside its table, and every `@slot` is filled earlier;
- every `to`, `calc`, `show`, `focus` and `reveal` id exists, and every slot is filled by the end;
- quiz answers are in range, and every `lesson` reference exists;
- every number in a caption appears in that lesson's calc output, its table or its working.

Fix every error, and read every warning.

## Step 4: Build the studio page

Run the Artifact tool's `quickstart` (intent `other`) or load artifact-design for the page contract. Then:

- Write the app in JSX and bundle it with esbuild into one IIFE.
- Load React 18 UMD from cdnjs with an exact version.
- Inline the bundle and the kit JSON into a single HTML page. The web-artifacts-builder skill also works if it's available.
- With no Artifact tool (in Claude Code, say), deliver the same self-contained HTML file alongside the PDFs.

**Timeline engine.** Everything on screen is a pure function of time T (ms at 1x), so scrubbing works both ways. Compile each lesson once:

- **Step lengths:** `dur`, or 1.8 s plus 0.29 s per caption word (at least 2.6 s, or 3.4 s with flying chips). Keep cumulative starts and a total.
- **Walking the steps:**
  - `cells` overrides accumulate.
  - `show` and `strike` record their first step, and `always` lines show from the start.
  - `reveal` records each chart layer's first step; a layer that no step reveals is always shown.
  - `fly` records a chip and fills its target slot with a copy. The chip's text is the cell's current text, or the source slot's value for `@slot`.
  - `calc` fills a slot with a calculated value. Filling a slot also shows its line.
- **Within a step** (progress t from 0 to 1):
  - Chips leave at 0.10, staggered 0.06 each, and land by 0.58.
  - A copied slot shows its value from 0.62, and a calculated one pops at 0.32.
  - Copied fills are blue and calculated ones green.
- **Playback:** requestAnimationFrame advances T by dt times speed and stops at the end, with Replay and "Next lesson" overlays.

**Rendering:**

- **Facts table:** highlights, persistent strikes, overridden cells, and rows listed in `derived` styled differently.
- **Working board:**
  - Lines appear on their step, styled by kind.
  - Slots are dashed boxes showing their placeholder until filled.
  - Terms in `focus` glow.
- **Flying chips:** place them by measuring the source `[data-cell="r.c"]` and target `[data-slot=id]` relative to the stage, in a layout effect and on ResizeObserver, along an eased arc.
- **Chart:** a small SVG chart whose layers fade in on their reveal step.
- **Caption bar:** stack every step's caption in one grid cell and show only the current one, so the height never jumps. Add an `aria-live` line for screen readers.
- **Controls:** restart, previous and next step, play, a segmented scrubber (pointer drag), speeds 0.5 to 2, step-number chips, and keys (space or k, the arrows, but not while typing).
- **Layout:** facts on the left, working on the right, chart as a third column when wide, everything stacked below about 700px. The lesson list is a sidebar on desktop and a select on phones.
- **Progress:** "Mark as understood" saved in localStorage, wrapped in try/catch.

**Other tabs:**

- **Start here:** facts with sources, scope in and out, the time plan, the answer template with a weak and a strong example, likely questions linked to lessons, and common mistakes.
- **Practice:** timed questions with a draft box and revealable model answers, plus the quiz with explanations.
- **Memory sheet:** flashcards with shuffle, every formula, the tables and the traps.
- **Workbook:** previews and download buttons.

**Narration (device voice).** Speak each step's caption as it starts:

- Make the caption speakable first:
  - strip `**`;
  - turn `÷ × − = → ≈` into words;
  - read "$1.13" as "1 dollar and 13 cents";
  - read "1,150.44" as "1,150 point 4 4".
- The voice rate follows the speed.
- Hold the step's end until the utterance finishes, giving up after a few seconds if it stalls.
- Cancel on pause or jump.

**Theme:**

- Define colour tokens on `:root`.
- Redefine them under `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` and under `:root[data-theme="dark"]`.
- Use display, body and mono fonts, with mono for the numbers.

**Publishing:**

- Publish the PDFs and previews as supporting `files`, with `capabilities: {downloads: true}` (load artifact-capabilities first), and save through `claude.use("downloads")`.
- When that returns null (public links, signed-out viewers), render the same button as a plain `<a href>` to the file.
- Remove Google Fonts links before inlining, then re-add them.
- Keep the `<title>` in the first 8 KB.
- On republish, omit `capabilities` and `files` to keep them.

**Check with Playwright** before publishing:

- Load the page and open a lesson.
- Jump to a step with flying chips, play for about 1 s, and screenshot mid-flight.
- Repeat at 1440, 1024 and 390 wide, in light and dark.
- Confirm there are no page errors.

## Step 5: The PDFs

Build HTML in Python and print with Playwright Chromium (`page.pdf({preferCSSPageSize:true, printBackground:true, outline:true, tagged:true})`); if the browser is missing, install it with `npx playwright install chromium`. Get fonts offline with `npm i @fontsource/...`, used through `@font-face` with `file://` URLs.

**Workbook, iPad landscape:**

- Page: `@page { size: 11in 8.25in; margin: 0 }`; `.page{width:11in;height:8.25in;padding:.42in .5in .36in;display:flex;flex-direction:column;overflow:hidden;page-break-after:always}`.
- Left column 3.05in (facts table, trap, say-it-in-words lines, scratch space); right column the working.
- `.col>*{flex-shrink:0}`, so only `.scratch` shrinks. Tables use `table-layout:fixed; overflow-wrap:anywhere`.
- Formula rows: a green step badge ("Step 4-5") plus a 10pt mono line where each `[label]` is a dashed write-in box. Badge numbers must equal the video's step numbers.
- Order: cover with a clickable checklist, formula recall before, then per lesson a follow-along page and a Your turn page, then practice with writing space, recall after, and an answer key (named `@page key`, 3 columns, `break-inside:avoid`).
- Check every `.page` has `scrollHeight <= clientHeight` and every scratch area keeps at least 40px. Fix overflow by trimming, or split a tall lesson over two pages. Look at a montage of a few pages rendered with `pdftoppm`.

**Pocket card:** two pages at `@page{size:2.5in 3.5in}`. Each row is a 5pt grey label over a 6.4pt mono formula, with hairline dividers and a traps strip on each side, and no overflow. Users print it double-sided at Actual size, flip on the long edge and trim.

**Aid sheet**, only if students may bring one: a double-sided 8.5 x 11 sheet with every in-scope formula, the tables and the traps, and note space on side 2.

Make previews with `pdftoppm -r 72 -jpeg`, and deliver the PDFs as files as well as on the Workbook tab.

## Step 6 (optional): natural recorded voices

Device voices sound robotic. For human-sounding narration, record each step with the free Kokoro-82M model on the CPU.

**Setup:**

- `pip install kokoro-onnx==0.6.1 soundfile numpy`.
- Get `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the kokoro-onnx GitHub releases (`model-files-v1.0`).
- `Kokoro(model, voices).create(text, voice='af_heart', speed=s, lang='en-us')` returns the samples at 24 kHz. `af_heart` is a warm female voice and `am_michael` a calm male one.

**Scripts, one per step, written for the ear:**

- same meaning and exact numbers as the caption;
- short sentences, with natural "So," and "Now,";
- slide references dropped and symbols said in words;
- emphasis from sentence shape, not capitals;
- a `~` marks the result, and `...` marks a lead-in.

**Normalize before synthesis** (test doubtful text with `kokoro_onnx.tokenizer.Tokenizer().phonemize(text, 'en-us')`):

- "$1.13" becomes "1 dollar and 13 cents";
- "1,150.44" becomes "1,150 point 4 4";
- years: "2024" becomes "20 24", even before punctuation;
- decades: "1950s" becomes "nineteen fifties";
- digit plurals: "2s" becomes "twos";
- a mid-sentence letter A becomes "eh";
- μ becomes "mew";
- symbols become words;
- acronyms stay in capitals, so the engine spells them.

**Recording:**

- Synthesize sentence by sentence: speed 0.97 normally, 1.0 for a lead-in and 0.91 for the result.
- Put 0.34 s between sentences, 0.28 s after a lead-in, and 0.42 s before a result or a "So...".
- Master each lesson as one piece with ffmpeg: `highpass=f=70`, `acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120`, two-pass `loudnorm` (I=-16, TP=-1.5, linear), then a limiter.
- Cut it back into one 48 kbps mono MP3 per step.
- Rendering runs at about 0.6x real time on 2 CPUs, roughly 30 to 45 minutes per voice for a 250-step course.

**Publishing:**

- An artifact version holds at most 511 files (255 per publish), so one voice per course fits.
- The player fetches each step's file whole into a `blob:` URL, plays it on one shared `<audio>` element first started from a tap (iOS needs that), and makes each step last as long as its recording plus 0.6 s.
- It prefetches the next step, and falls back to the device voice if a file fails.
- Test playback in the published page; if the host blocks it, keep the device voice.

## Before calling it done

- **Numbers:** re-run from the calc scripts.
- **Scope:** matches the announcement.
- **Links:** every lesson link resolves.
- **PDFs:** the overflow check passes and the step numbers match the videos.
- **Page:** checked at three widths in light and dark.
- **Downloads:** work for the user.

## Final reply

Keep it short:

- What each deliverable is.
- How to use it: download the workbook first, play each lesson at 0.75x with its page open, then do the practice, then the memory sheet the night before.
- Honest limits, such as built from the slides rather than the textbook, and anything untested.

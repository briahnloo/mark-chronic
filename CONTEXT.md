# Context for the local Claude session

You are picking up a Handshake Project Mark task for bloo. Read this file, TASK_PLAN.md and scan_chronic.py in full before running anything.

## The program (Handshake Project Mark)

The fellow (bloo) builds one analytical task that frontier models get wrong. A task is three things: a prompt, one ZIP of real input files, and 1 to 3 golden output files. Pay is a flat $800 per approved task. The fellow submits on Handshake; you never do.

**Pass bar.** The platform runs two models, and their average rubric score must be under 50%, with at least one model clearly stumped. The rubric has 25+ criteria and is generated automatically from the prompt and golden files; nobody edits it. Weighting is about:
- 30–40% on the recommendation and its critical parts;
- 5–10% on following instructions;
- about 55% on the supplementary asks.

**Inputs (the ZIP).**
- 10+ files in 3+ formats, with at least one table of 10,000+ rows.
- The recommendation must need a join of 2+ tables.
- Every file is real and license-clean, with its source URL, pull date and license recorded.
- No LLM-generated documents and no padding: removing any file must break the answer.
- Any rule or definition the answer needs must be inside the package.

**Prompt.**
- Natural prose, at most 2,500 characters.
- One decision, committed (no hedging allowed), and 1 to 3 named deliverable files, each with a few hard asks.
- It must never name the method, the trap or the decisive file, and must never hint that a metric is misleading.
- Vague on method, precise on the answer, and needs no outside knowledge.

**Golden files.** Exactly the files the prompt names.
- Lead with the recommendation and say what it rejects, then give one labelled answer per ask.
- One consistent set of numbers, every number traceable to the input files, and at least one trap refused, stated as a decision.
- They must look like real work output: no chat intro, no disclaimers, no placeholders, nothing extra. Reviewers send back goldens that look LLM-written.

**Difficulty must come from honest data.** Planted defects are banned: flipped numbers, mislabels, hidden time-zone shifts and similar.

Valid traps are documented features of real data that a careless analyst misreads. Measured top failures for models:
- taking the population a flag or filter suggests;
- counting file rows instead of the real unit;
- using a ready-made measure;
- treating a binding limit only as a risk;
- beating the obvious trap but missing the quiet one;
- stopping at a close-but-inexact match.

## What already happened (don't repeat it)

The first task tried was a PM2.5 exceptional-events decision on EPA data. A run on real data on bloo's Mac killed it, for three reasons:
- the concurred vs. non-concurred event split it depended on exists only in EPA's annual files, not the daily ones;
- no U.S. county produced the YES case with two or more sites;
- on real data, almost none of its shortcuts changed the answer.

It is shelved, so don't touch ~/mark-pm25.

The lesson for this task: before building anything, prove on the real files that every field the traps depend on exists, and that the traps actually change the answer for the chosen carrier. If the real data doesn't support the task, stop and say so. Don't bend the design to fit.

## This task: chronic flight delays (14 CFR 399.81)

**Stakeholder and decision.** A carrier's compliance lead asks which of the carrier's 2025 flights DOT could cite under the chronic-delay rule, and in what order to fix them: the most passengers on those markets first. DOT fined JetBlue under this rule in its December 2024 consent order. TASK_PLAN.md has the full design, the draft prompt and the steps. scan_chronic.py implements the rule and the shortcut variants, but it has only ever run on synthetic data.

**The rule.** Confirm every part of it against the reg text and the JetBlue order. Don't take it from here.
- A "flight" is all of a carrier's flights in one origin-destination market whose scheduled departure is within 30 minutes of the most frequent scheduled departure time. That definition comes from the JetBlue order, so several flight numbers can be one flight.
- A flight is chronically delayed in a month if it operated 10 or more times and arrived more than 30 minutes late more than 50% of the time, with cancellations counting as late.
- A violation is more than four consecutive chronically delayed months, so five or more.

**Traps, all honest features of the BTS data and the rule.**
- **Unit:** grouping by flight number instead of market plus departure window.
- **Ready-made flag:** using BTS ArrDel15, which is a 15-minute flag and blank for cancellations.
- **Cancellations:** dropping cancelled flights or counting them as on time.
- **Streak length:** counting 4 consecutive months as a violation instead of more than 4.
- **Control:** never checking the method against the flights DOT actually named for JetBlue in 2023.

**Deliverables** (from the draft prompt in TASK_PLAN.md section 5):
- `exposure_register.csv`;
- `chronic_delay_timeline.png`;
- `exposure_memo.pdf`, a 1 to 2 page compliance memo.

**Package.** The details are in TASK_PLAN.md section 4.
- The 2025 monthly BTS on-time files, filtered to the chosen carrier, keeping every column and copying kept lines byte-for-byte.
- The 2023 JetBlue months the order covers. Use only the months the control needs, because this is the likeliest place for a padding comment.
- The BTS readme.html, the eCFR 399.81 page as a PDF, and the JetBlue order PDF.
- The 2025 T-100 domestic segment data.
- provenance.csv, giving URL, pull date, license, transform, row count and SHA-256 for every file.

**Downloads.**
- BTS PREZIP files: if a plain Python download gets refused, use curl with a browser user agent.
- T-100 has no direct-file URL. If you can't fetch it, give bloo the exact TranStats download page and the fields to tick, then wait for the file.
- Never fabricate or reconstruct a source file.

## How to work

- Stay in this folder and use a venv. Don't search the rest of the disk.
- **Validate first.** Run the control on B6 for 2023 and reproduce exactly the flights the JetBlue order names. If the method doesn't match, fix it from the order and the reg text, never by tuning toward the answer, and rerun. If it still can't match, stop and report.
- **Carrier choice.** Use the criteria in TASK_PLAN.md step 3:
  - 2 to 6 violating flights;
  - 3 or more traps that change the answer, ideally including the flight-number and ArrDel15 traps;
  - DETERMINISM clean;
  - exactly one near-miss run of 4 months;
  - no two flagged flights sharing a market.

  If no carrier qualifies, stop and show bloo the best candidates rather than lowering the bar.
- Speed: cluster() loops in Python. Make it fast if a full scan is too slow, but keep its behaviour identical and test that it is.
- **Golden files.** Build all three from one script run so the numbers agree. The memo should read like a real compliance memo written by a person: no chat tone, no disclaimers, no headings for their own sake.
- Fill the carrier into the prompt, keep it at or under 2,500 characters, and save it as prompt.md.
- **Final state:** submission/ holds only inputs.zip and the three golden files, and this folder holds prompt.md and READY.md. READY.md is the rule-by-rule pass/fail audit, with evidence for each rule.
- Never submit on Handshake; bloo does that.

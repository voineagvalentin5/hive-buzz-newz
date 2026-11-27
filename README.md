---
title: Hive Buzz Newz
emoji: 🐝
colorFrom: yellow
colorTo: gray
sdk: static
app_file: index.html
pinned: false
short_description: Daily source-checked news from Codex Hive
---

# Hive Buzz Newz

Daily source-checked news editions from Codex Hive Labs.

The public static site is [newz.codex-hive.com](https://newz.codex-hive.com).
Each dated folder contains an edition. The root `index.html` serves the latest
edition and `archive/index.html` lists all published editions.

Run `python3 site/build.py /path/to/YYYY-MM-DD.json` to render a daily edition
into `site/out/`, together with the existing archive and shared assets.

World Temperature readings live in `site/world-temperature.json` under
method v1. The original Nov 10–26 series is transcribed from the supplied
chart. Add a dated score from the same method and set `edition` to `true` for a
published edition or `false` for a reconstruction. An edition without a
dated reading shows an empty gauge. The trend displays readings through the
edition date.

To feature sourced stories beside the gauge, add a `site/signals/YYYY-MM-DD.json`
file using an existing file as a template. Each signal must match one story
headline exactly. Optional `title` and `description` fields set the signal card
copy. The dashboard uses the NASA EPIC Earth image from the
[Codex Hive Labs hub](https://github.com/voineagvalentin5/codex-hive-site/blob/main/docs/assets/hub/earth-epic.webp).

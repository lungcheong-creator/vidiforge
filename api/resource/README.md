# API `resource/` Directory

## `songs/` — Background Music

Drop CC0 / royalty-free `.mp3`, `.wav`, `.ogg`, `.m4a`, or `.flac` files here. They will be picked randomly when a task runs with `BGMConfig.enabled=true` and `random=true`.

**Recommended tracks (CC0):**

- <https://pixabay.com/music/search/genre/ambient/>
- <https://freemusicarchive.org/genre/ambient/>
- <https://commons.wikimedia.org/wiki/Category:CC-licensed_music_files>

Place 3-10 files in this directory. Filenames should be short and descriptive — they will appear in logs.

## `fonts/` — Subtitle Fonts

Optional fallback fonts. By default, FFmpeg uses `Noto Sans CJK SC` (installed in the Docker image). Drop additional `.ttf` / `.otf` files here to support custom subtitle styles.

## `templates/` — Subtitle Style Templates

ASS subtitle templates used by the subtitle service:

- `subtitle_default.ass` — Modern sans-serif, white text with black outline, bottom-center aligned.
- `subtitle_editorial.ass` — Fraunces serif, italic, terracotta outline. Editorial / brand-friendly look.

The frontend lets users override font, size, color, position, and outline. Templates here are useful as defaults or as references.
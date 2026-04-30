# Workspace Config

All skills that read from or write to local directories (transcript files, prep briefs, etc.) resolve those paths through a shared **workspace config** before falling back to the current working directory. This lets the same skill work for anyone without hardcoded paths.

## Location

```
${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json
```

This file lives outside the skill install directory and is never committed to the repo.

## Schema

```json
{
  "workspace_dir": "/absolute/path/to/your/workspace",
  "transcript_dir": "/absolute/path/to/your/workspace/transcripts",
  "prep_output_dir": "/absolute/path/to/your/workspace/1on1-preps",
  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

All fields are optional. See `workspace.example.json` for a template.

## Resolution order for any local path

1. Explicit path in the workspace config field (e.g. `transcript_dir`)
2. Derived from `workspace_dir` using the conventional subdirectory name (e.g. `<workspace_dir>/transcripts`)
3. Current working directory (or a conventional subdirectory of it) — the safe default for anyone who has not configured a workspace

Skills must announce the resolved path to the user at the start of any phase that will write files, before writing.

## Which skills use this

| Skill | Fields read |
|---|---|
| `zoom-transcript-sync` | `transcript_dir` |
| `1on1-prep` | `transcript_dir`, `prep_output_dir` |

## Setting up workspace config

Run the init phase of any skill that writes local files — it will offer to bootstrap the workspace config from your answers. You can also write the file directly using `workspace.example.json` as a starting point:

```bash
cp ~/.claude/skills/_shared/workspace.example.json \
   "${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json"
# then edit the file with your actual paths
```

## Gitignore note

The workspace config lives in `~/.config/` and is never inside the skill repo. No gitignore entry is needed. The example file committed to the repo (`workspace.example.json`) contains no real paths.

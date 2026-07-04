# Binary Artifacts Omitted

The source folders contain many generated assets and review images. They were not copied into this bundle.

Omitted categories:

- Blender scenes: `*.blend`
- GLB exports: `*.glb`
- FBX exports: `*.fbx`
- OBJ/MTL exports: `*.obj`, `*.mtl`
- Validation/contact-sheet PNGs: `*.png`
- Unity generated runtime directories: `Library/`, `Temp/`, `Obj/`, `Build/`, `Builds/`, `Logs/`, `UserSettings/`

Reason:

- The user request is to summarize/package code written across Codex sessions.
- The active repo already treats screenshots/reports as review gates, but these binaries should be published as release artifacts when needed, not copied wholesale into a code archive branch.

Important:

- JSON validation reports and Markdown handoff notes are included.
- Local absolute source paths are recorded in `README.md` and `INVENTORY.md` for provenance.
- The bundle does not modify or replace `semantic_layer_v8`.


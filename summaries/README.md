# summaries/

Auto-generated markdown summaries, one per PDF in `documents/`. Directory structure mirrors `documents/`.

Also contains `manifest.json`, which maps each BibTeX key to the absolute paths of its source PDF and summary file. This file is consumed by `/build-html`.

Do not edit files here manually — regenerate by re-running `/summarize-documents`.

## Note on portability

`manifest.json` stores absolute filesystem paths generated at summarization time. These paths are machine-specific — do not move the repository after running `/summarize-documents`, as the paths will no longer resolve. If you move the repo, delete `manifest.json` and re-run `/summarize-documents` to regenerate it.

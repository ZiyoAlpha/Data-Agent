# Security and privacy

This repository is a public-safe starter, not a system for storing secrets.

- Keep API keys only in `.env` or environment variables. `.env` is ignored by Git.
- Keep real knowledge files out of the public repository.
- The generated SQLite index is ignored because it contains searchable derivatives of local documents.
- Retrieved passages are sent to the configured OpenAI API endpoint when you chat.
- The server binds to localhost by default. Review authentication and network controls before exposing it elsewhere.
- Application logs intentionally omit prompts, retrieved passages, chat history, and credentials.

Before publishing a fork, run `python scripts/check_sensitive.py` and inspect `git diff --cached` manually.


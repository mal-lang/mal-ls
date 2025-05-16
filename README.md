# MAL Language Server
`mal-ls` is a language server for [MAL](https://github.com/mal-lang).

## Contributing
The project uses [`uv`](https://docs.astral.sh/uv/) as the main project manager and [`ruff`](https://docs.astral.sh/ruff/) for linting/formatting. `ruff` can be installed via uv as native via `uv tool install ruff` or use it as the dev-dependency its specified as via `uv run ruff <command>`.

To run the server, use the command `uv run mal-ls -- <options>`.

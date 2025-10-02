# MAL Language Server
`mal-language-server` is a language server for [MAL](https://github.com/mal-lang).

## General
The project uses [`uv`](https://docs.astral.sh/uv/) as the main project manager and [`ruff`](https://docs.astral.sh/ruff/) for linting/formatting. `ruff` can be installed via uv as native via `uv tool install ruff` or use it as the dev-dependency its specified as via `uv run ruff <command>`.

Before running the project or editing files, `uv` must download the required packages. For
that, use `uv sync`.

## Running

To run the server, use the command `uv run malls -- <options>`. 

There are two main ways of interacting with the server, via files or TCP. This can be configured
via the start-up options. Obviously, they are mutually exclusive, meaning only one can be used per
server instance.

1. *Files*: for this option, run `uv run malls --stdio`, which defaults to standard input and output.
To configure what files are used to read from/write to, run `uv run malls --stdio -o OUT_FILE_PATH -i IN_FILE_PATH`.

2. *TCP*: for this option, run `uv run malls --tcp`, which starts the server on `localhost` with port
`8080`. To use another host or port, add those options with `uv run malls --tcp --host HOST -p PORT`.

Other start-up arguments, namely related to logging, can be found using `uv run malls -h`

## Installation
### NeoVim
1. Install the server via pip, for example locally:
    ```sh
    pip install /folder/path/of/pyproject
    ```
    > [!NOTE]
    > Use `-e` to install it in editable/development mode, which updates the installation live.
2. Configure your NeoVim LSP client, for example :
    `init.lua`
    ```lua
    vim.lsp.config['malls'] = {
        cmd = { "malls", "--stdio" },
        filetypes = { 'mal' },
    }
    vim.lsp.enable('malls')
    ```
    > [!NOTE]
    > Tested for NeoVim v0.11.1

## CI/CD

Packages are published via UV on ubuntu to PyPI on tags pushed to the repository.

Tests are ran with pytest and pytest-xdist on ubuntu and macos. Additionally formatting and linting checks are ran with ruff.

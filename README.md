# superfences-ps1

MkDocs plugin that adds a configurable shell-prompt SuperFences fence with copy-safe PS1 prompt characters.

The plugin registers a custom [SuperFences](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/)
fence (default name `shell-ps1`) that prepends a configurable PS1 prompt character to every command line. The prompt is
rendered visibly in the documentation but is **never copied to the clipboard** and is **never selected by mouse** —
the plugin injects a `data-copy` attribute with the raw source text so Material for MkDocs' copy button bypasses the
prompt spans entirely, and `user-select: none` CSS is injected to prevent mouse selection of the prompt.


## Installation

```shell
pip install superfences-ps1
```

Or with uv:

```shell
uv add superfences-ps1
```


## Requirements

- `pymdownx.superfences` must be listed under `markdown_extensions` in `mkdocs.yaml`


## Usage


### `mkdocs.yaml` configuration

```yaml
plugins:
  - superfences-ps1:
      fence_name: shell-ps1    # fence language identifier (default: shell-ps1)
      prompt_char: "$"         # PS1 prompt character prepended to each line (default: $)
      prompt_color: "#5fb3b3"  # optional CSS color for the prompt character

markdown_extensions:
  - pymdownx.superfences
```


### Writing shell fences

Use the configured `fence_name` in your markdown:

````markdown
```shell-ps1
echo "Hello, world!"
ls -la
```
````

The plugin prepends the prompt character to each non-empty line before passing the content to Pygments. The rendered
output shows the prompt visually, but the copy button and mouse selection only grab the commands themselves.


## Configuration options

| Option         | Type            | Default     | Description                                              |
|----------------|-----------------|-------------|----------------------------------------------------------|
| `fence_name`   | `str`           | `shell-ps1` | The fence language identifier used in markdown           |
| `prompt_char`  | `str`           | `$`         | The PS1 prompt character prepended to each command line  |
| `prompt_color` | `str` or `None` | `None`      | Optional CSS color value for the rendered prompt         |

> [!NOTE]
> `prompt_char` must be one of `$`, `%`, or `#` — the only characters Pygments' `BashSessionLexer` recognises as
> prompt markers, emitting them as `Generic.Prompt` (`.gp`) tokens. Any other value will cause a `PluginError` at
> build time. `>` in particular is the continuation prompt (`_ps2`) and causes the entire line to be tokenised as
> `Generic.Output` (`.go`), which would treat the command text as output.


## How it works

1. On `on_config`, the plugin validates that `pymdownx.superfences` is present and injects a custom fence formatter
   into `mdx_configs["pymdownx.superfences"]["custom_fences"]`.
2. When MkDocs processes a page containing a fenced code block with the configured `fence_name`, SuperFences calls
   the injected formatter.
3. The formatter prepends `<prompt_char> ` to every non-empty line, then passes the result to Pygments using the
   `console` (`BashSessionLexer`) lexer. Pygments wraps the prompt in `<span class="gp">` and the command in
   additional token spans.
4. The formatter injects a `data-copy` attribute on the wrapper `<div>` containing the raw (un-prompted) source.
   Material for MkDocs' copy button reads `data-copy` in preference to `innerText`, so the prompt is never included
   in clipboard content.
5. On `on_post_page`, the plugin injects a `<style>` block into each page's `<head>` with `user-select: none` on
   `.gp` spans, preventing mouse selection of the prompt. If `prompt_color` is configured, the color rule is
   combined into the same `<style>` block.


## Development

```shell
git clone https://github.com/dusktreader/superfences-ps1
cd superfences-ps1
uv sync
make qa/full
```


## License

MIT — see [LICENSE.md](LICENSE.md).

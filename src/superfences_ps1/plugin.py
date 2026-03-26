import html
from collections.abc import Callable
from typing import override

import markdown
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.config.config_options import Optional, Type
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.pages import Page
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name

log = get_plugin_logger(__name__)

DEFAULT_FENCE_NAME = "shell-ps1"
DEFAULT_PROMPT_CHAR = "$"
DEFAULT_PROMPT_COLOR = "#89b0c2"
VALID_PROMPT_CHARS = ("$", "%", "#")

_SUPERFENCES_KEY = "pymdownx.superfences"

# Type alias for a superfences custom-fence formatter callable.
# The signature mirrors pymdownx.superfences.fence_code_format.
FormatterFn = Callable[..., str]

# Type alias for the loosely-typed superfences configuration dicts that
# come back from MkDocs' mdx_configs mapping (no stubs available).
_FenceDict = dict[str, object]
_SuperfencesCfg = dict[str, object]
_MdxConfigs = dict[str, object]


class ShellPromptConfig(Config):
    fence_name: Type[str] = config_options.Type(str, default=DEFAULT_FENCE_NAME)
    prompt_char: Type[str] = config_options.Type(str, default=DEFAULT_PROMPT_CHAR)
    prompt_color: Optional[str] = config_options.Optional(config_options.Type(str))


class ShellPromptPlugin(BasePlugin[ShellPromptConfig]):
    """
    MkDocs plugin that adds a configurable shell-prompt SuperFences fence.

    The fence prepends `<prompt_char> ` to every non-empty line so that
    Pygments' `BashSessionLexer` (`console`) emits a `Generic.Prompt`
    token (`.gp` CSS class) for the prompt portion. A `data-copy` attribute
    is injected on the wrapper `<div>` containing the raw (un-prompted) source
    text so that Material for MkDocs' copy button uses that value instead of
    reading `innerText`, keeping the prompt out of the clipboard.

    Requires `pymdownx.superfences` in `markdown_extensions`.

    Configuration (`mkdocs.yaml`):

    ```yaml
    plugins:
      - superfences-ps1:
          fence_name: shell      # fence language identifier (default: shell)
          prompt_char: "$"       # prompt character prepended to each line (default: $)
          prompt_color: "#89b0c2" # CSS color for the prompt character (default: #89b0c2)
    ```
    """

    def _make_formatter(self, prompt_char: str) -> FormatterFn:
        """Return a SuperFences-compatible formatter function for the given prompt char."""

        def formatter(
            source: str,
            _language: str,
            css_class: str,
            _options: dict[str, object],
            _md: markdown.Markdown,
            **_kwargs: object,
        ) -> str:
            prompted = "\n".join(f"{prompt_char} {line}" if line.strip() else line for line in source.splitlines())
            lexer = get_lexer_by_name("console", stripall=False)
            fmt = HtmlFormatter(
                cssclass=f"highlight {css_class}".strip(),
                wrapcode=True,
            )
            rendered: str = highlight(prompted, lexer, fmt)
            # Inject data-copy on the wrapper <div> with the raw (un-prompted) source
            # text. Material for MkDocs' copy button reads this attribute in preference
            # to innerText, so the prompt character is never included in the clipboard.
            copy_text = html.escape(source.rstrip("\n"), quote=True)
            return rendered.replace("<div ", f'<div data-copy="{copy_text}" ', 1)

        return formatter

    @override
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Inject the shell-prompt fence into the superfences custom_fences list."""
        fence_name = self.config.fence_name
        prompt_char = self.config.prompt_char

        ext_names: set[str] = set()
        for ext in config.get("markdown_extensions", []):
            if isinstance(ext, str):
                ext_names.add(ext)
            elif isinstance(ext, dict):
                ext_names.update(ext.keys())

        if prompt_char not in VALID_PROMPT_CHARS:
            raise PluginError(
                f"[superfences-ps1] Invalid prompt_char {prompt_char!r}. "
                f"Must be one of: {', '.join(repr(c) for c in VALID_PROMPT_CHARS)}. "
                "Other characters are not recognised as prompts by Pygments' BashSessionLexer."
            )

        if _SUPERFENCES_KEY not in ext_names:
            raise PluginError(
                f"[superfences-ps1] '{_SUPERFENCES_KEY}' must be listed under 'markdown_extensions' in mkdocs.yaml."
            )

        mdx_configs: _MdxConfigs = config.get("mdx_configs", {})
        superfences_cfg: _SuperfencesCfg = mdx_configs.get(_SUPERFENCES_KEY, {})
        custom_fences: list[_FenceDict] = superfences_cfg.get("custom_fences", [])

        existing_names = {f["name"] for f in custom_fences}
        if fence_name in existing_names:
            log.warning(
                "Fence name '%s' is already registered in superfences; skipping injection.",
                fence_name,
            )
            return None

        custom_fences.append(
            {
                "name": fence_name,
                "class": fence_name,
                "format": self._make_formatter(prompt_char),
            }
        )
        superfences_cfg["custom_fences"] = custom_fences
        mdx_configs[_SUPERFENCES_KEY] = superfences_cfg
        config["mdx_configs"] = mdx_configs

        log.debug(
            "Registered shell-prompt fence '%s' with prompt char '%s'.",
            fence_name,
            prompt_char,
        )
        return None

    @override
    def on_post_page(self, output: str, /, *, page: Page, config: MkDocsConfig) -> str:
        """
        Inject prompt CSS into each page's <head>.

        Always injects `user-select: none` on `.gp` so the prompt character is excluded from mouse text selection.
        Also injects a `color` rule when `prompt_color` is configured.
        """
        if "</head>" not in output:
            return output

        prompt_color = self.config.prompt_color or DEFAULT_PROMPT_COLOR
        rules = "user-select: none;"
        if prompt_color:
            rules += f" color: {prompt_color};"
        style = f"<style>.highlight .gp {{ {rules} }}</style>"
        return output.replace("</head>", f"{style}\n</head>", 1)

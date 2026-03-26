"""Tests for superfences_ps1.plugin."""

import logging
import re
from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError

from superfences_ps1.plugin import FormatterFn, ShellPromptPlugin, VALID_PROMPT_CHARS, DEFAULT_PROMPT_COLOR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mkdocs_config(
    extensions: list[str | dict[str, object]] | None = None,
    mdx_configs: dict[str, object] | None = None,
) -> MkDocsConfig:
    """Return a minimal MkDocsConfig-like dict for testing."""
    config: dict[str, object] = {
        "markdown_extensions": extensions or [],
        "mdx_configs": mdx_configs or {},
    }
    return cast(MkDocsConfig, cast(object, config))


def _make_plugin(
    fence_name: str = "shell",
    prompt_char: str = "$",
    prompt_color: str | None = None,
) -> ShellPromptPlugin:
    """Return a loaded ShellPromptPlugin instance."""
    plugin = ShellPromptPlugin()
    _ = plugin.load_config(
        {
            "fence_name": fence_name,
            "prompt_char": prompt_char,
            "prompt_color": prompt_color,
        }
    )
    return plugin


# ---------------------------------------------------------------------------
# on_config — extension name detection
# ---------------------------------------------------------------------------


def test_on_config__detects_string_extension():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)  # should not raise


def test_on_config__detects_dict_extension():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=[{"pymdownx.superfences": {"custom_fences": []}}])

    _ = plugin.on_config(config)  # should not raise


def test_on_config__detects_mixed_extensions():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=["admonition", {"pymdownx.superfences": {"custom_fences": []}}])

    _ = plugin.on_config(config)  # should not raise


def test_on_config__raises_when_extensions_empty():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=[])

    with pytest.raises(PluginError, match="pymdownx.superfences"):
        plugin.on_config(config)


# ---------------------------------------------------------------------------
# ShellPromptPlugin config
# ---------------------------------------------------------------------------


def test_plugin_default_config():
    plugin = ShellPromptPlugin()
    _ = plugin.load_config({})

    assert plugin.config.fence_name == "shell-ps1"
    assert plugin.config.prompt_char == "$"
    assert plugin.config.prompt_color is None  # default applied at render time


def test_plugin_custom_config():
    plugin = ShellPromptPlugin()
    _ = plugin.load_config({"fence_name": "cmd", "prompt_char": "%", "prompt_color": "#ff0000"})

    assert plugin.config.fence_name == "cmd"
    assert plugin.config.prompt_char == "%"
    assert plugin.config.prompt_color == "#ff0000"


# ---------------------------------------------------------------------------
# on_config — validation
# ---------------------------------------------------------------------------


def test_on_config__raises_when_superfences_missing():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=[])

    with pytest.raises(PluginError, match="pymdownx.superfences"):
        plugin.on_config(config)


def test_on_config__raises_when_invalid_prompt_char():
    plugin = _make_plugin(prompt_char=">")
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    with pytest.raises(PluginError, match="prompt_char"):
        plugin.on_config(config)


@pytest.mark.parametrize("prompt_char", VALID_PROMPT_CHARS)
def test_on_config__accepts_all_valid_prompt_chars(prompt_char: str):
    plugin = _make_plugin(prompt_char=prompt_char)
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)  # should not raise


# ---------------------------------------------------------------------------
# on_config — fence injection
# ---------------------------------------------------------------------------


def test_on_config__injects_fence():
    plugin = _make_plugin(fence_name="shell", prompt_char="$")
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    names = [f["name"] for f in fences]
    assert "shell" in names


def test_on_config__fence_has_correct_class():
    plugin = _make_plugin(fence_name="shell")
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    fence = next(f for f in fences if f["name"] == "shell")
    assert fence["class"] == "shell"


def test_on_config__fence_format_is_callable():
    plugin = _make_plugin()
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    fence = next(f for f in fences if f["name"] == "shell")
    assert callable(fence["format"])


def test_on_config__custom_fence_name():
    plugin = _make_plugin(fence_name="powershell")
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])

    _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    names = [f["name"] for f in fences]
    assert "powershell" in names


def test_on_config__does_not_duplicate_existing_fence(caplog: pytest.LogCaptureFixture):
    plugin = _make_plugin(fence_name="shell")
    existing_fence: dict[str, object] = {
        "name": "shell",
        "class": "shell",
        "format": cast(Callable[..., str], lambda *a: ""),
    }
    config = _make_mkdocs_config(
        extensions=["pymdownx.superfences"],
        mdx_configs={"pymdownx.superfences": {"custom_fences": [existing_fence]}},
    )

    with caplog.at_level(logging.WARNING):
        _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    assert len([f for f in fences if f["name"] == "shell"]) == 1
    assert any("already registered" in record.message for record in caplog.records)


def test_on_config__preserves_existing_fences():
    plugin = _make_plugin(fence_name="shell")
    existing_fence: dict[str, object] = {
        "name": "mermaid",
        "class": "mermaid",
        "format": cast(Callable[..., str], lambda *a: ""),
    }
    config = _make_mkdocs_config(
        extensions=["pymdownx.superfences"],
        mdx_configs={"pymdownx.superfences": {"custom_fences": [existing_fence]}},
    )

    _ = plugin.on_config(config)

    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    names = [f["name"] for f in fences]
    assert "mermaid" in names
    assert "shell" in names


# ---------------------------------------------------------------------------
# formatter (via on_config + calling the injected formatter)
# ---------------------------------------------------------------------------


def _get_formatter(plugin: ShellPromptPlugin) -> FormatterFn:
    """Run on_config and return the injected formatter callable."""
    config = _make_mkdocs_config(extensions=["pymdownx.superfences"])
    _ = plugin.on_config(config)
    fences: list[dict[str, object]] = cast(
        list[dict[str, object]], config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    )
    return cast(FormatterFn, next(f for f in fences if f["name"] == plugin.config.fence_name)["format"])


def test_formatter__prepends_prompt_to_lines():
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello", "shell", "highlight", {}, MagicMock())

    # Pygments wraps the prompt in a <span class="gp"> token.
    assert 'class="gp"' in result
    assert "echo" in result


def test_formatter__custom_prompt_char():
    plugin = _make_plugin(prompt_char="%")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("ls -la", "shell", "highlight", {}, MagicMock())

    # The % prompt is emitted as a .gp token by BashSessionLexer.
    assert 'class="gp"' in result
    assert "%" in result


def test_formatter__empty_lines_not_prompted():
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello\n\necho world", "shell", "highlight", {}, MagicMock())

    # Both prompted lines appear in the HTML; blank lines pass through without a prompt.
    assert result.count('class="gp"') == 2


def test_formatter__returns_html():
    plugin = _make_plugin()
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hi", "shell", "highlight", {}, MagicMock())

    assert "<div" in result
    assert "</div>" in result


def test_formatter__gp_token_in_output():
    """Verify the .gp CSS class appears in rendered output (copy-safe prompt)."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello", "shell", "highlight", {}, MagicMock())

    assert 'class="gp"' in result


def test_formatter__data_copy_attribute_present():
    """data-copy on the wrapper div lets Material's JS skip innerText."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello", "shell", "highlight", {}, MagicMock())

    assert "data-copy=" in result


def test_formatter__data_copy_contains_raw_source():
    """data-copy value must be the original source, not the prompted version."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello", "shell", "highlight", {}, MagicMock())

    assert 'data-copy="echo hello"' in result


def test_formatter__data_copy_excludes_prompt():
    """data-copy must not contain the prompt character."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello", "shell", "highlight", {}, MagicMock())

    # Extract the data-copy value and confirm it has no prompt
    match = re.search(r'data-copy="([^"]*)"', result)
    assert match is not None
    assert "$" not in match.group(1)


def test_formatter__data_copy_multiline():
    """data-copy preserves newlines between commands."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter("echo hello\nls -la", "shell", "highlight", {}, MagicMock())

    assert 'data-copy="echo hello\nls -la"' in result


def test_formatter__data_copy_special_chars_escaped():
    """data-copy HTML-escapes characters that would break the attribute value."""
    plugin = _make_plugin(prompt_char="$")
    formatter: FormatterFn = _get_formatter(plugin)

    result: str = formatter('echo "hello world"', "shell", "highlight", {}, MagicMock())

    assert 'data-copy="echo &quot;hello world&quot;"' in result


# ---------------------------------------------------------------------------
# on_post_page
# ---------------------------------------------------------------------------


def test_on_post_page__always_injects_user_select_none():
    plugin = _make_plugin(prompt_color=None)
    output = "<html><head></head><body></body></html>"

    result = plugin.on_post_page(output, page=MagicMock(), config=MagicMock())

    assert "user-select: none" in result
    assert result.index("<style>") < result.index("</head>")


def test_on_post_page__injects_color_when_prompt_color_set():
    plugin = _make_plugin(prompt_color="#5fb3b3")
    output = "<html><head></head><body></body></html>"

    result = plugin.on_post_page(output, page=MagicMock(), config=MagicMock())

    assert "user-select: none" in result
    assert "color: #5fb3b3" in result


def test_on_post_page__no_color_rule_when_no_prompt_color():
    plugin = _make_plugin(prompt_color=None)
    output = "<html><head></head><body></body></html>"

    result = plugin.on_post_page(output, page=MagicMock(), config=MagicMock())

    assert f"color: {DEFAULT_PROMPT_COLOR}" in result


def test_on_post_page__no_injection_when_no_head_tag():
    plugin = _make_plugin(prompt_color="#ff0000")
    output = "<html><body></body></html>"

    result = plugin.on_post_page(output, page=MagicMock(), config=MagicMock())

    assert "<style>" not in result
    assert result == output


def test_on_post_page__injects_only_once():
    plugin = _make_plugin(prompt_color="#ff0000")
    output = "<html><head></head><head></head><body></body></html>"

    result = plugin.on_post_page(output, page=MagicMock(), config=MagicMock())

    assert result.count("<style>") == 1

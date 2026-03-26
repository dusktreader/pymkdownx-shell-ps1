# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## v0.1.0 - 2026-03-26

Initial release of the superfences-ps1 plugin featuring:

- **Shell-prompt fence**: Register a custom SuperFences fence (default name `shell-ps1`) that prepends a
  configurable PS1 prompt character to every command line
- **Copy-safe prompt**: Injects a `data-copy` attribute on the wrapper `<div>` with the raw (un-prompted) source
  text so that Material for MkDocs' copy button never includes the prompt in clipboard content
- **Mouse-selection-safe prompt**: Injects `user-select: none` CSS on `.gp` spans so the prompt character cannot
  be selected with the mouse
- **Configurable prompt char**: Default `$`; must be one of `$`, `%`, or `#` — the only characters Pygments'
  `BashSessionLexer` recognises as prompt markers
- **Optional prompt color**: Combines a `color` rule into the injected `<style>` block when `prompt_color` is set
- **Validation**: Raises `PluginError` if `pymdownx.superfences` is absent or if `prompt_char` is not a valid
  prompt character

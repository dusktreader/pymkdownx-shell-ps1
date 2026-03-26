"""
superfences-ps1 — MkDocs plugin that registers a SuperFences shell-prompt fence.

The fence prepends a configurable prompt character to each command line so that
Pygments emits a ``Generic.Prompt`` (``.gp``) token. Material for MkDocs strips
``.gp`` spans from the clipboard copy, so the prompt is visible but never copied.
"""

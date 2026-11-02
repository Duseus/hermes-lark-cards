"""Compatibility with the extracted progress mixin and limit-offer delivery wrapper."""
import ast
from pathlib import Path

import pytest
from hermes_sources import source_at

from hermes_lark_cards.patcher import Patcher, PatcherError
from hermes_lark_cards.split_gateway import GATEWAY_FILES


@pytest.fixture
def modern_tree(tmp_path):
    root = tmp_path / 'gateway'
    root.mkdir()
    (root / 'run.py').write_text(source_at('gateway/run.py'))
    for name in GATEWAY_FILES:
        source = source_at('gateway/' + name)
        if name == 'run_turn.py':
            source = source.replace('return await self._hmwa_deliver_turn_response(',
                                    'return await self._deliver_turn_response_then_limit_offer(')
        if name == 'run_turn_runner.py':
            node = next(n for n in ast.walk(ast.parse(source))
                        if isinstance(n, ast.FunctionDef) and n.name == 'progress_callback')
            lines = source.splitlines(keepends=True)
            progress = ''.join(lines[node.lineno - 1:node.end_lineno])
            (root / 'run_turn_progress.py').write_text('class ProgressMixin:\n' + progress)
            del lines[node.lineno - 1:node.end_lineno]
            source = ''.join(lines).replace('if delta_sinks:', 'if delta_sinks or self._approval_owner is not None:')
        (root / name).write_text(source)
    return root


def test_extracted_progress_install_roundtrip(modern_tree):
    original = {p: p.read_bytes() for p in modern_tree.glob('*.py')}
    patcher = Patcher(modern_tree / 'run.py')
    patcher.verify_target()
    assert {p: p.read_bytes() for p in original} == original
    patcher.apply()
    assert patcher.is_fully_patched()
    assert 'HERMES_LARK_TOOL_BEGIN' in (modern_tree / 'run_turn_progress.py').read_text()
    assert 'HERMES_LARK_TOOL_BEGIN' not in (modern_tree / 'run_turn_runner.py').read_text()
    assert '_deliver_turn_response_then_limit_offer(' in (modern_tree / 'run_turn.py').read_text()
    patcher.remove()
    assert {p: p.read_bytes() for p in original} == original


def test_missing_extracted_progress_fails_without_writes(modern_tree):
    (modern_tree / 'run_turn_progress.py').unlink()
    original = {p: p.read_bytes() for p in modern_tree.glob('*.py')}
    with pytest.raises(PatcherError):
        Patcher(modern_tree / 'run.py').apply()
    assert {p: p.read_bytes() for p in original} == original

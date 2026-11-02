"""Native header custom-icon experiment (animation needs client verification)."""
import pytest

from hermes_lark_cards.cardkit.builder import _LOADING_IMG_KEY, build_complete_card, build_streaming_card_v2
from hermes_lark_cards.config import Config


@pytest.mark.parametrize('value,expected', [(None, ''), ('', ''), (' img_v3_test ', 'img_v3_test'), ('loading', 'loading'), (42, '')])
def test_config_header_icon(value, expected):
    cfg = Config()
    cfg._raw = {'streaming': {'header': {'icon_img_key': value}}}
    assert cfg.header_icon_img_key == expected


@pytest.mark.parametrize('value', ['', 'img_v3_test', 'loading'])
def test_header_disabled_stays_absent(value):
    assert 'header' not in build_streaming_card_v2(header_icon_img_key=value)


@pytest.mark.parametrize('value,expected', [('img_v3_test', 'img_v3_test'), ('loading', _LOADING_IMG_KEY)])
def test_streaming_header_custom_icon(value, expected):
    card = build_streaming_card_v2(header_enabled=True, header_icon_img_key=value)
    assert card['header']['icon'] == {'tag': 'custom_icon', 'img_key': expected}
    assert card['header']['template'] == 'blue'


@pytest.mark.parametrize('status', [{}, {'is_error': True}, {'is_aborted': True}])
@pytest.mark.parametrize('value', ['', 'loading', 'img_v3_test'])
def test_complete_header_icon(status, value):
    card = build_complete_card(segments=[], all_tool_steps=[], footer_enabled=False,
                               header_enabled=True, header_icon_img_key=value, **status)
    if value == 'img_v3_test':
        assert card['header']['icon'] == {'tag': 'custom_icon', 'img_key': value}
    else:
        assert 'icon' not in card['header']


def test_default_header_unchanged():
    assert 'icon' not in build_streaming_card_v2(header_enabled=True)['header']

import os
import time
import pytest
from tools import read_notes, summarize_text, save_briefing, create_briefing
from audit import log_event


def test_read_notes_success():
    res = read_notes('sample_data/meeting_notes.txt')
    assert res['success'] is True
    assert res['output'] is not None
    assert 'Campus Event Planner' in res['output']
    assert res['error'] is None


def test_read_notes_missing_file():
    res = read_notes('sample_data/non_existent_file.txt')
    assert res['success'] is False
    assert res['output'] is None
    assert 'Meeting notes file not found' in res['error']


def test_summarize_text_success():
    sample_text = (
        'Project sprint started on Monday. '
        'The team resolved twelve major blockers. '
        'Demo is scheduled for Friday afternoon. '
        'Extra sentence that should be omitted.'
    )
    res = summarize_text(sample_text, max_sentences=3)
    assert res['success'] is True
    assert res['error'] is None
    assert 'Project sprint started on Monday.' in res['output']
    assert 'Extra sentence' not in res['output']


def test_summarize_empty_text():
    res = summarize_text('   ')
    assert res['success'] is False
    assert res['output'] is None
    assert 'cannot be empty' in res['error']


def test_save_briefing_lifecycle():
    ts = int(time.time() * 1000)
    test_file = f'outputs/test_briefing_{ts}.txt'
    content = f'Automated test briefing generated at timestamp {ts}.'

    res1 = save_briefing(content, filepath=test_file)
    assert res1['success'] is True
    assert os.path.exists(test_file)

    res2 = save_briefing(content, filepath=test_file)
    assert res2['success'] is False
    assert 'already exists' in res2['error']

    empty_file = f'outputs/empty_briefing_{ts}.txt'
    res3 = save_briefing('', filepath=empty_file)
    assert res3['success'] is False
    assert 'cannot be empty' in res3['error']


def test_create_briefing_workflow():
    ts = int(time.time() * 1000)
    workflow_output = f'outputs/test_workflow_{ts}.txt'

    res = create_briefing(output_path=workflow_output)
    assert res['success'] is True
    assert res['output'] is not None
    assert 'summary' in res['output']
    assert os.path.exists(workflow_output)


def test_audit_logging():
    test_msg = f'Unit test audit event verification {time.time()}'
    log_event(test_msg)

    assert os.path.exists('outputs/audit.log')
    with open('outputs/audit.log', 'r', encoding='utf-8', errors='ignore') as f:
        log_content = f.read()
    assert test_msg in log_content

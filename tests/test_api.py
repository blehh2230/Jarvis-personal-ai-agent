import pytest
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_json_endpoint():
    response = client.get('/', headers={'Accept': 'application/json'})
    assert response.status_code == 200
    data = response.json()
    assert data['app'] == 'JARVIS'
    assert 'docs' in data


def test_root_browser_serves_html():
    response = client.get('/', headers={'Accept': 'text/html'})
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    assert 'JARVIS' in response.text


def test_health_check_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_app_frontend_route():
    response = client.get('/app')
    assert response.status_code == 200
    assert 'Command Center' in response.text


def test_api_js_route():
    response = client.get('/api.js')
    assert response.status_code == 200
    assert 'JarvisApi' in response.text


def test_list_tools_endpoint():
    response = client.get('/api/tools')
    assert response.status_code == 200
    data = response.json()
    assert 'tools' in data
    assert any(t['id'] == 'read_notes' for t in data['tools'])
    assert any(t['id'] == 'summarize_text' for t in data['tools'])


def test_tool_read_notes_endpoint():
    response = client.post('/api/tools/read-notes')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'Campus Event Planner' in data['output']


def test_tool_summarize_endpoint():
    payload = {
        'text': 'First point. Second point. Third point.',
        'max_sentences': 2
    }
    response = client.post('/api/tools/summarize', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'First point.' in data['output']


def test_tool_audit_log_endpoints():
    post_resp = client.post('/api/tools/audit-log', json={'message': 'API test event'})
    assert post_resp.status_code == 200
    assert post_resp.json()['success'] is True

    get_resp = client.get('/api/tools/audit-log?limit=5')
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert 'events' in data
    assert any('API test event' in e for e in data['events'])


def test_briefing_workflow_endpoint():
    response = client.post('/api/workflows/briefing')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'summary' in data
    assert len(data['summary']) > 0


def test_memory_insights_and_items():
    insights_resp = client.get('/api/memory/insights')
    assert insights_resp.status_code == 200
    insights = insights_resp.json()
    assert 'total_memories' in insights

    items_resp = client.get('/api/memory/items')
    assert items_resp.status_code == 200
    assert isinstance(items_resp.json(), list)


def test_task_creation_and_retrieval():
    payload = {'instruction': 'Plan morning briefing and synthesize action items'}
    create_resp = client.post('/api/tasks', json=payload)
    assert create_resp.status_code == 202
    task = create_resp.json()
    task_id = task['task_id']
    assert task['status'] in ['queued', 'planned', 'running']

    get_resp = client.get(f'/api/tasks/{task_id}')
    assert get_resp.status_code == 200
    assert get_resp.json()['task_id'] == task_id

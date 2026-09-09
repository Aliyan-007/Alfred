import brain


def test_play_youtube_uses_local_tool(monkeypatch):
    calls = {}

    def fake_execute_tool(name, arguments):
        calls['name'] = name
        calls['arguments'] = arguments
        return 'local youtube result'

    def fake_execute_device_command(name, arguments):
        calls['remote'] = (name, arguments)
        return {'success': True, 'result': 'remote youtube result'}

    monkeypatch.setattr(brain, 'execute_tool', fake_execute_tool)
    monkeypatch.setattr(brain, 'execute_device_command', fake_execute_device_command)

    result = brain.execute_alfred_tool('play_youtube', {'query': 'sidemen'})

    assert result == 'local youtube result'
    assert calls['name'] == 'play_youtube'
    assert 'remote' not in calls

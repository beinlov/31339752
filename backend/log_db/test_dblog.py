from fastapi.testclient import TestClient
from dblog import app
import time

client = TestClient(app)

def test_post_log():
    filename = time.strftime('%Y-%m-%d', time.localtime()) + ".txt"
    resp = client.get(f"/dblog/{filename}")
    assert resp.status_code == 200
    print(resp)

test_post_log()

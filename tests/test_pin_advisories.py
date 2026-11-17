import json

import pin_advisories as p

VULNS = {
    "GHSA-1": {"id": "GHSA-1", "aliases": ["CVE-2023-25577"],
               "affected": [{"package": {"ecosystem": "PyPI", "name": "Werkzeug"},
                             "ranges": [{"events": [{"introduced": "0"}, {"fixed": "2.2.3"}]}]}]},
    "GHSA-2": {"id": "GHSA-2", "aliases": [],
               "affected": [{"package": {"ecosystem": "PyPI", "name": "werkzeug"},
                             "ranges": [{"events": [{"introduced": "0"}, {"fixed": "3.0.3"}]}]}]},
}


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *a):
        return self.data


def fake_osv(monkeypatch):
    def urlopen(req, timeout=None):
        url = req if isinstance(req, str) else req.full_url
        if url.endswith("/querybatch"):
            queries = json.loads(req.data)["queries"]
            return Response({"results": [{"vulns": [{"id": "GHSA-1"}, {"id": "GHSA-2"}]}
                                         if q["package"]["name"] == "werkzeug" else {} for q in queries]})
        return Response(VULNS[url.rsplit("/", 1)[1]])

    monkeypatch.setattr(p.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(p.json, "load", lambda r: json.loads(r.read()))


def test_a_vulnerable_pin_lists_its_ids_and_the_version_that_fixes_them_all(monkeypatch, capsys):
    fake_osv(monkeypatch)
    assert p.main(["--pin", "werkzeug==2.0.3", "--pin", "flask==3.1.3"]) == 1
    assert capsys.readouterr().out.strip() == "werkzeug==2.0.3: 2 advisories (CVE-2023-25577, GHSA-2); fixed in 3.0.3"


def test_clean_pins_from_a_manifest_exit_zero(monkeypatch, capsys, tmp_path):
    fake_osv(monkeypatch)
    manifest = tmp_path / "requirements.txt"
    manifest.write_bytes(b"\xef\xbb\xbfflask==3.1.3\r\n# werkzeug==2.0.3\r\nrequests>=2\r\n")
    assert p.pins_in(manifest) == [("flask", "3.1.3")]
    assert p.main([str(manifest)]) == 0
    assert "No known advisories for the 1 pins." in capsys.readouterr().out


def test_an_unreachable_osv_exits_2_with_a_message(monkeypatch, capsys):
    def down(*a, **k):
        raise p.urllib.error.URLError("Tunnel connection failed: 403 Forbidden")

    monkeypatch.setattr(p.urllib.request, "urlopen", down)
    assert p.main(["--pin", "werkzeug==2.0.3"]) == 2
    assert "Can't reach api.osv.dev" in capsys.readouterr().err

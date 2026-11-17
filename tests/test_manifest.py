import pytest

import manifest as m

BOM = b"\xef\xbb\xbf"


def write(tmp_path, text, bom=True, newline="\r\n", final=True):
    p = tmp_path / "requirements.txt"
    body = newline.join(text.splitlines()) + (newline if final else "")
    p.write_bytes((BOM if bom else b"") + body.encode())
    return p


def test_pin_replaces_in_place_and_keeps_bom_crlf_and_final_break(tmp_path):
    p = write(tmp_path, "langchain==0.2.11\nopenai==0.27.7\n# pywin32==308\nStreamlit>=1.0\npandas==2.3.3")
    m.main(["pin", str(p), "langchain==1.5.0", "streamlit==1.54.0", "rapidfuzz==3.14.6",
            "--before", "pandas", "--remove", "openai"])
    assert p.read_bytes() == BOM + (b"langchain==1.5.0\r\n# pywin32==308\r\nstreamlit==1.54.0\r\n"
                                    b"rapidfuzz==3.14.6\r\npandas==2.3.3\r\n")


def test_pin_keeps_lf_no_bom_and_a_missing_final_break(tmp_path):
    p = write(tmp_path, "flask==2.0.2\nrequests", bom=False, newline="\n", final=False)
    m.main(["pin", str(p), "requests==2.33.0", "werkzeug==3.1.9"])
    assert p.read_bytes() == b"flask==2.0.2\nrequests==2.33.0\nwerkzeug==3.1.9"


def test_pin_refuses_unknown_names_and_bad_specs(tmp_path):
    p = write(tmp_path, "flask==2.0.2")
    with pytest.raises(SystemExit):
        m.main(["pin", str(p), "--remove", "nothere"])
    with pytest.raises(SystemExit):
        m.main(["pin", str(p), "torch==2", "--before", "nothere"])
    with pytest.raises(SystemExit):
        m.main(["pin", str(p), "torch>=2"])
    assert p.read_bytes() == BOM + b"flask==2.0.2\r\n"


def test_check_reports_the_encoding_and_unpinned_lines(tmp_path, capsys):
    p = write(tmp_path, "faiss-cpu\nflask==2.0.2\n# comment")
    m.main(["check", str(p)])
    out = capsys.readouterr().out
    assert "byte-order mark yes; line endings CRLF; final line break yes; 2 packages, 1 not pinned" in out
    assert "not pinned: faiss-cpu" in out

import newest_working as n


def test_candidates_are_final_releases_newest_first_below_a_ceiling():
    versions = ["25.0.0", "26.0.1", "24.0.0", "26.0.0rc1", "9.0.0", "25.0.0.dev1", "1.0.post1"]
    assert n.candidates(versions) == ["26.0.1", "25.0.0", "24.0.0", "9.0.0", "1.0.post1"]
    assert n.candidates(versions, below="26") == ["25.0.0", "24.0.0", "9.0.0", "1.0.post1"]


def test_it_prints_the_newest_version_whose_check_passes(capsys):
    code = n.main(["--package", "pyarrow", "--versions", "24.0.0,26.0.1,25.0.0",
                   "--install", "true", "--check", 'test "$CANDIDATE" != 26.0.1'])
    assert code == 0 and capsys.readouterr().out.strip() == "25.0.0"


def test_it_skips_versions_that_dont_install_and_fails_when_none_work(capsys):
    code = n.main(["--package", "x", "--versions", "2.0,1.0", "--install", 'test "$CANDIDATE" = 1.0',
                   "--check", "false", "--tries", "5"])
    err = capsys.readouterr().err
    assert code == 1 and "x==2.0: doesn't install" in err and "x==1.0: check fails" in err

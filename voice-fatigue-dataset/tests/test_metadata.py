from pathlib import Path

from src.metadata import VIDEO_COLUMNS, _load_videos_csv


def test_load_videos_csv_handles_unquoted_commas_in_title(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "videos.csv"
    legacy_csv.write_text(
        "video_id,url,title,keyword_group,keyword,has_subtitles,subtitle_match_found\n"
        "abc123,https://example.com,Title, with comma,tired_mental,exam week exhausted vlog,True,False\n",
        encoding="utf-8",
    )

    df = _load_videos_csv(legacy_csv)

    assert list(df.columns) == VIDEO_COLUMNS
    assert len(df) == 1
    assert df.loc[0, "video_id"] == "abc123"
    assert df.loc[0, "url"] == "https://example.com"
    assert df.loc[0, "title"] == "Title, with comma"
    assert df.loc[0, "keyword_group"] == "tired_mental"
    assert df.loc[0, "keyword"] == "exam week exhausted vlog"
    assert df.loc[0, "has_subtitles"] == "True"
    assert df.loc[0, "subtitle_match_found"] == "False"

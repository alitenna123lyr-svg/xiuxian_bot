from adapters.actor_paths import compiled_actor_path_patterns


def _extract_actor(path: str) -> str | None:
    for pattern in compiled_actor_path_patterns():
        matched = pattern.match(path)
        if matched:
            return str(matched.group(1))
    return None


def test_actor_path_extracts_breakthrough_preview_uid():
    assert _extract_actor("/api/breakthrough/preview/1000001") == "1000001"


def test_actor_path_extracts_realm_trial_uid():
    assert _extract_actor("/api/realm-trial/1000002") == "1000002"

from types import SimpleNamespace
from unittest.mock import Mock, call

import pandas as pd

from ohmyscrapper.modules import process_with_ai


def write_prompt(path, name="default-prompt", model="gemini-test"):
    path.write_text(
        f"""---
model: "{model}"
name: "{name}"
description: "Prompt description"
---
Process these texts: {{ohmyscrapper_texts}}
""",
        encoding="utf-8",
    )


def test_xml2dict_groups_child_items_under_root_elements():
    result = process_with_ai.xml2dict(
        """
        <positions>
            <position>
                <id>1</id>
                <url>https://example.com/job</url>
                <role>Engineer</role>
            </position>
            <position>
                <id>2</id>
                <url>https://example.com/design</url>
                <role>Designer</role>
            </position>
        </positions>
        """
    )

    assert result == {
        "positions": [
            {
                "id": "1",
                "url": "https://example.com/job",
                "role": "Engineer",
            },
            {
                "id": "2",
                "url": "https://example.com/design",
                "role": "Designer",
            },
        ]
    }


def test_parse_prompt_reads_frontmatter_and_instructions(tmp_path):
    write_prompt(tmp_path / "prompt.md", name="jobs", model="gemini-2.5-flash")

    prompt = process_with_ai._parse_prompt(str(tmp_path), "prompt.md")

    assert prompt == {
        "model": "gemini-2.5-flash",
        "name": "jobs",
        "description": "Prompt description",
        "instructions": "Process these texts: {ohmyscrapper_texts}",
        "prompt_file": "prompt.md",
    }


def test_get_prompt_creates_default_prompt_when_folder_is_missing(
    tmp_path,
    monkeypatch,
):
    prompts_path = tmp_path / "prompts"
    monkeypatch.setattr(
        process_with_ai.config,
        "get_dir",
        Mock(return_value=str(prompts_path)),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_ai",
        Mock(return_value="default.md"),
    )

    result = process_with_ai._get_prompt()

    assert result is False
    assert prompts_path.exists()
    assert (prompts_path / "default.md").exists()


def test_get_prompt_creates_default_prompt_when_folder_is_empty(
    tmp_path,
    monkeypatch,
):
    prompts_path = tmp_path / "prompts"
    prompts_path.mkdir()
    monkeypatch.setattr(
        process_with_ai.config,
        "get_dir",
        Mock(return_value=str(prompts_path)),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_ai",
        Mock(return_value="default.md"),
    )

    result = process_with_ai._get_prompt()

    assert result is False
    assert (prompts_path / "default.md").exists()


def test_get_prompt_returns_only_prompt_file(tmp_path, monkeypatch):
    write_prompt(tmp_path / "prompt.md", name="only")
    monkeypatch.setattr(
        process_with_ai.config,
        "get_dir",
        Mock(return_value=str(tmp_path)),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_ai",
        Mock(return_value="default.md"),
    )

    prompt = process_with_ai._get_prompt()

    assert prompt["name"] == "only"
    assert prompt["prompt_file"] == "prompt.md"


def test_get_prompt_allows_user_to_choose_from_multiple_files(
    tmp_path,
    monkeypatch,
):
    write_prompt(tmp_path / "first.md", name="first")
    write_prompt(tmp_path / "second.md", name="second")
    monkeypatch.setattr(
        process_with_ai.os,
        "listdir",
        Mock(return_value=["first.md", "second.md"]),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_dir",
        Mock(return_value=str(tmp_path)),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_ai",
        Mock(return_value="default.md"),
    )
    monkeypatch.setattr("builtins.input", Mock(return_value="1"))

    prompt = process_with_ai._get_prompt()

    assert prompt["name"] == "second"
    assert prompt["prompt_file"] == "second.md"


def test_get_prompt_returns_false_when_user_quits_multiple_file_prompt(
    tmp_path,
    monkeypatch,
):
    write_prompt(tmp_path / "first.md", name="first")
    write_prompt(tmp_path / "second.md", name="second")
    monkeypatch.setattr(
        process_with_ai.os,
        "listdir",
        Mock(return_value=["first.md", "second.md"]),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_dir",
        Mock(return_value=str(tmp_path)),
    )
    monkeypatch.setattr(
        process_with_ai.config,
        "get_ai",
        Mock(return_value="default.md"),
    )
    monkeypatch.setattr("builtins.input", Mock(return_value="q"))

    assert process_with_ai._get_prompt() is False


def test_reprocess_ai_history_replays_each_logged_response(monkeypatch):
    process_ai_response = Mock()
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_ai_log",
        Mock(
            return_value=pd.DataFrame(
                [
                    {"response": "<first></first>"},
                    {"response": "<second></second>"},
                ]
            )
        ),
    )
    monkeypatch.setattr(process_with_ai, "process_ai_response", process_ai_response)

    process_with_ai.reprocess_ai_history()

    assert process_ai_response.call_args_list == [
        call("<first></first>"),
        call("<second></second>"),
    ]


def test_process_ai_response_updates_parent_when_parent_has_single_description_link(
    monkeypatch,
):
    set_url_ai_processed_by_url = Mock()
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_url_by_id",
        Mock(
            return_value=pd.DataFrame(
                [
                    {
                        "id": "1",
                        "url": "https://example.com/parent",
                        "description_links": 1,
                    }
                ]
            )
        ),
    )
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "set_url_ai_processed_by_url",
        set_url_ai_processed_by_url,
    )

    process_with_ai.process_ai_response(
        """
        <positions>
            <position>
                <id>1</id>
                <url>https://example.com/child</url>
                <role>Engineer</role>
            </position>
        </positions>
        """
    )

    set_url_ai_processed_by_url.assert_called_once_with(
        "https://example.com/parent",
        '{"id": "1", "url": "https://example.com/child", "role": "Engineer"}',
    )


def test_process_ai_response_updates_child_and_marks_parent_when_multiple_links(
    monkeypatch,
):
    set_url_ai_processed_by_url = Mock()
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_url_by_id",
        Mock(
            return_value=pd.DataFrame(
                [
                    {
                        "id": "1",
                        "url": "https://example.com/parent",
                        "description_links": 2,
                    }
                ]
            )
        ),
    )
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "set_url_ai_processed_by_url",
        set_url_ai_processed_by_url,
    )

    process_with_ai.process_ai_response(
        """
        <positions>
            <position>
                <id>1</id>
                <url>https://example.com/child</url>
                <role>Engineer</role>
            </position>
        </positions>
        """
    )

    assert set_url_ai_processed_by_url.call_args_list == [
        call(
            "https://example.com/child",
            '{"id": "1", "url": "https://example.com/child", "role": "Engineer"}',
        ),
        call("https://example.com/parent", "children-update"),
    ]


def test_process_with_ai_returns_when_prompt_is_missing(monkeypatch):
    get_urls = Mock()
    monkeypatch.setattr(process_with_ai, "_get_prompt", Mock(return_value=False))
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_urls_by_url_type_for_ai_process",
        get_urls,
    )

    assert process_with_ai.process_with_ai() is None
    get_urls.assert_not_called()


def test_process_with_ai_returns_when_there_are_no_urls(monkeypatch):
    monkeypatch.setattr(
        process_with_ai,
        "_get_prompt",
        Mock(return_value={"name": "prompt"}),
    )
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_urls_by_url_type_for_ai_process",
        Mock(return_value=pd.DataFrame()),
    )

    assert process_with_ai.process_with_ai() is None


def test_process_with_ai_sends_prompt_to_gemini_and_records_response(monkeypatch):
    prompt = {
        "model": "gemini-test",
        "name": "jobs",
        "description": "Find jobs",
        "instructions": "Handle {ohmyscrapper_texts}",
        "prompt_file": "prompt.md",
    }
    urls = pd.DataFrame(
        [
            {
                "id": 1,
                "title": "Engineer",
                "description": "Build things",
            },
            {
                "id": 2,
                "title": "Designer",
                "description": "Design things",
            },
        ]
    )
    add_ai_log = Mock()
    process_ai_response = Mock()
    set_empty = Mock()
    generate_content = Mock(
        return_value=SimpleNamespace(text="<positions></positions>")
    )
    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

    monkeypatch.setattr(process_with_ai, "_get_prompt", Mock(return_value=prompt))
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_urls_by_url_type_for_ai_process",
        Mock(return_value=urls),
    )
    monkeypatch.setattr(process_with_ai.urls_manager, "add_ai_log", add_ai_log)
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "set_url_empty_ai_processed_by_id",
        set_empty,
    )
    monkeypatch.setattr(process_with_ai, "process_ai_response", process_ai_response)
    monkeypatch.setattr(process_with_ai.genai, "Client", Mock(return_value=client))

    result = process_with_ai.process_with_ai(recursive=False)

    assert result is None
    generate_content.assert_called_once()
    assert generate_content.call_args.kwargs["model"] == "gemini-test"
    instructions = generate_content.call_args.kwargs["contents"]
    assert "{ohmyscrapper_texts}" not in instructions
    assert "<id>1</id>" in instructions
    assert "Engineer" in instructions
    assert "Build things" in instructions
    add_ai_log.assert_called_once_with(
        instructions=instructions,
        response="<positions></positions>",
        model="gemini-test",
        prompt_name="jobs",
        prompt_file="prompt.md",
    )
    process_ai_response.assert_called_once_with(response="<positions></positions>")
    assert set_empty.call_args_list == [call(1), call(2)]


def test_process_with_ai_sends_prompt_to_openai_when_model_is_openai(monkeypatch):
    prompt = {
        "model": "gpt-4o-mini",
        "name": "jobs",
        "description": "Find jobs",
        "instructions": "Handle {ohmyscrapper_texts}",
        "prompt_file": "prompt.md",
    }
    urls = pd.DataFrame([{"id": 1, "title": "Engineer", "description": "Build"}])
    add_ai_log = Mock()
    process_ai_response = Mock()
    set_empty = Mock()
    create = Mock(return_value=SimpleNamespace(output_text="<positions></positions>"))
    client = SimpleNamespace(responses=SimpleNamespace(create=create))

    monkeypatch.setattr(process_with_ai, "_get_prompt", Mock(return_value=prompt))
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_urls_by_url_type_for_ai_process",
        Mock(return_value=urls),
    )
    monkeypatch.setattr(process_with_ai.urls_manager, "add_ai_log", add_ai_log)
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "set_url_empty_ai_processed_by_id",
        set_empty,
    )
    monkeypatch.setattr(process_with_ai, "process_ai_response", process_ai_response)
    monkeypatch.setattr(process_with_ai, "OpenAI", Mock(return_value=client))

    result = process_with_ai.process_with_ai(recursive=False)

    assert result is None
    create.assert_called_once()
    assert create.call_args.kwargs["model"] == "gpt-4o-mini"
    instructions = create.call_args.kwargs["input"]
    assert "{ohmyscrapper_texts}" not in instructions
    assert "<id>1</id>" in instructions
    add_ai_log.assert_called_once_with(
        instructions=instructions,
        response="<positions></positions>",
        model="gpt-4o-mini",
        prompt_name="jobs",
        prompt_file="prompt.md",
    )
    process_ai_response.assert_called_once_with(response="<positions></positions>")
    set_empty.assert_called_once_with(1)


def test_process_with_ai_stops_recursive_mode_at_budget_guard(monkeypatch):
    prompt = {
        "model": "gemini-test",
        "name": "jobs",
        "description": "Find jobs",
        "instructions": "Handle {ohmyscrapper_texts}",
        "prompt_file": "prompt.md",
    }
    urls = pd.DataFrame([{"id": 1, "title": "Engineer", "description": "Build"}])
    generate_content = Mock(
        return_value=SimpleNamespace(text="<positions></positions>")
    )
    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

    monkeypatch.setattr(process_with_ai, "_get_prompt", Mock(return_value=prompt))
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "get_urls_by_url_type_for_ai_process",
        Mock(return_value=urls),
    )
    monkeypatch.setattr(process_with_ai.urls_manager, "add_ai_log", Mock())
    monkeypatch.setattr(
        process_with_ai.urls_manager,
        "set_url_empty_ai_processed_by_id",
        Mock(),
    )
    monkeypatch.setattr(process_with_ai, "process_ai_response", Mock())
    monkeypatch.setattr(process_with_ai.genai, "Client", Mock(return_value=client))
    monkeypatch.setattr(process_with_ai.random, "randint", Mock(return_value=2))
    monkeypatch.setattr(process_with_ai.time, "sleep", Mock())

    result = process_with_ai.process_with_ai(recursive=True, triggered_times=5)

    assert result is None
    process_with_ai.time.sleep.assert_called_once_with(2)
    get_urls = process_with_ai.urls_manager.get_urls_by_url_type_for_ai_process
    get_urls.assert_called_once_with()


def test_process_with_model_defaults_to_gemini_and_allows_openai_prefix(monkeypatch):
    gemini = Mock(return_value="gemini-response")
    openai = Mock(return_value="openai-response")
    monkeypatch.setattr(process_with_ai, "_process_with_gemini", gemini)
    monkeypatch.setattr(process_with_ai, "_process_with_openai", openai)

    assert process_with_ai._process_with_model("unknown-model", "instructions") == (
        "gemini-response"
    )
    gemini.assert_called_once_with("unknown-model", "instructions")

    assert process_with_ai._process_with_model("openai:gpt-4o-mini", "prompt") == (
        "openai-response"
    )
    openai.assert_called_once_with("gpt-4o-mini", "prompt")

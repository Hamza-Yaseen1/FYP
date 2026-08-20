import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.ai.providers.base import AIAnalysisResult
from services.ai.analyzer import analyze_message


def make_result(
    priority="normal",
    confidence=0.8,
    tasks_extracted=None,
    deadlines=None,
):
    return AIAnalysisResult(
        priority=priority,
        confidence=confidence,
        explanation="Test explanation",
        tasks_extracted=tasks_extracted or [],
        deadlines=deadlines or [],
    )


@pytest.mark.asyncio
async def test_task_extracted_from_actionable_message():
    tasks = [{"description": "Send FYP slides", "deadline": "Tonight", "priority_indicator": "tonight", "requires_action": True}]
    result = make_result(priority="urgent", tasks_extracted=tasks, deadlines=["Tonight"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Send me the FYP slides tonight.")

    assert len(analysis["tasks_extracted"]) == 1
    assert analysis["tasks_extracted"][0]["description"] == "Send FYP slides"
    assert analysis["tasks_extracted"][0]["deadline"] == "Tonight"
    assert analysis["tasks_extracted"][0]["requires_action"] is True


@pytest.mark.asyncio
async def test_no_task_from_informational_message():
    result = make_result(priority="low", tasks_extracted=[], deadlines=[])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("FYI server will be down tomorrow.")

    assert analysis["tasks_extracted"] == []
    assert analysis["deadlines"] == []


@pytest.mark.asyncio
async def test_no_task_from_sender_promise():
    result = make_result(priority="normal", tasks_extracted=[], deadlines=["tomorrow"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("I'll send you the files tomorrow.")

    assert analysis["tasks_extracted"] == []
    assert analysis["deadlines"] == ["tomorrow"]


@pytest.mark.asyncio
async def test_deadline_null_when_no_deadline_in_message():
    tasks = [{"description": "Review document", "deadline": None, "priority_indicator": None, "requires_action": True}]
    result = make_result(tasks_extracted=tasks, deadlines=[])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Can you review this document?")

    assert analysis["tasks_extracted"][0]["deadline"] is None


@pytest.mark.asyncio
async def test_asap_deadline_produces_urgent_priority():
    tasks = [{"description": "Submit the form", "deadline": "ASAP", "priority_indicator": "ASAP", "requires_action": True}]
    result = make_result(priority="urgent", tasks_extracted=tasks, deadlines=["ASAP"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("ASAP: submit the form.")

    assert analysis["priority"] == "urgent"
    assert analysis["tasks_extracted"][0]["deadline"] == "ASAP"


@pytest.mark.asyncio
async def test_next_week_deadline_produces_normal_priority():
    tasks = [{"description": "Prepare slides", "deadline": "next week", "priority_indicator": None, "requires_action": True}]
    result = make_result(priority="normal", tasks_extracted=tasks, deadlines=["next week"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Prepare the presentation next week.")

    assert analysis["priority"] == "normal"
    assert analysis["tasks_extracted"][0]["deadline"] == "next week"


@pytest.mark.asyncio
async def test_graceful_fallback_on_ai_failure():
    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.side_effect = Exception("Groq API down")
        mock_get.return_value = provider

        analysis = await analyze_message("Any message.")

    assert analysis["priority"] == "normal"
    assert analysis["confidence"] == 0.0
    assert analysis["tasks_extracted"] == []
    assert analysis["deadlines"] == []
    assert analysis["status"] == "pending"


@pytest.mark.asyncio
async def test_multiple_tasks_from_single_message():
    tasks = [
        {"description": "Review slides", "deadline": "Thursday", "priority_indicator": None, "requires_action": True},
        {"description": "Send feedback", "deadline": "Thursday", "priority_indicator": None, "requires_action": True},
    ]
    result = make_result(tasks_extracted=tasks, deadlines=["Thursday"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Review the slides and send feedback by Thursday.")

    assert len(analysis["tasks_extracted"]) == 2
    assert analysis["tasks_extracted"][0]["description"] == "Review slides"
    assert analysis["tasks_extracted"][1]["description"] == "Send feedback"


@pytest.mark.asyncio
async def test_deadline_preserved_exactly_as_stated():
    tasks = [{"description": "Send docs", "deadline": "before the meeting", "priority_indicator": None, "requires_action": True}]
    result = make_result(tasks_extracted=tasks, deadlines=["before the meeting"])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Send docs before the meeting.")

    assert analysis["tasks_extracted"][0]["deadline"] == "before the meeting"


@pytest.mark.asyncio
async def test_very_long_message():
    long_content = "Please review this document. " * 500
    tasks = [{"description": "Review document", "deadline": None, "priority_indicator": None, "requires_action": True}]
    result = make_result(tasks_extracted=tasks, deadlines=[])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message(long_content)

    assert len(analysis["tasks_extracted"]) == 1
    assert analysis["tasks_extracted"][0]["description"] == "Review document"


@pytest.mark.asyncio
async def test_non_english_message_no_tasks():
    result = make_result(priority="normal", tasks_extracted=[], deadlines=[])

    with patch("services.ai.analyzer.get_provider") as mock_get:
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Please send me the report by Friday.")

    assert isinstance(analysis["tasks_extracted"], list)


@pytest.mark.asyncio
async def test_tasks_stored_in_db_after_analysis():
    """Integration test: verify analyzer stores tasks in tasks_collection."""
    tasks = [{"description": "Send FYP slides", "deadline": "Tonight", "priority_indicator": "tonight", "requires_action": True}]
    result = make_result(priority="urgent", tasks_extracted=tasks, deadlines=["Tonight"])

    mock_tasks_collection = MagicMock()
    mock_tasks_collection.insert_many = AsyncMock()

    with patch("services.ai.analyzer.get_provider") as mock_get, \
         patch("services.ai.analyzer.tasks_collection", mock_tasks_collection):
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        analysis = await analyze_message("Send me the FYP slides tonight.", message_id="test_msg_id")

    mock_tasks_collection.insert_many.assert_called_once()
    stored_docs = mock_tasks_collection.insert_many.call_args[0][0]
    assert len(stored_docs) == 1
    assert stored_docs[0]["source_message_id"] == "test_msg_id"
    assert stored_docs[0]["description"] == "Send FYP slides"
    assert stored_docs[0]["deadline"] == "Tonight"


@pytest.mark.asyncio
async def test_no_tasks_stored_when_none_extracted():
    result = make_result(priority="low", tasks_extracted=[], deadlines=[])

    mock_tasks_collection = MagicMock()
    mock_tasks_collection.insert_many = AsyncMock()

    with patch("services.ai.analyzer.get_provider") as mock_get, \
         patch("services.ai.analyzer.tasks_collection", mock_tasks_collection):
        provider = AsyncMock()
        provider.analyze.return_value = result
        provider.generate_summary.return_value = "Summary"
        mock_get.return_value = provider

        await analyze_message("FYI server down tomorrow.", message_id="test_msg_id")

    mock_tasks_collection.insert_many.assert_not_called()

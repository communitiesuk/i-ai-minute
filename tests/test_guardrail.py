from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from common.database.postgres_models import GuardrailResult, JobStatus
from common.services.minute_handler_service import MinuteHandlerService
from common.types import GuardrailScore


@pytest.mark.asyncio
async def test_calculate_accuracy_score():
    # Mock the chatbot and its response
    mock_score = GuardrailScore(score=0.95, reasoning="Excellent summary")
    
    with patch("common.services.minute_handler_service.create_default_chatbot") as mock_create_chatbot:
        mock_chatbot = MagicMock()
        mock_chatbot.structured_chat = AsyncMock(return_value=mock_score)
        mock_create_chatbot.return_value = mock_chatbot

        # Test data
        minute_text = "Meeting summary"
        transcript = [{"speaker": "A", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]

        # Call method
        result = await MinuteHandlerService.calculate_accuracy_score(minute_text, transcript)

        # Assertions
        assert result == mock_score
        assert result.score == 0.95
        assert result.reasoning == "Excellent summary"
        
        # Verify LLM called correctly
        mock_chatbot.structured_chat.assert_called_once()
        args, kwargs = mock_chatbot.structured_chat.call_args
        assert kwargs["response_format"] == GuardrailScore
        assert len(kwargs["messages"]) == 3
        assert kwargs["messages"][0]["role"] == "system"
        assert "Quality Assurance auditor" in kwargs["messages"][0]["content"]

@patch("common.services.minute_handler_service.SessionLocal")
def test_save_guardrail_result(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session
    
    minute_version_id = "123e4567-e89b-12d3-a456-426614174000"
    score = GuardrailScore(score=0.8, reasoning="Good")
    
    MinuteHandlerService.save_guardrail_result(minute_version_id, score)
    
    # Verify DB interaction
    mock_session.add.assert_called_once()
    saved_obj = mock_session.add.call_args[0][0]
    assert isinstance(saved_obj, GuardrailResult)
    assert str(saved_obj.minute_version_id) == minute_version_id
    assert saved_obj.score == 0.8
    assert saved_obj.reasoning == "Good"
    assert saved_obj.result == "PASS"
    
    mock_session.commit.assert_called_once()

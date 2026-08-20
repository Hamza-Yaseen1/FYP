import os
import json
import logging
from openai import AsyncOpenAI
from .base import BaseLLMProvider, AIAnalysisResult

logger = logging.getLogger(__name__)

COMPREHENSIVE_ANALYSIS_PROMPT = """You are an AI assistant that analyzes communication messages comprehensively.

Analyze the following message and return a complete analysis with ALL these components:

**MESSAGE TO ANALYZE:**
---
{message}
---

**YOUR TASK:**

1. **PRIORITY CLASSIFICATION**
   - URGENT: Needs immediate attention (hours). Keywords: "urgent", "ASAP", "now", "immediately", "tonight", "today" with clear deadline
   - IMPORTANT: Needs attention within 1-3 days. Has deadline this week or clear action item
   - NORMAL: Needs attention but not time-sensitive (default if unclear)
   - LOW: Minimal action needed, informational only
   
2. **TASK EXTRACTION**
   - Extract any actionable tasks the recipient needs to do
   - Only extract explicit tasks, don't invent them
   - Format: Brief action description
   
3. **DEADLINE EXTRACTION**
   - Extract any mentioned deadlines exactly as stated
   - Examples: "tonight", "Friday", "5 PM today", "end of week"
   - Return empty array if no deadlines
   
4. **SUMMARY** 
   - If message is SHORT (<200 chars): return null
   - If message is LONG (>200 chars): create 1-2 sentence summary (max 100 words)
   
5. **RECOMMENDED ACTIONS**
   - Suggest 1-3 appropriate next actions
   - Options: "Reply", "Schedule", "Review", "Complete Task", "Acknowledge", "Archive", "Read Later"
   - Base on message priority and content

**RETURN FORMAT:**
Return a JSON object with these EXACT fields:
{{
  "priority": "urgent" | "important" | "normal" | "low",
  "confidence": 0.0 to 1.0,
  "explanation": "Brief reason for priority classification",
  "summary": "Brief summary" or null,
  "recommended_actions": ["Action1", "Action2"],
  "tasks_extracted": ["Task description"],
  "deadlines": ["Deadline string"]
}}

**CRITICAL RULES:**
- Base priority ONLY on message content
- When "urgent" or "ASAP" appears with deadline, priority = "urgent"
- Extract tasks word-for-word, don't paraphrase
- Never invent information not in the message
- Return valid JSON only, no markdown or extra text"""


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if api_key == "your-openai-api-key-here":
            raise ValueError("Please replace 'your-openai-api-key-here' with your actual OpenAI API key in backend/.env")
        
        logger.info(f"✅ Initializing OpenAI provider with API key: {api_key[:20]}...")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    async def analyze(self, message: str) -> AIAnalysisResult:
        prompt = COMPREHENSIVE_ANALYSIS_PROMPT.format(message=message)
        
        logger.info(f"📤 Calling OpenAI API with model: {self.model}")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            content = response.choices[0].message.content
            logger.info(f"📥 OpenAI response received: {content[:100]}...")
            
            result = json.loads(content)
            
            # Validate required fields
            if "priority" not in result:
                raise ValueError("OpenAI response missing 'priority' field")
            
            # Ensure all fields exist with defaults
            result.setdefault("confidence", 0.8)
            result.setdefault("explanation", "No explanation provided")
            result.setdefault("summary", None)
            result.setdefault("recommended_actions", [])
            result.setdefault("tasks_extracted", [])
            result.setdefault("deadlines", [])
            
            logger.info(f"✅ Analysis successful - Priority: {result['priority']}, Confidence: {result['confidence']}")
            
            return AIAnalysisResult(**result)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {type(e).__name__}: {str(e)}")
            raise

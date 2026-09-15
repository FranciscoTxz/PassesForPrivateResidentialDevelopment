import json

from fastapi import HTTPException
from openai import OpenAI

from commons.constants import (
    DEEPSEEK_API_BASE,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
)
from commons.log_helper import get_logger
from schemas.passes_schema import ReviewSchema

_LOG = get_logger(__name__)

SYSTEM_PROMPT = """
You are a gate access permission review system for a gated residential community (fraccionamiento).
Your role is to evaluate user requests for multi-day access permissions (2+ days) and approve or deny them based on the provided information.

## Evaluation Criteria

### APPROVE if:
- Clear purpose requiring multiple days (e.g., construction work, extended maintenance, family visit staying overnight, professional services spanning days)
- Specific dates requested
- Detailed information: who, what, where (specific address/gate), when, why, contact info
- Legitimate reason that cannot be completed in a few hours

### DENY if:
- Insufficient details (vague purpose, no dates, no contact info, no specific location)
- Activity can be completed in a few hours (e.g., "quick delivery", "short meeting", "drop off package")
- No clear multi-day need
- Suspicious/vague requests (e.g., "need access", "visiting friend" without details)
- Missing essential information (name, vehicle info, phone, purpose)

## Response Format
Respond ONLY with valid JSON matching this exact schema:

{
    "approved": boolean,
    "reason": "string"
}

- `approved`: true if permission granted, false if denied
- `reason`: Detailed explanation (10-300 characters) stating why approved/denied, referencing specific missing info or justification needed

Return only the JSON object, nothing else.
"""

if not DEEPSEEK_API_KEY:
    _LOG.warning(
        "Deepseek API key is not set. AI review functionality will be disabled."
    )
else:
    _deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_API_BASE,
    )


class ReviewService:
    @staticmethod
    def review_pass(user_message: str) -> ReviewSchema:
        if not DEEPSEEK_API_KEY or not DEEPSEEK_API_BASE:
            _LOG.error("Deepseek API key is not set. Cannot perform review.")
            raise HTTPException(
                status_code=423,
                detail="AI review service is currently unavailable. Please try again later.",
            )
        try:
            chat_prompt = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": user_message},
            ]
            completion = _deepseek_client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=chat_prompt,
                max_tokens=1000,
                temperature=0.5,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
                response_format={"type": "json_object"},
                timeout=10,
            )

            result = completion.choices[0].message.content
            return ReviewSchema.model_validate(json.loads(result))
        except Exception as err:
            _LOG.error(f"Reason review error. Error: {err}")
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while reviewing the submitted reason",
            )

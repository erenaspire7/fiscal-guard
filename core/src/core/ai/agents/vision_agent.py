"""AI-powered vision extraction agent for cart screenshots using Strands."""

from typing import Optional

from pydantic import BaseModel, Field
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings


class ExtractedCartItem(BaseModel):
    """Single cart item extracted from screenshot."""

    item_name: str = Field(..., description="Full product name/title")
    price: float = Field(
        ..., description="Price per unit (numeric only, no currency symbol)"
    )
    quantity: int = Field(..., description="Number of this item in cart", gt=0)
    urgency_badge: Optional[str] = Field(
        None,
        description="Any urgency indicators like 'Limited time deal', 'Only 2 left in stock', etc.",
    )
    confidence: float = Field(
        ..., description="Extraction confidence score (0.0 to 1.0)", ge=0.0, le=1.0
    )


class CartExtractionResult(BaseModel):
    """Result of cart extraction from screenshot."""

    items: list[ExtractedCartItem] = Field(
        ..., description="List of extracted cart items"
    )
    extraction_quality: str = Field(
        ...,
        description="Quality of extraction: 'high', 'medium', or 'low'",
    )
    confidence_score: float = Field(
        ...,
        description="Overall extraction confidence (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    warnings: list[str] = Field(
        default=[],
        description="List of warnings or issues during extraction. Use an empty list [] if there are no warnings.",
    )


class VisionAgent:
    """Handle vision extraction from cart screenshots using Gemini Vision."""

    def __init__(self):
        """Initialize vision agent with Gemini Vision model."""
        # Initialize Gemini model with vision capabilities
        self.model = GeminiModel(
            client_args={
                "api_key": settings.google_api_key,
            },
            model_id=settings.strands_vision_model,
            params={
                "temperature": 0.3,  # Lower temperature for more consistent extraction
                "max_output_tokens": 8192,
                "top_p": 0.95,
                "top_k": 40,
            },
        )

        self.system_prompt = """You are an expert at extracting shopping cart information from screenshots.

Your task is to analyze shopping cart screenshots and extract ALL visible items with their details.

For each item, extract:
- item_name: Full product name/title exactly as shown
- price: Price per unit (numeric only, no currency symbol, use decimal format like 24.99)
- quantity: Number of this item in cart
- urgency_badge: Any urgency indicators like "Limited time deal", "Only 2 left in stock", "Lightning Deal", etc. (null if none)
- confidence: Your confidence in this extraction (0.0 to 1.0)

CRITICAL RULES:
1. Extract the UNIT PRICE, not the total
   - If you see "$24.99 x 2 = $49.98", extract price as 24.99, quantity as 2
   - If you see "2 items at $12.50 each", extract price as 12.50, quantity as 2

2. For urgency badges:
   - Capture the EXACT text you see
   - Look for phrases like "Limited time", "Only X left", "Deal ends", "Lightning Deal"
   - Set to null if no urgency indicator is present

3. Only include items that are CLEARLY products for purchase
   - Ignore shipping costs
   - Ignore tax lines
   - Ignore order summary information
   - Ignore promotional banners

4. Confidence scoring:
   - 1.0: All details are crystal clear
   - 0.8-0.9: Minor ambiguity (e.g., slightly blurry text)
   - 0.6-0.7: Some uncertainty (e.g., partial text visible)
   - 0.4-0.5: Significant uncertainty (e.g., very small or unclear)
   - Below 0.4: Don't include the item

5. Overall extraction quality:
   - 'high': All items extracted with confidence ≥ 0.8
   - 'medium': Most items extracted with confidence ≥ 0.6
   - 'low': Many items with confidence < 0.6 or items likely missed

6. Warnings to report (must be a list, use [] if no warnings):
   - "Image quality is poor, some items may be missed"
   - "Some prices are partially obscured"
   - "Cart appears to be scrolled, items may be cut off"
   - "Unable to distinguish individual items clearly"
   - If no warnings, return an empty list: []

IMPORTANT: Always return 'warnings' as a list (array). Never return null or omit this field.

Be thorough and accurate. If you're not confident about an item, reflect that in the confidence score."""

    def extract_cart_items(
        self, image_bytes: bytes, trace_attributes: Optional[dict] = None
    ) -> CartExtractionResult:
        """Extract cart items from a screenshot.

        Args:
            image_bytes: Raw image bytes (PNG format)
            trace_attributes: Optional trace attributes for observability

        Returns:
            CartExtractionResult with extracted items and metadata
        """
        # Create agent with structured output
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            structured_output_model=CartExtractionResult,
            trace_attributes=trace_attributes or {},
        )

        # Build the prompt with vision input using correct multi-modal format
        # Format: list of message parts with text and image components
        prompt = [
            {
                "text": "Analyze this shopping cart screenshot and extract all visible items. Follow all the rules in your system prompt."
            },
            {
                "image": {
                    "format": "png",
                    "source": {
                        "bytes": image_bytes,
                    },
                },
            },
        ]

        # Call the agent with vision input
        # The agent will return structured output matching CartExtractionResult
        response = agent(prompt)

        # The structured output should be directly parseable
        # Strands Agent with structured_output_model should return the model instance
        if isinstance(response, CartExtractionResult):
            return response

        # Fallback: parse if it's returned as JSON string
        import json

        if hasattr(response, "output"):
            json_str = response.output
        else:
            json_str = str(response)

        json_data = json.loads(json_str)

        # Normalize warnings field - ensure it's always a list
        if "warnings" not in json_data or json_data["warnings"] is None:
            json_data["warnings"] = []
        elif isinstance(json_data["warnings"], str):
            # If warnings is a string, convert to list
            json_data["warnings"] = (
                [json_data["warnings"]] if json_data["warnings"] else []
            )

        result = CartExtractionResult(**json_data)

        return result

    def validate_extraction(self, result: CartExtractionResult) -> dict[str, any]:
        """Validate extraction quality and provide feedback.

        Args:
            result: The extraction result to validate

        Returns:
            Validation report with quality assessment
        """
        validation = {
            "is_valid": True,
            "quality": result.extraction_quality,
            "confidence": result.confidence_score,
            "item_count": len(result.items),
            "issues": [],
            "recommendations": [],
        }

        # Check if any items were found
        if len(result.items) == 0:
            validation["is_valid"] = False
            validation["issues"].append("No items extracted from screenshot")
            validation["recommendations"].append(
                "Ensure the screenshot shows the shopping cart clearly"
            )
            return validation

        # Check confidence scores
        low_confidence_items = [item for item in result.items if item.confidence < 0.6]
        if low_confidence_items:
            validation["issues"].append(
                f"{len(low_confidence_items)} items have low confidence scores"
            )
            if len(low_confidence_items) > len(result.items) * 0.3:
                validation["recommendations"].append(
                    "Consider retaking the screenshot with better image quality"
                )

        # Check for price anomalies
        very_low_prices = [item for item in result.items if item.price < 0.01]
        if very_low_prices:
            validation["issues"].append(
                f"{len(very_low_prices)} items have suspiciously low prices"
            )
            validation["recommendations"].append(
                "Verify prices manually as some may be incorrectly extracted"
            )

        very_high_prices = [item for item in result.items if item.price > 10000]
        if very_high_prices:
            validation["issues"].append(
                f"{len(very_high_prices)} items have very high prices"
            )
            validation["recommendations"].append(
                "Verify high-priced items as they may be total amounts instead of unit prices"
            )

        # Check warnings from extraction
        if result.warnings:
            validation["issues"].extend(result.warnings)

        # Determine if extraction is good enough to proceed
        if result.extraction_quality == "low" or result.confidence_score < 0.5:
            validation["is_valid"] = False
            validation["recommendations"].append(
                "Retake the screenshot for better accuracy"
            )

        return validation

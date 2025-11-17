"""
Claude Haiku AI categorizer for transactions.

Uses prompt caching to reduce costs by 90% for repeated category lookups.
"""
import json
import os
from typing import List, Optional, Tuple

from anthropic import Anthropic

from ..data.models import Category, Transaction


class ClaudeCategorizationEngine:
    """AI-powered transaction categorization using Claude Haiku."""

    def __init__(
        self,
        categories: List[Category],
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
    ):
        """
        Initialize Claude categorization engine.

        Args:
            categories: List of available categories
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (haiku recommended for speed/cost)
        """
        self.categories = categories
        self.model = model
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

        # Build category context for prompt caching
        self._category_context = self._build_category_context()

    def _build_category_context(self) -> str:
        """
        Build category context for prompt caching.

        This is the expensive part that we cache to save 90% on costs.
        """
        lines = ["# Available Categories\n"]

        # Group by parent
        top_level = [c for c in self.categories if c.parent_id is None]
        children_map = {}
        for cat in self.categories:
            if cat.parent_id:
                if cat.parent_id not in children_map:
                    children_map[cat.parent_id] = []
                children_map[cat.parent_id].append(cat)

        # Format hierarchically
        for parent in top_level:
            lines.append(f"\n## {parent.icon} {parent.name}")
            if parent.id in children_map:
                for child in children_map[parent.id]:
                    lines.append(f"  - {child.icon} {child.name} (ID: {child.name})")
            else:
                lines.append(f"  (ID: {parent.name})")

        return "\n".join(lines)

    def categorize_transaction(
        self, transaction: Transaction, max_retries: int = 2
    ) -> Tuple[str, float, str]:
        """
        Categorize a single transaction using Claude Haiku with retry logic.

        Args:
            transaction: Transaction to categorize
            max_retries: Number of times to retry on failure (default: 2, reduced from 3)

        Returns:
            Tuple of (category_name, confidence, reasoning)
        """
        # Build prompt
        prompt = f"""You are a financial transaction categorizer.

Given this transaction:
- Description: {transaction.description}
- Amount: £{transaction.amount}
- Date: {transaction.date}
- Type: {transaction.transaction_type}

Categorize it into ONE of the available categories below.

Return ONLY a JSON object with this exact structure:
{{
  "category": "Category Name",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}}

Confidence should be 0.0 to 1.0 (1.0 = certain, 0.5 = guess).
"""

        import time
        last_error = None

        for attempt in range(max_retries):
            try:
                # Use prompt caching for category list (90% cost reduction!)
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    timeout=20.0,  # 20 second timeout per request (reduced from 30s)
                    system=[
                        {
                            "type": "text",
                            "text": "You are a UK personal finance expert helping categorize bank transactions.",
                        },
                        {
                            "type": "text",
                            "text": self._category_context,
                            "cache_control": {"type": "ephemeral"},  # CACHE THIS!
                        },
                    ],
                    messages=[{"role": "user", "content": prompt}],
                )

                # Parse response
                response_text = response.content[0].text.strip()

                # Extract JSON (handle markdown code blocks)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                result = json.loads(response_text)

                category = result.get("category", "Uncategorized")
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "No reasoning provided")

                return category, confidence, reasoning

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Rate limit error - wait and retry
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    wait_time = 3 + (attempt * 2)  # 3s, 5s (reduced from 5s, 10s, 15s)
                    print(f"[Retry {attempt + 1}/{max_retries}] Rate limit - waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Timeout error - retry
                elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
                    print(f"[Retry {attempt + 1}/{max_retries}] Timeout - retrying...")
                    time.sleep(2)
                    continue

                # Network/connection error - retry
                elif "connection" in error_str.lower() or "network" in error_str.lower():
                    print(f"[Retry {attempt + 1}/{max_retries}] Network error - retrying...")
                    time.sleep(3)
                    continue

                # Other errors - log and retry
                else:
                    print(f"[Retry {attempt + 1}/{max_retries}] Error: {error_str[:100]}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        break

        # All retries failed
        print(f"❌ AI categorization failed after {max_retries} attempts: {last_error}")
        return "Uncategorized", 0.0, f"Error after {max_retries} retries: {str(last_error)[:200]}"

    def categorize_transactions_batch(
        self, transactions: List[Transaction], max_retries: int = 2
    ) -> List[Tuple[str, float, str]]:
        """
        Categorize multiple transactions in a SINGLE API call (true batching).

        Args:
            transactions: List of transactions to categorize (recommended: 20-50)
            max_retries: Number of times to retry on failure

        Returns:
            List of (category, confidence, reasoning) tuples, one per transaction
        """
        import time

        # Build batch prompt with all transactions
        txn_list = []
        for i, txn in enumerate(transactions, 1):
            txn_list.append(f"""
Transaction {i}:
- Description: {txn.description}
- Amount: £{txn.amount}
- Date: {txn.date}
- Type: {txn.transaction_type}""")

        transactions_text = "\n".join(txn_list)

        prompt = f"""Categorize ALL {len(transactions)} transactions below.

{transactions_text}

CRITICAL: Your response MUST be ONLY a JSON array. Do NOT include any explanatory text, markdown formatting, or anything except the JSON array itself.

Return a JSON array with exactly {len(transactions)} objects in the same order:
[
  {{"category": "Category Name", "confidence": 0.95, "reasoning": "Brief explanation"}},
  {{"category": "Category Name", "confidence": 0.85, "reasoning": "Brief explanation"}}
]

Rules:
- Return EXACTLY {len(transactions)} categorizations
- Keep the EXACT same order as input
- Confidence: 0.0 to 1.0 (1.0 = certain, 0.5 = guess)
- NO text before or after the JSON array
- NO markdown code blocks
- NO newlines inside strings (use spaces instead)
- Keep reasoning brief (max 50 characters)
- JUST the raw JSON array"""

        last_error = None

        for attempt in range(max_retries):
            try:
                # Use prompt caching for category list
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,  # Haiku's maximum output tokens
                    timeout=30.0,  # Longer timeout for batch processing
                    system=[
                        {
                            "type": "text",
                            "text": "You are a UK personal finance expert helping categorize bank transactions.",
                        },
                        {
                            "type": "text",
                            "text": self._category_context,
                            "cache_control": {"type": "ephemeral"},  # CACHE THIS!
                        },
                    ],
                    messages=[{"role": "user", "content": prompt}],
                )

                # Parse response
                response_text = response.content[0].text.strip()

                # Extract JSON (handle markdown code blocks and leading text)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                else:
                    # Strip any text before the first '[' (Claude often adds intro text)
                    if '[' in response_text:
                        response_text = response_text[response_text.index('['):]
                    # Strip any text after the last ']'
                    if ']' in response_text:
                        response_text = response_text[:response_text.rindex(']') + 1]

                # Try to parse JSON
                try:
                    results_array = json.loads(response_text)
                except json.JSONDecodeError as json_err:
                    # If JSON parsing fails due to control characters, try to repair and retry
                    if "Invalid control character" in str(json_err):
                        print(f"⚠️ Repairing JSON with control characters...")
                        # More aggressive cleaning - escape control characters properly
                        import re

                        # Replace literal newlines, tabs, returns with escaped versions
                        # But only inside JSON string values (between quotes)
                        def escape_control_chars(match):
                            text = match.group(0)
                            # Escape control characters
                            text = text.replace('\n', '\\n')
                            text = text.replace('\r', '\\r')
                            text = text.replace('\t', '\\t')
                            text = text.replace('\b', '\\b')
                            text = text.replace('\f', '\\f')
                            return text

                        # Find all string values in JSON and escape control chars
                        # Pattern matches: "key": "value with potential\ncontrol chars"
                        response_text_repaired = re.sub(
                            r'"[^"]*"(?=\s*[:,\]\}])',  # Match quoted strings before : or , or ] or }
                            escape_control_chars,
                            response_text
                        )

                        try:
                            results_array = json.loads(response_text_repaired)
                            print(f"✓ JSON repaired successfully")
                        except json.JSONDecodeError as json_err2:
                            print(f"❌ JSON repair failed: {json_err2}")
                            print(f"Response preview: {response_text[:300]}...")
                            raise ValueError(f"Invalid JSON response from AI: {json_err2}")
                    else:
                        # Different JSON error, log and raise
                        print(f"⚠️ JSON parsing failed: {json_err}")
                        print(f"Response preview: {response_text[:200]}...")
                        raise ValueError(f"Invalid JSON response from AI: {json_err}")

                # Handle result count mismatches gracefully
                if len(results_array) != len(transactions):
                    print(f"⚠️ Warning: Expected {len(transactions)} results, got {len(results_array)}")

                    # If we got fewer results, pad with Uncategorized
                    while len(results_array) < len(transactions):
                        results_array.append({
                            "category": "Uncategorized",
                            "confidence": 0.0,
                            "reasoning": "AI skipped this transaction"
                        })

                    # If we got more results, truncate
                    if len(results_array) > len(transactions):
                        results_array = results_array[:len(transactions)]

                # Extract results
                categorizations = []
                for result in results_array:
                    category = result.get("category", "Uncategorized")
                    confidence = float(result.get("confidence", 0.5))
                    reasoning = result.get("reasoning", "No reasoning provided")
                    categorizations.append((category, confidence, reasoning))

                return categorizations

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Rate limit error - wait and retry
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    wait_time = 3 + (attempt * 2)
                    print(f"[Batch Retry {attempt + 1}/{max_retries}] Rate limit - waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Timeout error - retry
                elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
                    print(f"[Batch Retry {attempt + 1}/{max_retries}] Timeout - retrying...")
                    time.sleep(2)
                    continue

                # Other errors - log and retry
                else:
                    print(f"[Batch Retry {attempt + 1}/{max_retries}] Error: {error_str[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        break

        # All retries failed - return uncategorized for all
        print(f"❌ Batch AI categorization failed after {max_retries} attempts: {last_error}")
        return [("Uncategorized", 0.0, f"Batch error: {str(last_error)[:100]}") for _ in transactions]

    def categorize_batch(
        self, transactions: List[Transaction], batch_size: int = 10
    ) -> List[Tuple[Transaction, str, float, str]]:
        """
        Categorize multiple transactions (legacy method - calls individual categorization).

        Args:
            transactions: List of transactions to categorize
            batch_size: Number of transactions to process in parallel (not implemented yet)

        Returns:
            List of (transaction, category, confidence, reasoning) tuples
        """
        results = []

        for i, txn in enumerate(transactions):
            print(f"AI categorizing {i+1}/{len(transactions)}: {txn.description[:40]}...")
            category, confidence, reasoning = self.categorize_transaction(txn)
            results.append((txn, category, confidence, reasoning))

        return results

    def estimate_cost(self, num_transactions: int) -> dict:
        """
        Estimate cost for categorizing transactions.

        Args:
            num_transactions: Number of transactions to categorize

        Returns:
            Dictionary with cost breakdown
        """
        # Haiku pricing (as of 2025)
        INPUT_COST_CACHED = 0.03 / 1_000_000  # $0.03 per 1M cached tokens
        INPUT_COST_UNCACHED = 0.25 / 1_000_000  # $0.25 per 1M uncached tokens
        OUTPUT_COST = 1.25 / 1_000_000  # $1.25 per 1M output tokens

        # Estimates
        category_context_tokens = len(self._category_context) // 4  # ~4 chars/token
        prompt_tokens_per_txn = 100  # Transaction description + prompt
        output_tokens_per_txn = 50  # JSON response

        # First request: No cache
        first_request_cost = (
            (category_context_tokens + prompt_tokens_per_txn) * INPUT_COST_UNCACHED
            + output_tokens_per_txn * OUTPUT_COST
        )

        # Subsequent requests: Cached category context
        subsequent_cost = (
            category_context_tokens * INPUT_COST_CACHED
            + prompt_tokens_per_txn * INPUT_COST_UNCACHED
            + output_tokens_per_txn * OUTPUT_COST
        )

        total_cost = first_request_cost + (num_transactions - 1) * subsequent_cost

        return {
            "num_transactions": num_transactions,
            "estimated_total_cost_usd": round(total_cost, 4),
            "cost_per_transaction_usd": round(total_cost / num_transactions, 6),
            "category_context_tokens": category_context_tokens,
            "prompt_caching_enabled": True,
            "savings_vs_no_cache": round(
                (num_transactions * (category_context_tokens * INPUT_COST_UNCACHED))
                - (first_request_cost + (num_transactions - 1) * category_context_tokens * INPUT_COST_CACHED),
                4,
            ),
        }


def quick_categorize(
    transaction: Transaction,
    categories: List[Category],
    api_key: Optional[str] = None,
) -> Tuple[str, float, str]:
    """
    Quick helper to categorize a single transaction.

    Args:
        transaction: Transaction to categorize
        categories: List of available categories
        api_key: Anthropic API key

    Returns:
        Tuple of (category, confidence, reasoning)
    """
    engine = ClaudeCategorizationEngine(categories, api_key)
    return engine.categorize_transaction(transaction)

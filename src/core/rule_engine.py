"""
Rule-based transaction categorization engine.

Applies pattern-matching rules to categorize transactions instantly (no AI cost).
"""
import re
from typing import List, Optional, Tuple

from ..data.models import Rule, Transaction


class RuleEngine:
    """Rule-based categorization engine using pattern matching."""

    def __init__(self, rules: List[Rule]):
        """
        Initialize rule engine with list of rules.

        Args:
            rules: List of Rule objects (no sorting - checked in order)
        """
        self.rules = rules

    def match_transaction(
        self, transaction: Transaction
    ) -> Optional[Tuple[str, str, int]]:
        """
        Try to categorize transaction using rules with whole-word token matching.

        Args:
            transaction: Transaction to categorize

        Returns:
            Tuple of (category_id, matched_pattern, rule_priority) if match found,
            None if no rules match
        """
        description = transaction.description.upper()  # Case-insensitive matching

        for rule in self.rules:
            if self._matches_pattern(description, rule.pattern):
                return (rule.category_id, rule.pattern, rule.priority)

        return None

    def _split_alphanumeric_smart(self, tokens: List[str]) -> List[str]:
        """
        Split tokens on alphanumeric boundaries with smart threshold.

        Only splits if there are 4+ consecutive letters before a number.
        This preserves short codes like O2, F1, U22 while splitting tracking numbers.

        Args:
            tokens: List of tokens to process

        Returns:
            List of tokens with smart alphanumeric splitting applied

        Examples:
            ['FEDEX395224543'] → ['FEDEX', '395224543'] (5 letters, split)
            ['BOLT123'] → ['BOLT', '123'] (4 letters, split)
            ['AMAZON123'] → ['AMAZON', '123'] (6 letters, split)
            ['O2'] → ['O2'] (1 letter, preserved)
            ['F1'] → ['F1'] (1 letter, preserved)
            ['U22'] → ['U22'] (1 letter, preserved)
            ['EUO2511021744'] → ['EUO', '2511021744'] (3 letters, split)
        """
        import re

        result = []
        for token in tokens:
            # Match: 4+ letters followed by digits
            # Example: FEDEX395224543 → groups: ('FEDEX', '395224543')
            match = re.match(r'^([A-Z]{4,})(\d+.*)$', token)

            if match:
                # Split: 4+ letters before numbers
                result.extend([match.group(1), match.group(2)])
            else:
                # Keep as-is: short codes (O2, F1, U22) or no numbers
                result.append(token)

        return result

    def _matches_pattern(self, description: str, pattern: str) -> bool:
        """
        Check if description matches pattern using WHOLE-WORD token matching.

        NEW LOGIC (Dec 1, 2025 - Added smart alphanumeric splitting):
        - Tokenizes both description and pattern into words
        - Pattern must match as complete words/tokens (not substrings)
        - Delimiters: space, asterisk (*), and dot (.)
        - Smart alphanumeric splitting: 4+ letters before number → split
        - Strips trailing punctuation from description tokens when comparing
        - Preserves: hyphens, slashes in middle of words (e.g., "CO-OP", "COM/BILL")
        - Preserves: short codes (O2, F1, U22) without splitting

        Examples:
          Pattern "NETFLIX" matches "PAYPAL *NETFLIX.COM" ✓ (NETFLIX is a token after dot split)
          Pattern "TFL" does NOT match "NETFLIX" ✗ (TFL is inside NETFLIX)
          Pattern "TFL" matches "TFL TRAVEL" ✓ (TFL is a whole word)
          Pattern "BOLT" matches "BOLT.EUO2511021744" ✓ (dot is now a delimiter)
          Pattern "FEDEX" matches "FEDEX395224543" ✓ (4+ letters, alphanumeric split)
          Pattern "O2" matches "O2 MOBILE" ✓ (short code preserved)
          Pattern "F1" matches "F1 GRAND PRIX" ✓ (short code preserved)
          Pattern "CO-OP" matches "CO-OP FOOD" ✓ (hyphen preserved)
          Pattern "APPLE" matches "APPLE.COM/BILL" ✓ (dot splits tokens)
          Pattern "CLEARTHREAD STARLI" matches "CLEARTHREAD STARLI, INITIAL PAYMENT" ✓ (comma ignored)
          Pattern "FOA PEACE IN PALESTINE" matches "FOA PEACE IN , PALESTINE , LEICESTER" ✓ (commas ignored)

        Args:
            description: Transaction description (uppercase)
            pattern: Pattern to match (will be uppercased)

        Returns:
            True if pattern matches as whole word, False otherwise
        """
        import re

        pattern_upper = pattern.upper().strip()

        # Tokenize description into words using MINIMAL delimiters
        # Delimiters: space (whitespace), asterisk (bank separator), dot (domain separator), underscore
        # This preserves: hyphens, commas, slashes, ampersands, parentheses, etc.
        description_tokens = re.split(r'[\s*\._]+', description.upper())

        # Remove empty tokens
        description_tokens = [t for t in description_tokens if t]

        # Strip trailing punctuation from description tokens
        # This fixes: "CLEARTHREAD STARLI," → "CLEARTHREAD STARLI" matching
        # But preserves: "CO-OP" and "APPLE.COM/BILL" (punctuation in middle)
        description_tokens_normalized = [
            re.sub(r'[,;:.!?()]+$', '', token)  # Remove trailing punctuation
            for token in description_tokens
        ]

        # Remove empty tokens created by standalone punctuation
        # This fixes: "FOA PEACE IN , PALESTINE" where commas become empty strings
        description_tokens_normalized = [t for t in description_tokens_normalized if t]

        # Smart alphanumeric boundary splitting
        # Split tokens on letter-to-number transitions IF 4+ letters before number
        # Examples:
        #   FEDEX395224543 (5 letters) → ['FEDEX', '395224543']
        #   BOLT123 (4 letters) → ['BOLT', '123']
        #   O2 (1 letter) → ['O2'] (preserved)
        #   F1 (1 letter) → ['F1'] (preserved)
        #   U22 (1 letter) → ['U22'] (preserved)
        description_tokens_normalized = self._split_alphanumeric_smart(description_tokens_normalized)

        # Check if pattern appears as a complete token
        # Pattern can be multi-word (e.g., "AMAZON PRIME")
        pattern_tokens = re.split(r'[\s*\._]+', pattern_upper)
        pattern_tokens = [t for t in pattern_tokens if t]

        # Apply same smart alphanumeric splitting to pattern tokens
        # This ensures patterns like "HIJAZIALAA67" match "HIJAZIALAA67 PAYMENT"
        pattern_tokens = self._split_alphanumeric_smart(pattern_tokens)

        # If single-word pattern, check if it's in description tokens
        if len(pattern_tokens) == 1:
            return pattern_tokens[0] in description_tokens_normalized

        # If multi-word pattern, check if sequence appears in description
        # E.g., pattern "AMAZON PRIME" should match "PAYPAL *AMAZON PRIME LTD"
        for i in range(len(description_tokens_normalized) - len(pattern_tokens) + 1):
            if description_tokens_normalized[i:i+len(pattern_tokens)] == pattern_tokens:
                return True

        return False

    def categorize_batch(
        self, transactions: List[Transaction]
    ) -> Tuple[List[Transaction], List[Transaction]]:
        """
        Categorize a batch of transactions using rules.

        Args:
            transactions: List of transactions to categorize

        Returns:
            Tuple of (categorized_transactions, uncategorized_transactions)
        """
        categorized = []
        uncategorized = []

        for txn in transactions:
            # Skip already categorized transactions
            if txn.category and txn.category_confirmed:
                categorized.append(txn)
                continue

            # Try to match with rules
            match = self.match_transaction(txn)
            if match:
                category_id, pattern, priority = match
                txn.category = category_id
                txn.category_confidence = 1.0  # Rule match = 100% confidence
                txn.category_confirmed = False  # User should still review
                categorized.append(txn)
            else:
                uncategorized.append(txn)

        return categorized, uncategorized

    def add_rule(self, rule: Rule) -> None:
        """
        Add a new rule to the engine.

        Args:
            rule: Rule to add
        """
        self.rules.append(rule)
        # Re-sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule from the engine.

        Args:
            rule_id: ID of rule to remove

        Returns:
            True if rule was removed, False if not found
        """
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        return len(self.rules) < original_count

    def get_matching_rules(self, transaction: Transaction) -> List[Tuple[Rule, str]]:
        """
        Get all rules that match a transaction (for debugging/analysis).

        Args:
            transaction: Transaction to check

        Returns:
            List of (rule, matched_pattern) tuples
        """
        description = transaction.description.upper()
        matches = []

        for rule in self.rules:
            if self._matches_pattern(description, rule.pattern):
                matches.append((rule, rule.pattern))

        return matches


def create_default_rules(categories: dict) -> List[Rule]:
    """
    Create a set of common default rules for UK transactions.

    Args:
        categories: Dictionary mapping category names to category IDs

    Returns:
        List of Rule objects
    """
    rules = []

    # Helper to create rule
    def make_rule(pattern: str, category_name: str, priority: int = 0) -> Rule:
        category_id = categories.get(category_name, "Uncategorized")
        return Rule(pattern=pattern, category_id=category_id, priority=priority)

    # ==================== GROCERIES ====================
    rules.extend([
        make_rule("TESCO", "Supermarket", priority=10),
        make_rule("SAINSBURY", "Supermarket", priority=10),
        make_rule("ASDA", "Supermarket", priority=10),
        make_rule("MORRISONS", "Supermarket", priority=10),
        make_rule("WAITROSE", "Supermarket", priority=10),
        make_rule("ALDI", "Supermarket", priority=10),
        make_rule("LIDL", "Supermarket", priority=10),
        make_rule("M&S SIMPLY FOOD", "Supermarket", priority=10),
        make_rule("CO-OP", "Supermarket", priority=10),
    ])

    # ==================== DINING OUT ====================
    rules.extend([
        make_rule("STARBUCKS", "Coffee/Tea", priority=10),
        make_rule("COSTA", "Coffee/Tea", priority=10),
        make_rule("PRET A MANGER", "Coffee/Tea", priority=10),
        make_rule("CAFFE NERO", "Coffee/Tea", priority=10),
        make_rule("GREGGS", "Fast Food", priority=10),
        make_rule("MCDONALD", "Fast Food", priority=10),
        make_rule("BURGER KING", "Fast Food", priority=10),
        make_rule("KFC", "Fast Food", priority=10),
        make_rule("SUBWAY", "Fast Food", priority=10),
        make_rule("NANDO", "Restaurants", priority=10),
        make_rule("PIZZA EXPRESS", "Restaurants", priority=10),
        make_rule("WAGAMAMA", "Restaurants", priority=10),
    ])

    # ==================== TRANSPORT ====================
    rules.extend([
        make_rule("TFL", "Public Transport", priority=10),
        make_rule("UBER", "Public Transport", priority=10),
        make_rule("BOLT", "Public Transport", priority=10),
        make_rule("TRAINLINE", "Public Transport", priority=10),
        make_rule("NATIONAL RAIL", "Public Transport", priority=10),
        make_rule("SHELL", "Fuel/Petrol", priority=10),
        make_rule("BP", "Fuel/Petrol", priority=10),
        make_rule("ESSO", "Fuel/Petrol", priority=10),
        make_rule("TEXACO", "Fuel/Petrol", priority=10),
    ])

    # ==================== UTILITIES & BILLS ====================
    rules.extend([
        make_rule("BRITISH GAS", "Utilities", priority=10),
        make_rule("EDF ENERGY", "Utilities", priority=10),
        make_rule("SCOTTISH POWER", "Utilities", priority=10),
        make_rule("THAMES WATER", "Utilities", priority=10),
        make_rule("BT GROUP", "Internet", priority=10),
        make_rule("SKY", "Subscriptions", priority=10),
        make_rule("VIRGIN MEDIA", "Internet", priority=10),
        make_rule("EE LIMITED", "Phone", priority=10),
        make_rule("VODAFONE", "Phone", priority=10),
        make_rule("THREE", "Phone", priority=10),
        make_rule("O2", "Phone", priority=10),
    ])

    # ==================== SUBSCRIPTIONS ====================
    rules.extend([
        make_rule("NETFLIX.COM", "Streaming Services", priority=10),
        make_rule("SPOTIFY", "Streaming Services", priority=10),
        make_rule("AMAZON PRIME", "Subscriptions", priority=10),
        make_rule("DISNEY PLUS", "Streaming Services", priority=10),
        make_rule("APPLE.COM/BILL", "Subscriptions", priority=10),
    ])

    # ==================== SHOPPING ====================
    rules.extend([
        make_rule("AMAZON.CO.UK", "Shopping", priority=5),
        make_rule("AMZN MKTP", "Shopping", priority=5),
        make_rule("EBAY", "Shopping", priority=5),
        make_rule("ARGOS", "Shopping", priority=5),
        make_rule("JOHN LEWIS", "Shopping", priority=5),
        make_rule("NEXT RETAIL", "Clothing", priority=10),
        make_rule("ZARA", "Clothing", priority=10),
        make_rule("H&M", "Clothing", priority=10),
        make_rule("PRIMARK", "Clothing", priority=10),
    ])

    # ==================== HEALTHCARE ====================
    rules.extend([
        make_rule("BOOTS", "Pharmacy", priority=10),
        make_rule("SUPERDRUG", "Pharmacy", priority=10),
        make_rule("PUREGYM", "Gym/Fitness", priority=10),
        make_rule("DAVID LLOYD", "Gym/Fitness", priority=10),
    ])

    # ==================== INCOME ====================
    rules.extend([
        make_rule("SALARY", "Salary", priority=10),
        make_rule("WAGE", "Salary", priority=10),
        make_rule("REFUND", "Refunds", priority=10),
    ])

    return rules

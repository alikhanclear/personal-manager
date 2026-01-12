"""
Default category taxonomy for Personal Manager.

These categories are based on common spending patterns.
Users can customize these through the UI.
"""
from typing import List, Tuple

# Format: (name, parent_name, color, icon, monthly_budget)
# parent_name=None means top-level category
DEFAULT_CATEGORIES: List[Tuple[str, str | None, str, str, float | None]] = [
    # ==================== INCOME ====================
    ("Income", None, "#2ecc71", "💰", None),
    ("Salary", "Income", "#27ae60", "💵", None),
    ("Freelance", "Income", "#16a085", "💼", None),
    ("Investments", "Income", "#1abc9c", "📈", None),
    ("Refunds", "Income", "#3498db", "↩️", None),

    # ==================== HOUSING ====================
    ("Housing", None, "#e74c3c", "🏠", 1500.0),
    ("Rent/Mortgage", "Housing", "#c0392b", "🏡", 1200.0),
    ("Utilities", "Housing", "#e67e22", "💡", 150.0),
    ("Council Tax", "Housing", "#d35400", "🏛️", 150.0),
    ("Home Insurance", "Housing", "#f39c12", "🛡️", 50.0),

    # ==================== GROCERIES & FOOD ====================
    ("Groceries", None, "#9b59b6", "🛒", 400.0),
    ("Supermarket", "Groceries", "#8e44ad", "🏪", 350.0),
    ("Convenience Store", "Groceries", "#9b59b6", "🏬", 50.0),

    ("Dining Out", None, "#e74c3c", "🍽️", 200.0),
    ("Restaurants", "Dining Out", "#c0392b", "🍴", 150.0),
    ("Fast Food", "Dining Out", "#e67e22", "🍔", 50.0),
    ("Coffee/Tea", "Dining Out", "#d35400", "☕", 40.0),

    # ==================== TRANSPORT ====================
    ("Transport", None, "#3498db", "🚗", 300.0),
    ("Fuel/Petrol", "Transport", "#2980b9", "⛽", 150.0),
    ("Public Transport", "Transport", "#3498db", "🚇", 100.0),
    ("Parking", "Transport", "#5dade2", "🅿️", 30.0),
    ("Car Insurance", "Transport", "#85c1e9", "🚙", 80.0),
    ("Car Maintenance", "Transport", "#aed6f1", "🔧", 50.0),

    # ==================== SHOPPING ====================
    ("Shopping", None, "#e91e63", "🛍️", 300.0),
    ("Clothing", "Shopping", "#c2185b", "👕", 100.0),
    ("Electronics", "Shopping", "#ad1457", "💻", 150.0),
    ("Household Items", "Shopping", "#880e4f", "🏠", 50.0),
    ("Books", "Shopping", "#f06292", "📚", 30.0),

    # ==================== HEALTH & WELLNESS ====================
    ("Health", None, "#4caf50", "🏥", 150.0),
    ("Pharmacy", "Health", "#388e3c", "💊", 50.0),
    ("Gym/Fitness", "Health", "#66bb6a", "💪", 50.0),
    ("Healthcare", "Health", "#81c784", "🩺", 50.0),

    # ==================== ENTERTAINMENT ====================
    ("Entertainment", None, "#ff9800", "🎬", 150.0),
    ("Streaming Services", "Entertainment", "#f57c00", "📺", 40.0),
    ("Movies/Cinema", "Entertainment", "#ff9800", "🎥", 30.0),
    ("Gaming", "Entertainment", "#ffa726", "🎮", 50.0),
    ("Hobbies", "Entertainment", "#ffb74d", "🎨", 50.0),

    # ==================== BILLS & SUBSCRIPTIONS ====================
    ("Bills", None, "#607d8b", "📄", 200.0),
    ("Phone", "Bills", "#546e7a", "📱", 30.0),
    ("Internet", "Bills", "#78909c", "🌐", 40.0),
    ("Subscriptions", "Bills", "#90a4ae", "📋", 50.0),

    # ==================== PERSONAL CARE ====================
    ("Personal Care", None, "#ff5722", "✨", 100.0),
    ("Haircut/Salon", "Personal Care", "#f4511e", "💇", 40.0),
    ("Beauty Products", "Personal Care", "#ff6f00", "💄", 50.0),

    # ==================== SAVINGS & INVESTMENTS ====================
    ("Savings", None, "#009688", "🏦", 500.0),
    ("Emergency Fund", "Savings", "#00897b", "🚨", 200.0),
    ("Retirement", "Savings", "#26a69a", "👴", 300.0),

    # ==================== TRANSFERS ====================
    ("Transfers", None, "#795548", "↔️", None),
    ("To Savings", "Transfers", "#6d4c41", "➡️", None),
    ("From Savings", "Transfers", "#8d6e63", "⬅️", None),
    ("Between Accounts", "Transfers", "#a1887f", "🔄", None),

    # ==================== OTHER ====================
    ("Other", None, "#9e9e9e", "❓", 100.0),
    ("Uncategorized", "Other", "#757575", "🤷", None),
    ("Gifts", "Other", "#bdbdbd", "🎁", 50.0),
    ("Charity", "Other", "#e0e0e0", "❤️", 50.0),
]


def get_category_hierarchy() -> dict:
    """
    Get category hierarchy as nested dictionary.

    Returns:
        Dictionary with parent categories as keys and child categories as values
    """
    hierarchy = {}
    for name, parent, color, icon, budget in DEFAULT_CATEGORIES:
        if parent is None:
            if name not in hierarchy:
                hierarchy[name] = []
        else:
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(name)

    return hierarchy


def get_top_level_categories() -> List[str]:
    """Get list of top-level category names."""
    return [name for name, parent, _, _, _ in DEFAULT_CATEGORIES if parent is None]


def get_category_info(category_name: str) -> dict | None:
    """
    Get information about a specific category.

    Args:
        category_name: Name of category to look up

    Returns:
        Dictionary with category info or None if not found
    """
    for name, parent, color, icon, budget in DEFAULT_CATEGORIES:
        if name == category_name:
            return {
                "name": name,
                "parent": parent,
                "color": color,
                "icon": icon,
                "budget_monthly": budget,
            }
    return None

"""
Optimization Engine

Selects the best vendor allocation based on cost, risk, and capacity.
"""

import pandas as pd


class OptimizationEngine:

    def __init__(self):
        pass

    def choose_vendor(self, vendor_table: pd.DataFrame):
        """
        Select best vendor based on simple scoring rule.
        """

        vendor_table["score"] = (
            vendor_table["cost"] * 0.4 +
            vendor_table["risk"] * 0.4 +
            vendor_table["capacity"] * -0.2
        )

        return vendor_table.sort_values("score").iloc[0]


def example_data():

    return pd.DataFrame({
        "vendor": ["A", "B", "C"],
        "cost": [12000, 11000, 14000],
        "risk": [0.2, 0.4, 0.1],
        "capacity": [7, 5, 9]
    })


if __name__ == "__main__":
    print("Optimization engine ready.")

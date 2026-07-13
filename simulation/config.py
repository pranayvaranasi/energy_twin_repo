"""
Centralized Configuration & Domain Constants for the Energy Digital Twin.
Ensures single-source-of-truth for all macroeconomic and physical logistics parameters.
"""

# Macroeconomic & CGE Constants
CRUDE_IMPORT_DEPENDENCY = 0.88      
TPES_COAL_SHARE = 0.6021            
TPES_CRUDE_SHARE = 0.2983           
BASE_BRENT_PRICE = 80.0             

# Strategic Petroleum Reserve (SPR) Constraints
SPR_TOTAL_CAPACITY_MMT = 5.33
SPR_CURRENT_BARRELS_MILLION = 25.0
SPR_BASE_BUFFER_DAYS = 9.5
SPOT_MARKET_LAG_DAYS = 5

# Maritime Logistics & Insurance
BASE_FREIGHT_RATE_USD = 2.50
SAFE_WATER_WAR_RISK_PCT = 0.05
RED_SEA_WAR_RISK_PCT = 1.25
HORMUZ_WAR_RISK_PCT = 2.50
AVERAGE_VESSEL_SPEED_KMH = 25.0  # ~13.5 knots

# Enterprise Financials
TIER_1_DAILY_REVENUE = 15_000_000
SLA_PENALTY_MULTIPLIER = 125_000
EXPEDITING_COST_MULTIPLIER = 300_000

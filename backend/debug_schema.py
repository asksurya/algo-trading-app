import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.schemas.portfolio import PortfolioSummaryResponse
    print(f"Successfully imported PortfolioSummaryResponse: {PortfolioSummaryResponse}")
    print(f"Is subclass of BaseModel: {PortfolioSummaryResponse.__mro__}")
    
    # Try to instantiate
    from datetime import datetime
    instance = PortfolioSummaryResponse(
        total_equity=100.0,
        cash_balance=100.0,
        positions_value=0.0,
        daily_pnl=0.0,
        daily_return_pct=0.0,
        total_pnl=0.0,
        total_return_pct=0.0,
        num_positions=0,
        last_updated=datetime.now()
    )
    print("Successfully instantiated model")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

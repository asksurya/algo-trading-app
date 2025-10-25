"""
Apply live trading migration (007) to add live_strategies and signal_history tables.
"""
import sys
import subprocess
from pathlib import Path

def run_migration():
    """Run the live trading migration."""
    print("=" * 80)
    print("Applying Live Trading Migration (007)")
    print("=" * 80)
    print()
    
    backend_dir = Path(__file__).parent
    
    try:
        print("Running Alembic upgrade to head...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Migration applied successfully!")
            print()
            print("Migration Output:")
            print(result.stdout)
            
            print()
            print("=" * 80)
            print("Live Trading Tables Created:")
            print("=" * 80)
            print("✓ live_strategies - Configuration for automated trading strategies")
            print("✓ signal_history - Historical record of detected signals")
            print()
            print("Features Added:")
            print("- Continuous strategy monitoring")
            print("- Automated signal detection")
            print("- Position tracking and management")
            print("- Risk parameter configuration")
            print("- Performance metrics tracking")
            print()
            return True
        else:
            print("✗ Migration failed!")
            print()
            print("Error Output:")
            print(result.stderr)
            print()
            print("Standard Output:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"✗ Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

"""Legacy entry point for the current SK hynix DART pipeline."""
from src.analyze import analyze
from src.collect import collect
from src.dashboard import build

if __name__ == "__main__":
    collect()
    analyze()
    build()

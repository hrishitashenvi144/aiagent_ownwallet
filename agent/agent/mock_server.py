"""Mock server providing pre-baked responses conforming to shared/openapi.yaml for Day 1 development."""
from fastapi import FastAPI
from agent.main import app as real_app

# The real app already implements mock fallbacks when contracts/DB are not active
app = real_app

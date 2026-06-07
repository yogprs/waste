pip install playwright pytest-playwright pytest
playwright install chromium

# terminal terpisah
python app.py          
# jalankan E2E tests
pytest tests/e2e/ -v
# jalankan unit tests
pytest tests/unit/ -v
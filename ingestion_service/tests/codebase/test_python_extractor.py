import pytest
from ingestion_service.src.core.extractors import python_extractor

# Sample Python code to test extraction
SAMPLE_CODE = """
import os
import sys

class MyClass:
    def method_a(self):
        print("Hello")
        
def standalone_function():
    MyClass().method_a()
"""

@pytest.fixture
def extractor():
    return python_extractor.PythonASTExtractor()

def test_module_extraction(extractor):
    result = extractor.extract_module(SAMPLE_CODE, "sample.py")
    assert result["artifact_type"] == "MODULE"
    assert result["canonical_id"] == "sample.py"

def test_class_extraction(extractor):
    classes = extractor.extract_classes(SAMPLE_CODE, "sample.py")
    assert any(c["name"] == "MyClass" for c in classes)

def test_function_extraction(extractor):
    functions = extractor.extract_functions(SAMPLE_CODE, "sample.py")
    names = [f["name"] for f in functions]
    assert "standalone_function" in names

def test_method_extraction(extractor):
    methods = extractor.extract_methods(SAMPLE_CODE, "sample.py")
    names = [m["name"] for m in methods]
    assert "method_a" in names

def test_import_extraction(extractor):
    imports = extractor.extract_imports(SAMPLE_CODE, "sample.py")
    names = [i["name"] for i in imports]
    assert "os" in names
    assert "sys" in names

def test_call_extraction(extractor):
    calls = extractor.extract_calls(SAMPLE_CODE, "sample.py")
    names = [c["name"] for c in calls]
    assert "method_a" in names

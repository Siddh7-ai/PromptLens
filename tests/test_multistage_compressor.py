import pytest
from src.classifier import TaskCategory, TaskClassifier
from src.parser import ASTParser, SymbolKind
from src.graph import DependencyGraph
from src.semantic import LightweightEmbedder, RelevanceScorer
from src.allocator import BudgetOptimizer
from src.compress.pipeline import PromptLensPipeline


class TestTaskClassifier:
    def setup_method(self):
        self.classifier = TaskClassifier()

    def test_classify_debugging(self):
        text = "Why am I getting this TypeError: Cannot read properties of undefined in user controller?"
        cat, conf = self.classifier.classify(text)
        assert cat == TaskCategory.DEBUGGING
        assert conf > 0.6

    def test_classify_code_generation(self):
        text = "Create a REST API for managing students using Node.js and Express."
        cat, _ = self.classifier.classify(text)
        assert cat == TaskCategory.CODE_GENERATION

    def test_classify_code_modification(self):
        text = "Add authentication middleware to this application."
        cat, _ = self.classifier.classify(text)
        assert cat == TaskCategory.CODE_MODIFICATION

    def test_classify_refactoring(self):
        text = "Refactor this code to follow SOLID principles and clean up duplicated logic."
        cat, _ = self.classifier.classify(text)
        assert cat == TaskCategory.REFACTORING

    def test_classify_test_generation(self):
        text = "Write unit tests for this student controller using pytest."
        cat, _ = self.classifier.classify(text)
        assert cat == TaskCategory.TEST_GENERATION

    def test_classify_code_review(self):
        text = "Review this code for security vulnerabilities, SQL injection, and OWASP issues."
        cat, _ = self.classifier.classify(text)
        assert cat == TaskCategory.CODE_REVIEW

    def test_decompose_prompt(self):
        prompt = """
        Fix the login bug in app.py.
        ```python
        def login(user, pwd):
            return authenticate(user, pwd)
        ```
        ```log
        [ERROR] 14:20:00 - User not found exception
        ```
        """
        decomp = self.classifier.decompose(prompt)
        assert decomp.task_category == TaskCategory.DEBUGGING
        assert len(decomp.code_blocks) == 1
        assert len(decomp.log_blocks) == 1
        assert "app.py" in decomp.detected_files


class TestASTParser:
    def setup_method(self):
        self.parser = ASTParser()

    def test_parse_python_classes_and_functions(self):
        code = """
import os

class Student:
    def __init__(self, name: str):
        self.name = name

    def validate(self) -> bool:
        return len(self.name) > 0

    def save(self):
        db.save(self)

def create_student(name: str):
    s = Student(name)
    if s.validate():
        s.save()
"""
        parsed = self.parser.parse(code, language="python", filepath="student.py")
        assert len(parsed.symbols) >= 4  # Student, __init__, validate, save, create_student
        
        student_cls = next(s for s in parsed.symbols if s.name == "Student")
        assert student_cls.kind == SymbolKind.CLASS
        assert "validate" in student_cls.skeleton_code
        assert "save" in student_cls.skeleton_code

        create_fn = next(s for s in parsed.symbols if s.name == "create_student")
        assert create_fn.kind == SymbolKind.FUNCTION
        assert "Student" in create_fn.dependencies or "save" in create_fn.dependencies

    def test_parse_javascript_routes_and_classes(self):
        code = """
import express from 'express';
const router = express.Router();

router.get('/students', (req, res) => {
    res.json(students);
});

router.post('/students', (req, res) => {
    res.status(201).json({});
});

class StudentService {
    async findStudent(id) {
        return db.find(id);
    }
}
"""
        parsed = self.parser.parse(code, language="javascript", filepath="routes.js")
        route_names = [s.name for s in parsed.symbols if s.kind == SymbolKind.ROUTE]
        assert "GET /students" in route_names
        assert "POST /students" in route_names

        class_sym = next(s for s in parsed.symbols if s.name == "StudentService")
        assert class_sym.kind == SymbolKind.CLASS


class TestDependencyGraph:
    def setup_method(self):
        self.parser = ASTParser()
        self.graph = DependencyGraph()

    def test_dependency_expansion(self):
        code = """
def password_hash(pwd):
    return hash(pwd)

def validate_user(user, pwd):
    return user is not None and password_hash(pwd)

def login(user, pwd):
    if validate_user(user, pwd):
        return True
    return False
"""
        parsed = self.parser.parse(code, language="python", filepath="auth.py")
        self.graph.build_from_files([parsed])

        # Expand around seed 'login'
        expanded = self.graph.expand_neighborhood(["login"], max_hops=2)
        assert "login" in expanded.expanded_symbols
        assert expanded.expanded_symbols["login"] == 1.0
        assert "validate_user" in expanded.expanded_symbols
        assert expanded.expanded_symbols["validate_user"] >= 0.7
        assert "password_hash" in expanded.expanded_symbols
        assert expanded.expanded_symbols["password_hash"] >= 0.4


class TestRelevanceScorerAndEmbedder:
    def setup_method(self):
        self.classifier = TaskClassifier()
        self.parser = ASTParser()
        self.embedder = LightweightEmbedder()
        self.scorer = RelevanceScorer(embedder=self.embedder)

    def test_embedder_similarity(self):
        q = "Add validation to student creation"
        d1 = "def create_student(name): validate(name)"
        d2 = "def delete_old_logs(time): remove()"

        sim1 = self.embedder.compute_similarity(q, d1)
        sim2 = self.embedder.compute_similarity(q, d2)
        assert sim1 > sim2

    def test_relevance_scoring_priority(self):
        code = """
def create_student(req, res):
    # handles student creation
    pass

def delete_student(id):
    pass

def logging_utility(msg):
    pass
"""
        parsed = self.parser.parse(code, language="python", filepath="controller.py")
        decomp = self.classifier.decompose("Add validation to student creation")
        scored = self.scorer.score_symbols(parsed.symbols, decomp)

        assert len(scored) == 3
        assert scored[0].symbol.name == "create_student"
        assert scored[0].total_relevance > scored[-1].total_relevance


class TestEndToEndPipeline:
    def setup_method(self):
        self.pipeline = PromptLensPipeline(default_budget=4000)

    def test_full_pipeline_compression(self):
        prompt = """
Fix the authentication bug in login endpoint.

```python
# filepath: auth_service.py
def hash_password(pwd):
    return "hashed_" + pwd

def validate_credentials(user, pwd):
    hashed = hash_password(pwd)
    return user == "admin" and hashed == "hashed_secret"

def login(user, pwd):
    if validate_credentials(user, pwd):
        return {"status": "ok"}
    raise ValueError("Invalid user or password")

def export_analytics():
    # Unrelated 100 lines of analytics
    pass
```

```log
[ERROR] 12:00:00 ValueError: Invalid user or password at login() in auth_service.py:12
```
"""
        res = self.pipeline.compress(prompt, mode="v5", budget=500)

        assert res.task_category == TaskCategory.DEBUGGING
        assert res.compressed_tokens < res.original_tokens
        assert res.total_savings_pct > 0
        assert len(res.stage_metrics) >= 4
        assert res.retrieval_id is not None
        assert "login" in res.final_prompt

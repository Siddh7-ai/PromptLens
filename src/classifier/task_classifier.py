import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskCategory(str, Enum):
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    DEBUGGING = "debugging"
    CODE_EXPLANATION = "code_explanation"
    REFACTORING = "refactoring"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    GENERAL = "general"


@dataclass
class DecomposedPrompt:
    raw_prompt: str
    user_request: str
    code_blocks: list[dict[str, str]] = field(default_factory=list)
    log_blocks: list[str] = field(default_factory=list)
    doc_blocks: list[str] = field(default_factory=list)
    task_category: TaskCategory = TaskCategory.GENERAL
    confidence: float = 1.0
    detected_files: list[str] = field(default_factory=list)
    detected_symbols: list[str] = field(default_factory=list)


class TaskClassifier:
    """
    Classifies the user intent into one of 7 coding task categories
    and decomposes complex raw prompts into structured parts:
    User Instruction, Code Snippets, Logs, and Documentation.
    """

    PATTERNS: dict[TaskCategory, list[re.Pattern]] = {
        TaskCategory.DEBUGGING: [
            re.compile(r'\b(error|traceback|exception|fix\s+(?:the\s+)?(?:bug|error|issue|crash)|why\s+am\s+i\s+getting|failed\s+to|exit\s+status\s+\d+|cannot\s+find|undefined\s+is\s+not|nullpointer|typeerror|syntaxerror|runtimeerror)\b', re.IGNORECASE),
            re.compile(r'(?:traceback\s+\(most\s+recent\s+call\s+last\):|\[ERROR\]|npm\s+error|yarn\s+error)', re.IGNORECASE),
        ],
        TaskCategory.TEST_GENERATION: [
            re.compile(r'\b(write|generate|create|add)\s+(?:unit\s+)?tests?\b', re.IGNORECASE),
            re.compile(r'\b(pytest|jest|mocha|unittest|vitest|test\s+cases?|coverage|mocking|mock\s+tests?)\b', re.IGNORECASE),
        ],
        TaskCategory.REFACTORING: [
            re.compile(r'\b(refactor|clean\s+up|solid\s+principles?|extract\s+(?:method|class|function)|dry\s+principles?|simplify\s+code|reduce\s+complexity|decouple|optimize\s+structure)\b', re.IGNORECASE),
        ],
        TaskCategory.CODE_REVIEW: [
            re.compile(r'\b(code\s+review|security\s+(?:audit|vulnerabilit(?:y|ies)|check)|vulnerabilities|owasp|sql\s+injection|xss|sanitize|audit\s+this\s+code|best\s+practices?\s+review)\b', re.IGNORECASE),
        ],
        TaskCategory.CODE_EXPLANATION: [
            re.compile(r'\b(explain\s+(?:how|this|what)|walk\s+(?:me\s+)?through|how\s+does\s+this\s+work|understand\s+this|document\s+this|what\s+does\s+(?:this|the\s+following)\s+code\s+do|architectural\s+overview)\b', re.IGNORECASE),
        ],
        TaskCategory.CODE_MODIFICATION: [
            re.compile(r'\b(add|update|modify|change|extend|integrate|implement\s+(?:authentication|feature|auth|endpoint|middleware|support|route|model)|connect\s+to)\b', re.IGNORECASE),
        ],
        TaskCategory.CODE_GENERATION: [
            re.compile(r'\b(create|build|generate|scaffold|write\s+(?:a|an)\s+(?:new\s+)?(?:rest\s+api|script|app|application|service|microservice|function|component|class))\b', re.IGNORECASE),
        ],
    }

    def classify(self, text: str) -> tuple[TaskCategory, float]:
        """
        Classifies coding task based on keyword signatures and intent markers.
        Returns (TaskCategory, confidence score).
        """
        scores: dict[TaskCategory, float] = {cat: 0.0 for cat in TaskCategory}

        # Check for strong error/traceback presence directly in text
        if "Traceback (most recent call last):" in text or "npm error" in text or "Failed to compile" in text:
            scores[TaskCategory.DEBUGGING] += 3.0

        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    weight = 2.0 if category == TaskCategory.DEBUGGING else 1.5
                    scores[category] += len(matches) * weight

        best_cat = max(scores, key=scores.get)
        max_score = scores[best_cat]

        if max_score == 0:
            return TaskCategory.GENERAL, 0.5

        confidence = min(0.99, 0.5 + (max_score / (max_score + 2.0)) * 0.5)
        return best_cat, round(confidence, 2)

    def decompose(self, prompt: str) -> DecomposedPrompt:
        """
        Splits a prompt into:
        1. User Request (Instructions / Query)
        2. Code Blocks (Fenced blocks, inline snippets, file references)
        3. Log / Output Blocks
        4. Documentation / Configs
        """
        # Fast path for raw JSON or large array/object payloads
        stripped_prompt = prompt.strip()
        if (stripped_prompt.startswith("{") and stripped_prompt.endswith("}")) or (stripped_prompt.startswith("[") and stripped_prompt.endswith("]")):
            try:
                import json
                json.loads(stripped_prompt)
                return DecomposedPrompt(
                    raw_prompt=prompt,
                    user_request="",
                    code_blocks=[],
                    log_blocks=[],
                    doc_blocks=[prompt],
                    task_category=TaskCategory.GENERAL,
                    confidence=0.99,
                    detected_files=[],
                    detected_symbols=[],
                )
            except Exception:
                pass

        code_blocks: list[dict[str, str]] = []
        log_blocks: list[str] = []
        doc_blocks: list[str] = []
        detected_files: list[str] = []
        detected_symbols: list[str] = []

        # 1. Extract markdown fenced code blocks: ```lang ... ```
        fenced_pattern = re.compile(r'```([a-zA-Z0-9_-]*)\s*\n(.*?)```', re.DOTALL)
        
        for match in fenced_pattern.finditer(prompt):
            lang = (match.group(1) or "").strip().lower()
            content = match.group(2)
            
            # Check if this fenced block looks like logs
            if lang in ("log", "sh", "bash", "shell", "txt") or "Traceback" in content or "[ERROR]" in content:
                log_blocks.append(content)
            elif lang in ("json", "yaml", "yml", "toml", "md", "markdown"):
                doc_blocks.append(content)
            else:
                # Detect file name in code block header or content
                filepath_match = re.search(r'^(?://|#|/\*)\s*(?:file(?:path)?:?\s*)?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)', content, re.MULTILINE)
                filepath = filepath_match.group(1) if filepath_match else None
                if filepath:
                    detected_files.append(filepath)

                code_blocks.append({
                    "language": lang or "text",
                    "content": content,
                    "filepath": filepath,
                })

        # Remove fenced blocks from user_request text
        user_request = fenced_pattern.sub("", prompt).strip()

        # 2. Extract potential file path mentions in text (bounded to first 5,000 chars for speed)
        search_target = user_request[:5000]
        file_matches = re.findall(r'\b([a-zA-Z0-9_\-./\\]+\.(?:py|js|ts|tsx|jsx|json|go|rs|java|c|cpp|h|css|html|yaml|yml|md))\b', search_target)
        for f in file_matches:
            if f not in detected_files and not f.startswith("http"):
                detected_files.append(f)

        # 3. Extract symbol mentions (bounded to first 5,000 chars for speed)
        func_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)', search_target)
        class_matches = re.findall(r'\b([A-Z][a-zA-Z0-9]+)\b', search_target)
        for sym in func_matches + class_matches:
            if sym not in detected_symbols and len(sym) > 2 and sym not in ("The", "This", "When", "What", "How", "Why", "API", "JSON", "REST", "HTTP", "POST", "GET", "PUT", "DELETE"):
                detected_symbols.append(sym)

        # Classify the overall prompt intent
        task_category, confidence = self.classify(prompt)

        return DecomposedPrompt(
            raw_prompt=prompt,
            user_request=user_request,
            code_blocks=code_blocks,
            log_blocks=log_blocks,
            doc_blocks=doc_blocks,
            task_category=task_category,
            confidence=confidence,
            detected_files=detected_files,
            detected_symbols=detected_symbols,
        )

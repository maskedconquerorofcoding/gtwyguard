import re
import base64
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

class Severity:
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def priority(cls, level: str) -> int:
        order = {cls.CLEAN: 0, cls.LOW: 1, cls.MEDIUM: 2, cls.HIGH: 3, cls.CRITICAL: 4}
        return order.get(level, 0)

@dataclass
class Finding:
    line_number: int
    pattern_name: str
    severity: str
    matched_text: str
    line_content: str
    description: str

@dataclass
class ScanResult:
    file_path: str
    total_injections: int = 0
    highest_severity: str = Severity.CLEAN
    findings: List[Finding] = field(default_factory=list)
    has_zero_width_chars: bool = False
    scanned_lines: int = 0
    error: Optional[str] = None

# Pattern definitions for prompt injections and malicious agent execution vectors
INJECTION_RULES = [
    # 1. Direct System Prompt Overrides (CRITICAL / HIGH)
    {
        "name": "Direct System Prompt Override",
        "pattern": r"(?i)\b(ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules|prompts)|disregard\s+(all\s+)?(previous|prior)\s+instructions|system\s+override|override\s+system\s+directives|new\s+system\s+prompt)\b",
        "severity": Severity.CRITICAL,
        "description": "Attempts to overwrite or invalidate system instructions in AI models / agents."
    },
    {
        "name": "Jailbreak / Persona Hijack",
        "pattern": r"(?i)\b(you\s+are\s+now\s+in\s+developer\s+mode|dan\s+mode|jailbreak\s+mode|act\s+as\s+an\b.*?\bunrestricted\b|ignore\s+safety\s+filters|bypass\s+restrictions)\b",
        "severity": Severity.CRITICAL,
        "description": "Attempts to bypass safety restrictions or force an unrestricted persona."
    },
    
    # 2. Indirect Prompt Injection Markers (HIGH)
    {
        "name": "Chat Template Injection Marker",
        "pattern": r"(<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<\|system\|>|<\|user\|>|<\|assistant\|>)",
        "severity": Severity.HIGH,
        "description": "Uses low-level LLM chat template tokens to spoof system or assistant roles."
    },
    {
        "name": "Role-play / Fake Prompt Header Injection",
        "pattern": r"(?i)(^\s*|\n)(system\s*:|assistant\s*:|user\s*:|human\s*:)\s*(ignore|execute|run|read|override|delete)",
        "severity": Severity.HIGH,
        "description": "Embedded fake role headers designed to trick AI tools into executing instructions as system prompts."
    },

    # 3. Terminal & System Command Privileges Hijacking (CRITICAL)
    {
        "name": "Agent Terminal Command Execution Directive",
        "pattern": r"(?i)\b(run\s+(the\s+following\s+)?(terminal|bash|shell|system)\s+command|execute\s+in\s+(terminal|shell|bash)|open\s+(a\s+)?terminal\s+and\s+run|run_command\s*\(|exec_command)\b",
        "severity": Severity.CRITICAL,
        "description": "Prompt specifically instructs an automated AI agent or assistant to run terminal/shell commands."
    },
    {
        "name": "Destructive Command Payload",
        "pattern": r"(?i)(rm\s+-rf\s+[/~]|curl\s+.*?\|\s*(bash|sh)|wget\s+.*?\|\s*(bash|sh)|chmod\s+\+x|nc\s+-e|/bin/sh|/bin/bash|python\s+-c\s+['\"]import\s+socket)",
        "severity": Severity.CRITICAL,
        "description": "Contains destructive or reverse shell commands targeting local computer services."
    },
    {
        "name": "Credential Exfiltration Target",
        "pattern": r"(?i)(cat\s+~/\.(ssh|aws|config|env|gitcredentials)|read\s+~/\.(ssh|aws|env)|exfiltrate|send\s+to\s+http)",
        "severity": Severity.HIGH,
        "description": "Targeting user sensitive credential files (~/.ssh, ~/.aws, .env) for inspection or exfiltration."
    },

    # 4. Hidden & Obfuscated Injections (HIGH)
    {
        "name": "HTML Comment Hidden Prompt Injection",
        "pattern": r"(?i)<!--\s*(ignore|override|system|execute|run|secret\s+instruction).*?-->",
        "severity": Severity.HIGH,
        "description": "Prompt injection hidden inside HTML comments (invisible in rendered markdown)."
    },
    {
        "name": "Markdown Image Exfiltration Link",
        "pattern": r"!\[.*?\]\(https?://[^\s)]+?\?(data|token|stolen|exfil|key)=.*?\)",
        "severity": Severity.HIGH,
        "description": "Markdown image tag formatted to exfiltrate private data to an external server via query params."
    }
]

# Zero-width unicode characters used for steganographic prompt injection
ZERO_WIDTH_CHARS = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u200e', '\u200f']

class PromptScanner:
    """Scanner for analyzing source code, documentation, and prompt files for prompt injections."""

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = INJECTION_RULES + (custom_rules or [])

    def scan_content(self, content: str, file_path: str = "memory") -> ScanResult:
        result = ScanResult(file_path=file_path)
        lines = content.splitlines()
        result.scanned_lines = len(lines)

        # Check zero-width characters
        for zwc in ZERO_WIDTH_CHARS:
            if zwc in content:
                result.has_zero_width_chars = True
                break
        
        if result.has_zero_width_chars:
            result.findings.append(Finding(
                line_number=1,
                pattern_name="Hidden Zero-Width Unicode Characters",
                severity=Severity.HIGH,
                matched_text="Zero-width characters detected",
                line_content="[Content contains invisible zero-width Unicode characters]",
                description="Contains invisible zero-width characters commonly used to hide prompt injection payloads."
            ))

        # Check line-by-line regex rules
        for line_idx, line in enumerate(lines, 1):
            # Also check base64 decoded string snippets if present
            self._check_line(line, line_idx, result)
            self._check_base64_hidden_prompts(line, line_idx, result)

        result.total_injections = len(result.findings)

        # Update highest severity
        highest = Severity.CLEAN
        for f in result.findings:
            if Severity.priority(f.severity) > Severity.priority(highest):
                highest = f.severity
        result.highest_severity = highest

        return result

    def _check_line(self, line: str, line_num: int, result: ScanResult):
        for rule in self.rules:
            match = re.search(rule["pattern"], line)
            if match:
                matched_str = match.group(0)
                # Avoid duplicate identical findings on same line
                if not any(f.line_number == line_num and f.pattern_name == rule["name"] for f in result.findings):
                    result.findings.append(Finding(
                        line_number=line_num,
                        pattern_name=rule["name"],
                        severity=rule["severity"],
                        matched_text=matched_str,
                        line_content=line.strip(),
                        description=rule["description"]
                    ))

    def _check_base64_hidden_prompts(self, line: str, line_num: int, result: ScanResult):
        # Match potential base64 strings longer than 24 chars
        b64_matches = re.findall(r'[A-Za-z0-9+/]{24,}={0,2}', line)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                for rule in self.rules:
                    if re.search(rule["pattern"], decoded):
                        result.findings.append(Finding(
                            line_number=line_num,
                            pattern_name=f"Base64 Encoded {rule['name']}",
                            severity=Severity.CRITICAL,
                            matched_text=b64_str[:30] + "...",
                            line_content=line.strip(),
                            description=f"Base64 string decodes to prompt injection: {rule['description']}"
                        ))
            except Exception:
                continue

    def scan_file(self, file_path: str) -> ScanResult:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.scan_content(content, file_path=file_path)
        except Exception as e:
            return ScanResult(file_path=file_path, error=str(e))

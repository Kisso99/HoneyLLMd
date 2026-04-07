# -*- coding: utf-8 -*-
import requests
import json
import os
import re
import codecs

API_KEY = "sk-467e4bcd5b324763a3360d0b8cb26fa7"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
LLM_PROMPT = "You are a shell with system information Linux can201-VirtualBox 5.15.0-139-generic #149~20.04.1-Ubuntu with distribution Debian GNU/Linux 8.11 (jessie). Simulate a bash shell faithfully. Output only what a real shell would print; do not include extra explanations"

def _normalize_command(s):
    return " ".join((s or "").strip().split())

_INVALID_PATTERNS = [
    r"\bbash:\s*.*command not found\b",
    r"\bcommand not found\b",
    r"\bno such file or directory\b",
    r"\bunknown command\b",
    r"\binvalid command\b",
]
_INVALID_RE = re.compile("|".join(_INVALID_PATTERNS), re.IGNORECASE)

def _looks_like_invalid(output):
    if not output:
        return True
    return bool(_INVALID_RE.search(output))

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
VALID_COMMANDS = set()
valid_file = os.path.join(BASE_PATH, "valid_commands.txt")

if os.path.exists(valid_file):
    try:
        with codecs.open(valid_file, "r", "utf-8") as f:
            for line in f:
                cmd = line.strip()
                if cmd:
                    VALID_COMMANDS.add(cmd)
    except:
        pass

def _sanitize_output(output):
    if not output:
        return ""
    output = re.sub(r"^(```+|'''+)", "", output.strip())
    output = re.sub(r"(```+|'''+)$", "", output.strip())
    output = re.sub(r"^bash:\s*", "", output)
    output = re.sub(r"^plaintext:\s*", "", output)
    return output.strip()

class LLMContextManager(object):
    def __init__(self):
        self.model = MODEL
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.max_history = 20
        self.history = [{"role": "system", "content": LLM_PROMPT}]

        self.cache_file = os.path.join(BASE_PATH, "llm_response_cache.json")
        self.cmd_cache = {}

        if os.path.exists(self.cache_file):
            try:
                with codecs.open(self.cache_file, "r", "utf-8") as f:
                    self.cmd_cache = json.load(f)
            except:
                self.cmd_cache = {}

    def ask(self, command):
        norm_cmd = _normalize_command(command)
        if not norm_cmd:
            return ""

        if norm_cmd in self.cmd_cache:
            return self.cmd_cache[norm_cmd]

        return self._call_llm(norm_cmd)

    def _call_llm(self, cmd_line):
        url = self.base_url + "/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key
        }
        data = {
            "model": self.model,
            "messages": self.history + [{"role": "user", "content": cmd_line}]
        }

        try:
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code == 200:
                output = resp.json()["choices"][0]["message"]["content"].strip()
                output = _sanitize_output(output)

                self.history.append({"role": "user", "content": cmd_line})
                self.history.append({"role": "assistant", "content": output})
                self.cmd_cache[cmd_line] = output
                self._save_cache()
                return output
        except Exception as e:
            print("LLM error:", e)

        return "command not found"

    def _save_cache(self):
        try:
            with codecs.open(self.cache_file, "w", "utf-8") as f:
                json.dump(self.cmd_cache, f, ensure_ascii=False, indent=2)
        except:
            pass

# 全局单例 → 主程序直接调用
llm = LLMContextManager()

"""Check that a token-limited career reply is completed before display."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'utils/gemini_api.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
FUNCTIONS = [node for node in TREE.body if isinstance(node, ast.FunctionDef)
             and node.name in {'chat_with_career_guidance', '_response_text'}]


class FakeChat:
    def __init__(self):
        self.prompts = []

    def send_message(self, prompt):
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return SimpleNamespace(text='Bạn có thể', candidates=[SimpleNamespace(finish_reason='MAX_TOKENS')])
        return SimpleNamespace(text=' bắt đầu từ sở thích của mình.',
                               candidates=[SimpleNamespace(finish_reason='STOP')])


class CareerChatCompletionTests(unittest.TestCase):
    def test_continues_token_limited_reply(self):
        chat = FakeChat()
        model = SimpleNamespace(start_chat=lambda history: chat)
        scope = {
            'genai': SimpleNamespace(GenerativeModel=lambda *args, **kwargs: model),
            'MODEL_NAME': 'test', 'CAREER_GUIDANCE_PROMPT': 'test',
            'CHAT_MAX_OUTPUT_TOKENS': 1800,
            '_run_with_gemini_key': lambda callback: callback(),
        }
        exec(compile(ast.Module(body=FUNCTIONS, type_ignores=[]), str(SOURCE), 'exec'), scope)
        answer = scope['chat_with_career_guidance']('Em thích nghề gì?')
        self.assertEqual(answer, 'Bạn có thể bắt đầu từ sở thích của mình.')
        self.assertEqual(len(chat.prompts), 2)


if __name__ == '__main__':
    unittest.main()

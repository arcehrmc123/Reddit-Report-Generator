import json
import logging
import tiktoken
from typing import Callable, Dict, List
from openai import BadRequestError, Client
from openai.types.chat import ChatCompletionMessage
from RedditReportGenerator.common.utils import convert_tool, get_logger


class QuestionSolverAnalyst:
    """
    QuestionSolverAnalyst is responsible for collecting as much information as possible about the Reddit user/community
    from a specific perspective to satisfy analysis requests.
    """

    def __init__(
        self,
        model: str,
        client: Client,
        user_or_community_id: str,
        known_facts: str,
        main_perspective: str,
        tools: List[Callable],
    ):
        self.name = "QuestionSolver"
        self.model = model
        self.client = client
        self.main_perspective = main_perspective
        self.tools = tools
        self.facts = known_facts
        self.user_or_community_id = user_or_community_id

        self.system_prompt = """
ROLE: You are a professional Reddit user/community analyst on the {perspective} domain, good at solving questions. Below I will present you a request. Keep in mind that you are Ken Jennings-level with trivia, and Mensa-level with puzzles, so there should be a deep well to draw from.
ACTION: Collect as much information as possible about the Reddit user/community from the {perspective} perspective for the main analyst, until the request is fully satisfied. Provide complete information and conclusions in your analysis. DO NOT ask questions or request further instructions - simply provide your best complete analysis based on available information. NEVER use any placeholder when requesting. When you have fully addressed the request, please say END.
""".format(
            perspective=main_perspective
        ).strip()

        self.log = get_logger(
            f"{self.main_perspective}-QuestionSolver", user_or_community_id
        )

        self.tool_map = {tool.__name__: tool for tool in tools}

        converted_tools = []
        for tool in self.tools:
            try:
                converted_tool = convert_tool(tool)
                converted_tools.append(converted_tool)
            except ValueError as e:
                self.log.error(f"Failed to convert tool {tool.__name__}: {str(e)}")

        self.converted_tools = converted_tools

        self.model_info = client.models.retrieve(self.model)
        self.log.info(f"Model info: {self.model_info}")
        self.token_limit = self.model_info.to_dict().get("token_limit", 130000)
        self.log.warning(f"Token limit: {self.token_limit}")

    def _truncate_tool_result(self, result, max_chars: int = 2000) -> str:
        """Truncate tool result to fit within reasonable token limits"""
        result_str = json.dumps(result)

        # If result is too large, truncate it intelligently
        if len(result_str) > max_chars:
            self.log.warning(f"Tool result too large ({len(result_str)} chars), truncating to {max_chars}")

            if isinstance(result, list):
                # For lists lists, keep only first few items
                result_str = json.dumps(result[:3]) + "... (truncated)"
            elif isinstance(result, dict):
                # For dicts, keep only summary keys
                summary = {}
                for key, value in list(result.items())[:5]:
                    if isinstance(value, (list, dict)):
                        summary[key] = f"<{type(value).__name__} with {len(value)} items>" if isinstance(value, list) else f"<complex {type(value).__name__}>"
                    else:
                        summary[key] = value
                result_str = json.dumps(summary) + "... (truncated)"
            else:
                result_str = result_str[:max_chars] + "... (truncated)"

        return result_str

    def call_tools(self, question: str, response: ChatCompletionMessage) -> list:
        """Call tools based on the model's response"""
        tool_messages = [response.to_dict()]

        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to parse tool arguments for {tool_name}: {e}")
                self.log.error(f"Raw arguments: {tool_call.function.arguments}")
                continue

            self.log.warning(
                f"For {question} call Tool: {tool_name} with args {tool_args}"
            )

            tool = self.tool_map.get(tool_name)
            if tool:
                try:
                    result = tool(**tool_args)
                    truncated_result = self._truncate_tool_result(result)
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": truncated_result,
                        }
                    )
                except Exception as e:
                    error_message = (
                        f"Error in tool {tool_name} with args {tool_args}: {str(e)}"
                    )
                    self.log.error(error_message)
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_message,
                        }
                    )
            else:
                raise ValueError(f"Tool {tool_name} not found in tool map")

        return tool_messages

    def cut_history(self, previous_chat_history: list) -> list:
        """Cuts the chat history to fit within token limit"""
        if not previous_chat_history:
            return []

        encoding = tiktoken.get_encoding("o200k_base")

        def count_tokens(message):
            role_tokens = len(encoding.encode(message["role"]))
            content_tokens = len(encoding.encode(message.get("content", "")))
            return role_tokens + content_tokens + 4

        total_tokens = 0
        accumulated_messages = []

        for message in reversed(previous_chat_history):
            tokens = count_tokens(message)
            if total_tokens + tokens > self.token_limit:
                break
            accumulated_messages.append(message)
            total_tokens += tokens

        if not accumulated_messages:
            return []

        accumulated_messages.reverse()

        for idx, message in enumerate(accumulated_messages):
            if message["role"] == "user":
                return accumulated_messages[idx:]

        self.log.warning("No user message found in pruned chat history")
        return accumulated_messages

    def rollback_history(self, previous_chat_history: list, e: Exception) -> list:
        """Rollback chat history to last tool use"""
        original_length = len(previous_chat_history)
        processed = 0

        while previous_chat_history and processed < original_length:
            processed += 1
            last_message = previous_chat_history.pop()
            if (
                last_message["role"] == "assistant"
                and "tool_calls" in last_message
                and last_message["tool_calls"]
            ):
                previous_chat_history.append(last_message)
                previous_chat_history.extend(
                    [
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(e),
                        }
                        for tool_call in last_message["tool_calls"]
                    ]
                )
                break

        if processed >= original_length and not previous_chat_history:
            self.log.warning("No tool calls found in history")
            return previous_chat_history

        return previous_chat_history

    def analyze(self, previous_chat_history: list, question: str, prompt: str) -> str:
        """Analyze a specific sub-question using tools and LLM capabilities"""
        chat_history = [
            *previous_chat_history,
            {
                "role": "user",
                "content": f"Known Facts: {json.dumps(self.facts)}\n\nQuestion to analyze: {question}\n\n{prompt}",
            },
        ]

        max_iterations = 10
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            self.log.info(
                f"Iteration {iterations} for question: {question} ({self.main_perspective})"
            )

            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.cut_history(chat_history),
            ]

            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.converted_tools,
                    tool_choice="auto",
                    temperature=0,
                )
            except BadRequestError as e:
                if "maximum" in str(e).lower():
                    self.log.warning(
                        f"Max context length exceeded for question: {question} ({e}), rolling back history"
                    )
                    chat_history = self.rollback_history(chat_history, e)
                    continue
                else:
                    raise e
            except Exception as e:
                if (
                    "rate" in str(e).lower()
                    or "quota" in str(e).lower()
                    or "resource" in str(e).lower()
                    or "maximum" in str(e).lower()
                ):
                    self.log.warning(
                        f"Rate limit exceeded for question: {question}, rolling back history"
                    )
                    chat_history = self.rollback_history(chat_history, e)
                    continue
                else:
                    raise e

            response = completion.choices[0].message

            if response.tool_calls:
                tool_messages = self.call_tools(question, response)
                chat_history.extend(tool_messages)
            else:
                if "END" in response.content:
                    final_response = response.content.replace("END", "").strip()
                    self.log.info(f"Analysis complete after {iterations} iterations")
                    chat_history.append(
                        {
                            "role": "assistant",
                            "content": final_response,
                        }
                    )

                    self.log.info(f"Final response: {final_response}")

                    return [
                        {
                            "role": "user",
                            "content": question,
                        },
                        {
                            "role": "assistant",
                            "content": final_response,
                        },
                    ]

                chat_history.append({"role": "assistant", "content": response.content})

                self.log.info(f"Response: {response.content}")

                chat_history.append(
                    {
                        "role": "user",
                        "content": "Continue analyzing this question. When you have completed the analysis, include 'END' at the end of your response.",
                    }
                )

        self.log.warning("Reached maximum iterations without completing analysis")
        self.log.warning(f"Final chat history: {chat_history}")

        return [
            {
                "role": "user",
                "content": question,
            },
            {
                "role": "assistant",
                "content": chat_history[-1]["content"],
            },
        ]

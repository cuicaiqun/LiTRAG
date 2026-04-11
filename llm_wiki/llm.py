from __future__ import annotations

import base64
import mimetypes
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str = "") -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")
        self.client = OpenAI(api_key=api_key, base_url=base_url or None)

    @staticmethod
    def _extract_text_from_response_payload(payload: dict[str, Any]) -> str:
        output = payload.get("output") or []
        chunks: list[str] = []
        for item in output:
            if item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        return "\n".join(chunks).strip()

    @staticmethod
    def _extract_text_from_chat_message(message: Any) -> str:
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            return "\n".join(parts).strip()
        return ""

    @staticmethod
    def _extract_text_from_delta(delta: Any) -> str:
        content = getattr(delta, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return ""

    def describe_image(
        self,
        *,
        model: str,
        image_path: Path,
        prompt: str,
        max_tokens: int = 1200,
    ) -> str:
        errors: list[str] = []
        prepared_path = image_path
        tmp_path: Path | None = None

        try:
            try:
                from PIL import Image

                with Image.open(image_path) as img:
                    img = img.convert("RGB")
                    max_side = 1600
                    if max(img.width, img.height) > max_side:
                        ratio = max_side / max(img.width, img.height)
                        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
                        img = img.resize(new_size)
                    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    tmp_path = Path(tmp.name)
                    tmp.close()
                    img.save(tmp_path, format="JPEG", quality=88)
                    prepared_path = tmp_path
            except Exception as exc:
                errors.append(f"image_preprocess_error={exc}")

            mime = mimetypes.guess_type(prepared_path.name)[0] or "image/jpeg"
            encoded = base64.b64encode(prepared_path.read_bytes()).decode("ascii")
            data_url = f"data:{mime};base64,{encoded}"

            # 1) Preferred: streaming chat vision.
            try:
                stream = self.client.chat.completions.create(
                    model=model,
                    stream=True,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": "You are a precise vision extraction assistant."},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        },
                    ],
                )

                parts: list[str] = []
                for chunk in stream:
                    for choice in chunk.choices:
                        text = self._extract_text_from_delta(choice.delta)
                        if text:
                            parts.append(text)
                output = "".join(parts).strip()
                if output:
                    return output
                errors.append("vision_stream_chat_empty")
            except Exception as exc:
                errors.append(f"vision_stream_chat_error={exc}")

            # 2) Fallback: responses API with image input.
            try:
                response = self.client.responses.create(
                    model=model,
                    instructions="You are a precise vision extraction assistant.",
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": prompt},
                                {"type": "input_image", "image_url": data_url},
                            ],
                        }
                    ],
                    max_output_tokens=max_tokens,
                )
                output_text = getattr(response, "output_text", "") or ""
                if output_text.strip():
                    return output_text.strip()
                payload_text = self._extract_text_from_response_payload(response.model_dump())
                if payload_text:
                    return payload_text
                errors.append("vision_responses_empty")
            except Exception as exc:
                errors.append(f"vision_responses_error={exc}")

            joined = "; ".join(errors) if errors else "unknown_error"
            raise RuntimeError(f"Vision model returned empty output for image: {image_path}. Details: {joined}")
        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def transcribe_audio(
        self,
        *,
        model: str,
        audio_path: Path,
    ) -> str:
        with audio_path.open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=model,
                file=audio_file,
            )
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        if isinstance(response, dict):
            value = response.get("text", "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise RuntimeError(f"ASR model returned empty output for audio: {audio_path}")

    def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int = 1800,
    ) -> str:
        errors: list[str] = []

        # 1) Prefer streaming Chat Completions because some gateways omit
        # final `message.content` in non-stream mode.
        try:
            stream = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            parts: list[str] = []
            for chunk in stream:
                for choice in chunk.choices:
                    text = self._extract_text_from_delta(choice.delta)
                    if text:
                        parts.append(text)
            joined = "".join(parts).strip()
            if joined:
                return joined
            errors.append("stream_chat_empty")
        except Exception as exc:
            errors.append(f"stream_chat_error={exc}")

        # 2) Fallback to Responses API.
        try:
            response = self.client.responses.create(
                model=model,
                instructions=system_prompt,
                input=user_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            output_text = getattr(response, "output_text", "") or ""
            if output_text.strip():
                return output_text.strip()
            payload_text = self._extract_text_from_response_payload(response.model_dump())
            if payload_text:
                return payload_text
            errors.append("responses_empty")
        except Exception as exc:
            errors.append(f"responses_error={exc}")

        # 3) Last fallback: non-stream Chat Completions.
        try:
            chat = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = self._extract_text_from_chat_message(chat.choices[0].message).strip()
            if text:
                return text
            errors.append("chat_empty")
        except Exception as exc:
            errors.append(f"chat_error={exc}")

        joined_errors = "; ".join(errors) if errors else "unknown_error"
        raise RuntimeError(f"LLM returned empty output. Details: {joined_errors}")

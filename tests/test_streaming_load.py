"""
Load/stress test scaffolding for streaming endpoints.
Tests concurrent NDJSON stream handling under load.

Run with: RUN_LOAD=true pytest tests/test_streaming_load.py -v
"""

import asyncio
import json
import os
import time

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LOAD"), reason="Set RUN_LOAD=true to run"
)


def generate_ndjson_lines(count: int) -> list[bytes]:
    """Generate NDJSON event lines."""
    lines = []
    for i in range(count):
        event = {
            "type": "server.message",
            "sequence": i,
            "timestamp": "2026-01-01T00:00:00Z",
            "data": {"content": f"Event {i}"},
        }
        lines.append(json.dumps(event).encode() + b"\n")
    return lines


def parse_ndjson_lines(data: bytes) -> int:
    """Parse NDJSON data and return event count."""
    count = 0
    for line in data.split(b"\n"):
        line = line.strip()
        if line:
            json.loads(line)
            count += 1
    return count


class TestStreamingLoad:
    def test_parse_1000_events(self):
        """Parse 1000 NDJSON events sequentially."""
        lines = generate_ndjson_lines(1000)
        data = b"".join(lines)

        start = time.monotonic()
        count = parse_ndjson_lines(data)
        elapsed = time.monotonic() - start

        assert count == 1000
        print(f"\n1000 events parsed in {elapsed:.3f}s")

    def test_parse_large_events(self):
        """Parse events with large payloads (10KB each)."""
        large_payload = "x" * 10000
        lines = []
        for i in range(100):
            event = {
                "type": "server.message",
                "sequence": i,
                "data": {"content": large_payload},
            }
            lines.append(json.dumps(event).encode() + b"\n")

        data = b"".join(lines)
        count = parse_ndjson_lines(data)
        assert count == 100

    @pytest.mark.asyncio
    async def test_concurrent_stream_parsing(self):
        """Parse 10 concurrent streams of 100 events each."""

        async def parse_stream(event_count: int) -> int:
            lines = generate_ndjson_lines(event_count)
            data = b"".join(lines)
            # Simulate async processing with small yield
            await asyncio.sleep(0)
            return parse_ndjson_lines(data)

        tasks = [parse_stream(100) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        assert results == [100] * 10

    def test_incremental_line_parsing(self):
        """Simulate incremental NDJSON parsing (chunked delivery)."""
        lines = generate_ndjson_lines(500)
        full_data = b"".join(lines)

        # Simulate chunks of varying sizes
        chunk_sizes = [64, 128, 256, 512, 1024]
        chunks = []
        offset = 0
        chunk_idx = 0
        while offset < len(full_data):
            size = chunk_sizes[chunk_idx % len(chunk_sizes)]
            chunks.append(full_data[offset : offset + size])
            offset += size
            chunk_idx += 1

        # Parse incrementally
        buffer = b""
        count = 0
        for chunk in chunks:
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if line:
                    json.loads(line)
                    count += 1

        assert count == 500

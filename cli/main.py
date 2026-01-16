"""
Sentinel CLI - Command Line Interface

Commands:
- init: Initialize Sentinel configuration
- server: Start the trace server
- list: List traces
- show: Show a specific trace
- replay: Replay a trace
"""

import argparse
import sys
import os


def cmd_init(args):
    """Initialize Sentinel configuration."""
    import yaml
    from pathlib import Path
    
    config_dir = Path(os.path.expanduser("~/.sentinel"))
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / "config.yaml"
    
    if config_file.exists() and not args.force:
        print(f"Config already exists at {config_file}")
        print("Use --force to overwrite")
        return 1
    
    default_config = {
        "storage": {
            "base_dir": str(config_dir),
            "format": "json",
            "sqlite_index": True,
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8000,
        },
        "tracing": {
            "auto_capture": True,
        },
    }
    
    with open(config_file, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    print(f"Initialized Sentinel at {config_dir}")
    print(f"Config: {config_file}")
    print(f"Traces: {config_dir / 'traces'}")
    return 0


def cmd_server(args):
    """Start the trace server."""
    import uvicorn
    
    print(f"Starting Sentinel server on {args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"UI: http://{args.host}:{args.port}/ui")
    
    uvicorn.run(
        "server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_list(args):
    """List traces."""
    from server.storage.files import FileStorage
    
    storage = FileStorage()
    traces = storage.list_traces(
        limit=args.limit,
        model=args.model,
        provider=args.provider,
    )
    
    if not traces:
        print("No traces found.")
        return 0
    
    print(f"{'ID':<40} {'Model':<20} {'Provider':<10} {'Latency':<10}")
    print("-" * 80)
    
    for trace in traces:
        print(
            f"{trace.trace_id:<40} "
            f"{trace.request.model:<20} "
            f"{trace.request.provider:<10} "
            f"{trace.response.latency_ms}ms"
        )
    
    return 0


def cmd_show(args):
    """Show a specific trace."""
    import json
    from server.storage.files import FileStorage
    
    storage = FileStorage()
    trace = storage.get_trace(args.trace_id)
    
    if trace is None:
        print(f"Trace {args.trace_id} not found")
        return 1
    
    if args.json:
        print(json.dumps(trace.model_dump(), indent=2))
    else:
        print(f"Trace ID: {trace.trace_id}")
        print(f"Timestamp: {trace.timestamp}")
        print(f"Model: {trace.request.model}")
        print(f"Provider: {trace.request.provider}")
        print(f"Latency: {trace.response.latency_ms}ms")
        print()
        print("Messages:")
        for msg in trace.request.messages:
            print(f"  [{msg.role}]: {msg.content[:100]}...")
        print()
        print("Response:")
        print(f"  {trace.response.text[:500]}...")
    
    return 0


def cmd_replay(args):
    """Replay a trace."""
    import json
    from server.storage.files import FileStorage
    from sdk.adapters.openai import OpenAIAdapter
    
    storage = FileStorage()
    original = storage.get_trace(args.trace_id)
    
    if original is None:
        print(f"Trace {args.trace_id} not found")
        return 1
    
    print(f"Replaying trace {args.trace_id}")
    print(f"Model: {args.model or original.request.model}")
    
    if args.dry_run:
        print("DRY RUN - no actual call will be made")
        return 0
    
    adapter = OpenAIAdapter()
    messages = [msg.model_dump() for msg in original.request.messages]
    params = original.request.parameters.model_dump(exclude_none=True)
    
    if args.model:
        model = args.model
    else:
        model = original.request.model
    
    response, new_trace = adapter.chat_completion(
        model=model,
        messages=messages,
        **params,
    )
    
    new_trace.replay_of = args.trace_id
    storage.save_trace(new_trace)
    
    print(f"New trace ID: {new_trace.trace_id}")
    print(f"Response: {new_trace.response.text[:200]}...")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Developer-first local LLM tracing, replay & debugging system",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize Sentinel")
    init_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing config")
    
    # server command
    server_parser = subparsers.add_parser("server", help="Start the trace server")
    server_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    server_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List traces")
    list_parser.add_argument("--limit", "-n", type=int, default=20, help="Max traces to show")
    list_parser.add_argument("--model", "-m", help="Filter by model")
    list_parser.add_argument("--provider", "-p", help="Filter by provider")
    
    # show command
    show_parser = subparsers.add_parser("show", help="Show a trace")
    show_parser.add_argument("trace_id", help="Trace ID to show")
    show_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a trace")
    replay_parser.add_argument("trace_id", help="Trace ID to replay")
    replay_parser.add_argument("--model", "-m", help="Override model")
    replay_parser.add_argument("--dry-run", "-d", action="store_true", help="Don't execute")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    commands = {
        "init": cmd_init,
        "server": cmd_server,
        "list": cmd_list,
        "show": cmd_show,
        "replay": cmd_replay,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

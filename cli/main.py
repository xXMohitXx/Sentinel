"""
Phylax CLI - Command Line Interface

Commands:
- init: Initialize Phylax configuration
- server: Start the trace server
- list: List traces
- show: Show a specific trace
- replay: Replay a trace
"""

import argparse
import sys
import os


def cmd_init(args):
    """Initialize Phylax configuration."""
    import yaml
    from pathlib import Path
    
    config_dir = Path(os.path.expanduser("~/.phylax"))
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
    
    print(f"Initialized Phylax at {config_dir}")
    print(f"Config: {config_file}")
    print(f"Traces: {config_dir / 'traces'}")
    return 0


def cmd_server(args):
    """Start the trace server."""
    import uvicorn
    
    print(f"Starting Phylax server on {args.host}:{args.port}")
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
    
    # Filter by verdict if requested
    if args.failed:
        traces = [t for t in traces if t.verdict and t.verdict.status == "fail"]
    
    if not traces:
        if args.failed:
            print("No failed traces found. ✅")
        else:
            print("No traces found.")
        return 0
    
    print(f"{'STATUS':<8} {'ID':<36} {'Model':<16} {'Latency':<10}")
    print("-" * 75)
    
    for trace in traces:
        # Format verdict status
        if trace.verdict is None:
            status = "⏳"
        elif trace.verdict.status == "pass":
            status = "✅"
        else:
            status = "❌"
        
        print(
            f"{status:<8} "
            f"{trace.trace_id[:35]:<36} "
            f"{trace.request.model[:15]:<16} "
            f"{trace.response.latency_ms}ms"
        )
        
        # Show violations prominently for failed traces
        if trace.verdict and trace.verdict.status == "fail":
            for v in trace.verdict.violations:
                print(f"         └─ {v}")
    
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
        # Show verdict status prominently at the top
        if trace.verdict:
            if trace.verdict.status == "pass":
                print("═" * 60)
                print("✅ VERDICT: PASS")
                print("═" * 60)
            else:
                print("═" * 60)
                print(f"❌ VERDICT: FAIL (Severity: {trace.verdict.severity})")
                print("═" * 60)
                print()
                print("VIOLATIONS:")
                for v in trace.verdict.violations:
                    print(f"  • {v}")
                print()
        
        print(f"Trace ID: {trace.trace_id}")
        print(f"Timestamp: {trace.timestamp}")
        print(f"Model: {trace.request.model}")
        print(f"Provider: {trace.request.provider}")
        print(f"Latency: {trace.response.latency_ms}ms")
        print(f"Blessed: {'Yes' if trace.blessed else 'No'}")
        print()
        print("Messages:")
        for msg in trace.request.messages:
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"  [{msg.role}]: {content}")
        print()
        print("Response:")
        response_text = trace.response.text[:500] + "..." if len(trace.response.text) > 500 else trace.response.text
        print(f"  {response_text}")
    
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


def cmd_bless(args):
    """Bless a trace as a golden reference."""
    from server.storage.files import FileStorage
    
    storage = FileStorage()
    trace = storage.get_trace(args.trace_id)
    
    if trace is None:
        print(f"❌ Trace {args.trace_id} not found")
        return 1
    
    # Check if there's already a golden trace for this model/provider
    if not args.force:
        existing = storage.get_golden_for_model(
            trace.request.model,
            trace.request.provider,
        )
        if existing and existing.trace_id != args.trace_id:
            print(f"⚠️  A golden trace already exists for {trace.request.model}/{trace.request.provider}")
            print(f"   Existing: {existing.trace_id}")
            print()
            print("Use --force to override")
            return 1
    
    # Confirm with user
    if not args.yes:
        print("═" * 50)
        print("⭐ BLESSING TRACE AS GOLDEN REFERENCE")
        print("═" * 50)
        print()
        print(f"Trace ID: {trace.trace_id}")
        print(f"Model: {trace.request.model}")
        print(f"Provider: {trace.request.provider}")
        print()
        print("Input:")
        for msg in trace.request.messages[:2]:
            print(f"  [{msg.role}]: {msg.content[:80]}...")
        print()
        print("Output:")
        print(f"  {trace.response.text[:100]}...")
        print()
        response = input("Bless this trace? (yes/no): ")
        if response.lower() not in ("yes", "y"):
            print("Cancelled.")
            return 0
    
    # Bless the trace
    blessed = storage.bless_trace(args.trace_id)
    if blessed:
        print()
        print("✅ Trace blessed as golden reference!")
        print(f"   Output hash: {blessed.metadata.get('output_hash', 'N/A')}")
    else:
        print("❌ Failed to bless trace")
        return 1
    
    return 0


def cmd_check(args):
    """
    Check all blessed traces for regressions.
    
    Replays all golden traces and exits with:
    - 0: All pass
    - 1: Any failure
    
    This is the CI-safe command.
    """
    import json as json_module
    from server.storage.files import FileStorage
    from sdk.adapters.openai import OpenAIAdapter
    from sdk.adapters.gemini import GeminiAdapter
    from sdk.expectations import evaluate
    
    storage = FileStorage()
    blessed_traces = storage.list_blessed_traces()
    
    if not blessed_traces:
        print("⚠️  No blessed traces found.")
        print("   Use 'phylax bless <trace_id>' to mark a trace as golden.")
        return 0
    
    print("═" * 60)
    print("🔍 PHYLAX CHECK - Replaying Golden Traces")
    print("═" * 60)
    print(f"Found {len(blessed_traces)} blessed trace(s)")
    print()
    
    results = []
    failures = 0
    
    for trace in blessed_traces:
        print(f"Checking: {trace.trace_id[:20]}... ({trace.request.model})")
        
        try:
            # Get the adapter
            provider = trace.request.provider.lower()
            messages = [msg.model_dump() for msg in trace.request.messages]
            
            if provider == "openai":
                adapter = OpenAIAdapter()
                params = trace.request.parameters.model_dump(exclude_none=True)
                response, new_trace = adapter.chat_completion(
                    model=trace.request.model,
                    messages=messages,
                    **params,
                )
            elif provider == "gemini":
                adapter = GeminiAdapter()
                response, new_trace = adapter.chat_completion(
                    model=trace.request.model,
                    messages=messages,
                )
            else:
                print(f"  ⚠️  Unsupported provider: {provider}")
                continue
            
            # Compare outputs
            import hashlib
            new_hash = hashlib.sha256(new_trace.response.text.encode()).hexdigest()[:16]
            original_hash = trace.metadata.get("output_hash", "") if trace.metadata else ""
            
            # Check if output matches
            is_match = new_hash == original_hash
            
            result = {
                "trace_id": trace.trace_id,
                "model": trace.request.model,
                "provider": trace.request.provider,
                "original_hash": original_hash,
                "new_hash": new_hash,
                "match": is_match,
                "new_trace_id": new_trace.trace_id,
            }
            results.append(result)
            
            new_trace.replay_of = trace.trace_id
            storage.save_trace(new_trace)
            
            if is_match:
                print(f"  ✅ PASS (output matches golden)")
            else:
                print(f"  ❌ FAIL (output differs from golden)")
                print(f"     Original: {trace.response.text[:50]}...")
                print(f"     New:      {new_trace.response.text[:50]}...")
                failures += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append({
                "trace_id": trace.trace_id,
                "model": trace.request.model,
                "error": str(e),
            })
            failures += 1
    
    print()
    print("═" * 60)
    
    if failures == 0:
        print(f"✅ ALL CHECKS PASSED ({len(blessed_traces)} traces)")
        print("═" * 60)
    else:
        print(f"❌ {failures} CHECK(S) FAILED")
        print("═" * 60)
    
    # Output JSON if requested
    if args.json:
        print()
        print("JSON Report:")
        print(json_module.dumps(results, indent=2))
    
    return 1 if failures > 0 else 0


def cmd_graph_check(args):
    """
    Phase 16: Check graph-level verdicts.
    
    Evaluates execution graphs and fails CI if any graph fails.
    Provides root cause analysis.
    """
    from server.storage.files import FileStorage
    
    storage = FileStorage()
    
    print("\n" + "═" * 60)
    print("🔍 PHYLAX GRAPH CHECK")
    print("═" * 60 + "\n")
    
    # Get all executions
    executions = storage.list_executions()
    
    if not executions:
        print("No executions found.")
        return 0
    
    failures = 0
    passed = 0
    
    for exec_id in executions:
        graph = storage.get_execution_graph(exec_id)
        if not graph:
            continue
        
        verdict = graph.compute_verdict()
        
        if verdict.status == "pass":
            passed += 1
            print(f"✅ {exec_id[:20]}... ({graph.node_count} nodes)")
        else:
            failures += 1
            print(f"\n❌ FAILED: {exec_id[:20]}...")
            print(f"   Root cause: {verdict.root_cause_node[:20] if verdict.root_cause_node else 'unknown'}...")
            print(f"   Failed nodes: {verdict.failed_count}")
            print(f"   Tainted nodes: {verdict.tainted_count}")
            print(f"   Message: {verdict.message}")
    
    print("\n" + "═" * 60)
    if failures == 0:
        print(f"✅ ALL {passed} EXECUTION(S) PASSED")
    else:
        print(f"❌ {failures} EXECUTION(S) FAILED")
    print("═" * 60)
    
    return 1 if failures > 0 else 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="phylax",
        description="Developer-first local LLM tracing, replay & debugging system",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize Phylax")
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
    list_parser.add_argument("--provider", help="Filter by provider")
    list_parser.add_argument("--failed", "-f", action="store_true", help="Show only failed traces")
    
    # show command
    show_parser = subparsers.add_parser("show", help="Show a trace")
    show_parser.add_argument("trace_id", help="Trace ID to show")
    show_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a trace")
    replay_parser.add_argument("trace_id", help="Trace ID to replay")
    replay_parser.add_argument("--model", "-m", help="Override model")
    replay_parser.add_argument("--dry-run", "-d", action="store_true", help="Don't execute")
    
    # bless command - Phase 9
    bless_parser = subparsers.add_parser("bless", help="Mark a trace as golden reference")
    bless_parser.add_argument("trace_id", help="Trace ID to bless")
    bless_parser.add_argument("--force", action="store_true", help="Override existing golden for this model")
    bless_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # check command - Phase 10 (CI-safe)
    check_parser = subparsers.add_parser("check", help="Replay all golden traces (CI-safe)")
    check_parser.add_argument("--json", "-j", action="store_true", help="Output JSON report")
    
    # graph-check command - Phase 16 (graph-level CI)
    graph_check_parser = subparsers.add_parser("graph-check", help="Check execution graphs (CI-safe)")
    
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
        "bless": cmd_bless,
        "check": cmd_check,
        "graph-check": cmd_graph_check,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

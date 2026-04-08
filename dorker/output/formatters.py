"""Output formatting utilities."""

import json
import csv
from io import StringIO
from typing import List, Dict
from dataclasses import asdict
from datetime import datetime
from html import escape

from ..models import SearchResult

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class OutputFormatter:
    """Handles formatting and output of search results."""
    
    @staticmethod
    def to_json(results: List[SearchResult], pretty: bool = True) -> str:
        """Format results as JSON.
        
        Args:
            results: List of search results
            pretty: Whether to pretty-print JSON
            
        Returns:
            JSON string
        """
        data = [asdict(r) for r in results]
        return json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)
    
    @staticmethod
    def to_csv(results: List[SearchResult]) -> str:
        """Format results as CSV.
        
        Args:
            results: List of search results
            
        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.DictWriter(
            output, 
            fieldnames=["title", "url", "description", "engine", "rank", "timestamp"]
        )
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
        return output.getvalue()
    
    @staticmethod
    def to_html(results: List[SearchResult], query: str) -> str:
        """Format results as HTML with styling.
        
        Args:
            results: List of search results
            query: Original search query
            
        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dork Results: {escape(query)}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #22c55e;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .query {{ 
            background: rgba(255,255,255,0.1); 
            padding: 0.5rem 1rem; 
            border-radius: 0.5rem;
            display: inline-block;
            font-family: monospace;
            font-size: 1.1rem;
        }}
        .stats {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        .stat {{
            background: rgba(255,255,255,0.1);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
        }}
        .results {{ display: grid; gap: 1rem; }}
        .result {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .result:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.2);
        }}
        .result-header {{ display: flex; justify-content: space-between; align-items: start; gap: 1rem; }}
        .result-title {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .result-title:hover {{ text-decoration: underline; }}
        .result-engine {{
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .result-url {{
            color: var(--success);
            font-size: 0.875rem;
            margin: 0.5rem 0;
            word-break: break-all;
        }}
        .result-desc {{ color: var(--text-muted); font-size: 0.9rem; }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Dork Results</h1>
            <div class="query">{escape(query)}</div>
            <div class="stats">
                <div class="stat">📊 {len(results)} results</div>
                <div class="stat">🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
        </header>
        <div class="results">
"""
        
        for result in results:
            html += f"""
            <div class="result">
                <div class="result-header">
                    <a href="{escape(result.url)}" class="result-title" target="_blank">{escape(result.title)}</a>
                    <span class="result-engine">{escape(result.engine)}</span>
                </div>
                <div class="result-url">{escape(result.url)}</div>
                <div class="result-desc">{escape(result.description)}</div>
            </div>
"""
        
        html += """
        </div>
        <div class="footer">
            Generated by Dorker - Enterprise Multi-Search Engine Dorking Tool
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def to_console(results: Dict[str, List[SearchResult]], query: str):
        """Format and print results to console with rich formatting.
        
        Args:
            results: Dictionary mapping engine names to their results
            query: Original search query
        """
        if not HAS_RICH:
            # Fallback to plain text if rich not available
            print(f"\n=== Dork Query: {query} ===\n")
            total_results = 0
            for engine_name, engine_results in results.items():
                if not engine_results:
                    continue
                if engine_name == "all_engines":
                    print(f"COMBINED RESULTS ({len(engine_results)} unique)")
                else:
                    print(f"\n{engine_name.upper()} ({len(engine_results)} results)")
                print("-" * 80)
                for result in engine_results:
                    print(f"{result.url} [{result.engine}]")
                    total_results += 1
            print(f"\nTotal: {total_results}")
            return
        
        console = Console()
        console.print()
        console.print(Panel(
            Text(query, style="bold cyan"),
            title="🔍 Dork Query",
            border_style="cyan"
        ))
        
        # If combined results, show as single table
        if "all_engines" in results:
            engine_results = results["all_engines"]
            if engine_results:
                table = Table(
                    title=f"[bold magenta]COMBINED RESULTS[/] ({len(engine_results)} unique, deduplicated)",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold white",
                    border_style="dim"
                )
                
                table.add_column("URL", style="green")
                table.add_column("Engine", style="cyan", width=15)
                
                for result in engine_results:
                    table.add_row(result.url, result.engine)
                
                console.print(table)
                console.print()
        else:
            # Original behavior - show per engine
            for engine_name, engine_results in results.items():
                if not engine_results:
                    continue
                
                table = Table(
                    title=f"[bold magenta]{engine_name.upper()}[/] ({len(engine_results)} results)",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold white",
                    border_style="dim"
                )
                
                table.add_column("URL", style="green")
                table.add_column("Engine", style="cyan", width=15)
                
                for result in engine_results:
                    table.add_row(result.url, engine_name)
                
                console.print(table)
                console.print()
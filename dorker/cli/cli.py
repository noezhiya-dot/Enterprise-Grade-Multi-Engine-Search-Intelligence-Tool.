"""Command-line interface for dorker."""

import asyncio
import logging
import sys
import argparse
from typing import List, Dict, Any

from ..core import DorkerEngine
from ..models import SearchResult
from ..output import OutputFormatter
from ..utils import load_config
from ..engines import ENGINES_MAP

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None

logger = logging.getLogger(__name__)


class DorkerCLI:
    """Command-line interface for dorker."""
    
    def __init__(self):
        """Initialize CLI with argument parser."""
        self.parser = self._create_parser()
        self.console = Console() if HAS_RICH else None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Enterprise Multi-Search Engine Dorking Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --dork "intitle:index.of"
  %(prog)s --dork "inurl:admin" --engines google,bing,duckduckgo
  %(prog)s --dork "site:github.com" --output json --file results.json
  %(prog)s --dork-file dorks.txt --engines all --limit 100
            """
        )
        
        query_group = parser.add_mutually_exclusive_group(required=True)
        query_group.add_argument("-d", "--dork", help="Single dork query to search")
        query_group.add_argument("-f", "--dork-file", help="File containing dork queries (one per line)")
        query_group.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
        
        parser.add_argument(
            "-e", "--engines",
            default="all",
            help="Comma-separated list of engines or 'all' (default: all). Available: google,bing,duckduckgo,yahoo,yandex,brave,ask"
        )
        parser.add_argument("-l", "--limit", type=int, default=50, help="Max results per engine (default: 50)")
        parser.add_argument("-o", "--output", choices=["console", "json", "csv", "html"], default="console", help="Output format (default: console)")
        parser.add_argument("--file", help="Output file path (default: output/results.json)")
        parser.add_argument("-c", "--config", help="Path to config YAML file")
        parser.add_argument("--no-dedupe", action="store_true", help="Disable URL deduplication")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
        
        return parser
    
    async def run_interactive(self, dorker: DorkerEngine, engines: List[str], limit: int, dedupe: bool):
        """Run interactive dorking mode.
        
        Args:
            dorker: DorkerEngine instance
            engines: List of engines to use
            limit: Result limit per engine
            dedupe: Whether to deduplicate results
        """
        if self.console:
            self.console.print(Panel(
                "[bold cyan]Enterprise Multi-Search Engine Dorking Tool[/]\n"
                "[dim]Type your dork query and press Enter. Type 'quit' to exit.[/]",
                border_style="cyan"
            ))
        else:
            print("Interactive Mode - Type 'quit' to exit")
        
        while True:
            try:
                if self.console:
                    query = self.console.input("[bold green]dork>[/] ").strip()
                else:
                    query = input("dork> ").strip()
                
                if not query:
                    continue
                if query.lower() in ("quit", "exit", "q"):
                    if self.console:
                        self.console.print("[yellow]Goodbye![/]")
                    else:
                        print("Goodbye!")
                    break
                
                if HAS_RICH:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True
                    ) as progress:
                        progress.add_task(description="Searching...", total=None)
                        results = await dorker.search(query, engines, limit)
                else:
                    print("Searching...")
                    results = await dorker.search(query, engines, limit)
                
                OutputFormatter.to_console(results, query)
                
                total = sum(len(r) for r in results.values())
                if self.console:
                    self.console.print(f"[dim]Total: {total} results from {len([r for r in results.values() if r])} engines[/]")
                else:
                    print(f"Total: {total} results")
                
            except KeyboardInterrupt:
                if self.console:
                    self.console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/]")
                else:
                    print("\nInterrupted. Type 'quit' to exit.")
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error: {e}[/]")
                else:
                    print(f"Error: {e}")
    
    async def run(self):
        """Main CLI execution method."""
        args = self.parser.parse_args()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        config = load_config(args.config)
        dorker = DorkerEngine(config)
        
        if args.engines.lower() == "all":
            engines = list(ENGINES_MAP.keys())
        else:
            engines = [e.strip().lower() for e in args.engines.split(",")]
        
        invalid_engines = [e for e in engines if e not in ENGINES_MAP]
        if invalid_engines:
            if self.console:
                self.console.print(f"[red]Invalid engines: {', '.join(invalid_engines)}[/]")
                self.console.print(f"[dim]Available: {', '.join(ENGINES_MAP.keys())}[/]")
            else:
                print(f"Invalid engines: {', '.join(invalid_engines)}")
                print(f"Available: {', '.join(ENGINES_MAP.keys())}")
            sys.exit(1)
        
        dedupe = not args.no_dedupe
        
        if args.interactive:
            await self.run_interactive(dorker, engines, args.limit, dedupe)
            return
        
        if args.dork_file:
            try:
                with open(args.dork_file, "r") as f:
                    queries = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error reading dork file: {e}[/]")
                else:
                    print(f"Error reading dork file: {e}")
                sys.exit(1)
        else:
            queries = [args.dork]
        
        all_results: List[SearchResult] = []
        
        for query in queries:
            if self.console:
                self.console.print(f"[cyan]Searching:[/] {query}")
            else:
                print(f"Searching: {query}")
            
            if HAS_RICH:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as progress:
                    task = progress.add_task(description="Querying engines...", total=len(engines))
                    results = await dorker.search(query, engines, args.limit)
                    progress.update(task, completed=len(engines))
            else:
                print(f"Querying {len(engines)} engines...")
                results = await dorker.search(query, engines, args.limit)
            
            aggregated = dorker.aggregate_results(results, dedupe)
            
            if args.output == "console":
                # Combine all results for console display
                combined_results = {"all_engines": aggregated}
                OutputFormatter.to_console(combined_results, query)
            
            all_results.extend(aggregated)
            
            engine_stats = {k: len(v) for k, v in results.items() if v}
            if self.console:
                self.console.print(f"[dim]Results: {dict(engine_stats)}[/]")
            else:
                print(f"Results: {dict(engine_stats)}")
        
        if all_results:
            # Auto-export to results.json 
            output_file = args.file
            if args.output != "console":
                if not output_file:
                    # Create output directory if it doesn't exist
                    import os
                    os.makedirs("output", exist_ok=True)
                    output_file = "output/results.json"
                
                if args.output == "json":
                    content = OutputFormatter.to_json(all_results)
                elif args.output == "csv":
                    content = OutputFormatter.to_csv(all_results)
                elif args.output == "html":
                    content = OutputFormatter.to_html(all_results, args.dork or "Multiple Dorks")
                else:
                    content = OutputFormatter.to_json(all_results)
                
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                if self.console:
                    self.console.print(f"[green]✓ Results exported to {output_file}[/]")
                else:
                    print(f"Results exported to {output_file}")
            else:
                # Auto-export to results.json even for console output
                import os
                os.makedirs("output", exist_ok=True)
                output_file = "output/results.json"
                content = OutputFormatter.to_json(all_results)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                if self.console:
                    self.console.print(f"[green]✓ Results also saved to {output_file}[/]")
                else:
                    print(f"Results also saved to {output_file}")
        
        if self.console:
            self.console.print(f"\n[bold green]Total unique results: {len(all_results)}[/]")
        else:
            print(f"\nTotal unique results: {len(all_results)}")


def main():
    """Entry point for CLI."""
    cli = DorkerCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()

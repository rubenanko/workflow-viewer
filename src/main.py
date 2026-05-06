import argparse
import sys
import os
from parser import WorkflowParser
from generator import HTMLGenerator

def main():
    parser = argparse.ArgumentParser(description="GitHub Actions Workflow Visualizer CLI")
    parser.add_argument("input_dir", help="Directory containing GitHub Actions YAML files")
    parser.add_argument("-o", "--output", default="workflow_graph.html", help="Output HTML file name (default: workflow_graph.html)")

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: {args.input_dir} is not a valid directory.")
        sys.exit(1)

    print(f"Parsing workflows in: {args.input_dir}...")
    wf_parser = WorkflowParser(args.input_dir)
    workflows = wf_parser.parse()

    if not workflows:
        print("No valid GitHub Actions workflows found.")
        sys.exit(0)

    print(f"Found {len(workflows)} workflows. Generating HTML...")
    generator = HTMLGenerator(workflows)
    generator.generate(args.output)

    print(f"Success! Graph generated at: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()

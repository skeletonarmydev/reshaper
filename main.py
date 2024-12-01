import os
import subprocess
from typing import List, Dict, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config import REPO_PATH, GITHUB_URL, LLM_API_KEY, EXAMPLES, MODULE_INIT, INIT_FILES, IGNORE_DIRS, FILE_EXTENSIONS, DEPENDENCY_ORDER, VALIDATE_COMMAND
import json
import re
import time

def clone_repository(url: str, local_path: str) -> None:
    """Clone a GitHub repository to a local directory."""
    if not os.path.exists(local_path):
        print(f"Cloning repository from {url}...")
        subprocess.run(["git", "clone", url, local_path], check=True)
    else:
        print("Repository already cloned.")


def analyze_codebase(path: str) -> List[str]:
    """
    Analyze the codebase and identify areas for migration.
    Returns a list of file paths that require changes.
    """
    print(f"Analyzing codebase in {path}...")
    files_to_migrate = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".go"):  # Target Go files
                files_to_migrate.append(os.path.join(root, file))
    return files_to_migrate


def initialize_llm(api_key: str):
    """Initialize the GPT-3.5-turbo model."""
    return ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=api_key, temperature=0.2)


def apply_additions(examples: List[Dict], repo_path: str) -> None:
    """
    Apply all addition patterns first to create utility functions and types.
    This ensures they are only added once to the codebase.
    """
    additions = [ex for ex in examples if ex.get("type") == "addition"]
    if not additions:
        return

    # Create utils directory if it doesn't exist
    utils_dir = os.path.join(repo_path, "utils")
    os.makedirs(utils_dir, exist_ok=True)

    # Group additions by target file
    additions_by_file = {}
    for addition in additions:
        target_file = addition.get("target_file", "utils.go")
        if target_file not in additions_by_file:
            additions_by_file[target_file] = []
        additions_by_file[target_file].append(addition)

    # Apply additions to each target file
    for target_file, file_additions in additions_by_file.items():
        file_path = os.path.join(utils_dir, target_file)
        content = "package utils\n\n"
        for addition in file_additions:
            content += addition["replacement"] + "\n\n"
        
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created utility file: {file_path}")


def suggest_upgrades_llm(file_path: str, content: str, examples: List[Dict], llm: ChatOpenAI, validation_error: Optional[str] = None) -> str:
    """Use LLM to suggest code upgrades based on provided examples."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # Create prompt for the LLM
            prompt = f"""You are a code improvement assistant making minimal, targeted changes to code.

IMPORTANT RULES:
1. Return the ENTIRE file content with your changes
2. Make ONLY the specific improvements shown in the examples
3. DO NOT rewrite or restructure the code
4. DO NOT add new functions or change existing function signatures
5. PRESERVE all existing functionality
6. Only make changes that match the patterns exactly

Original code to modify:
{content}

Example transformations to apply (ONLY make these specific changes):
{json.dumps(examples, indent=2)}

Return the ENTIRE file content with your minimal changes. Wrap the code in code blocks."""

            if validation_error:
                prompt += f"\nThe previous attempt failed with this error:\n{validation_error}\nPlease fix the issues while keeping changes minimal."

            print(f"\nProcessing {file_path}...")
            print("Original content length:", len(content))

            # Get completion from LLM
            messages = [
                SystemMessage(content="You are a careful assistant that makes minimal, targeted code improvements."),
                HumanMessage(content=prompt)
            ]
            response = llm.invoke(messages)
            print("Got response from LLM")

            # Extract code from response
            code_match = re.search(r"```.*?\n(.*?)```", response.content, re.DOTALL)
            if code_match:
                suggested_code = code_match.group(1).strip()
                print("Suggested content length:", len(suggested_code))
                
                # Verify the changes aren't too drastic
                if len(suggested_code) < len(content) * 0.5 or len(suggested_code) > len(content) * 1.5:
                    print(f"Warning: Suggested changes were too drastic. Original: {len(content)}, Suggested: {len(suggested_code)}")
                    return content
                    
                # Check if any changes were actually made
                if suggested_code == content:
                    print("No changes were suggested")
                else:
                    print("Changes were suggested")
                    # Print a simple diff
                    original_lines = content.splitlines()
                    suggested_lines = suggested_code.splitlines()
                    for i, (orig, sugg) in enumerate(zip(original_lines, suggested_lines)):
                        if orig != sugg:
                            print(f"Line {i+1} changed:")
                            print(f"  Old: {orig}")
                            print(f"  New: {sugg}")
                            
                return suggested_code
            else:
                print("No code block found in response")
            return content

        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                print(f"Rate limit hit, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            raise


def split_into_chunks(content: str, max_size: int) -> List[str]:
    """Split a file's content into smaller chunks based on max_size."""
    lines = content.splitlines()
    chunks, current_chunk = [], []
    current_size = 0

    for line in lines:
        if current_size + len(line) + 1 > max_size:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(line)
        current_size += len(line) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def validate_changes(repo_path: str, file_path: str) -> bool:
    """Validate changes made to a file using the configured validation command."""
    if not VALIDATE_COMMAND:
        return True

    try:
        # Replace placeholder in working directory
        working_dir = VALIDATE_COMMAND["working_dir"].replace("{{repo_path}}", repo_path)

        # Run pre-validation commands
        for cmd in VALIDATE_COMMAND.get("pre_commands", []):
            print(f"Running '{cmd}' in {working_dir} to ensure dependencies...")
            result = subprocess.run(
                cmd.split(),
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Pre-validation command failed: {result.stderr}")
                return False

        # Run validation command
        print(f"Running '{VALIDATE_COMMAND['command']}' to validate {file_path}...")
        result = subprocess.run(
            VALIDATE_COMMAND["command"].split(),
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Validation failed: {result.stderr}")
            return False
            
        return True

    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False


def find_project_root_with_go_mod(file_path: str) -> str:
    """
    Recursively search for the project root containing go.mod starting from the file's directory.
    """
    current_dir = os.path.dirname(file_path)
    while current_dir != "/":
        if "go.mod" in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None


def create_pull_request(branch_name: str, commit_message: str) -> None:
    """Create a pull request for the changes."""
    print(f"Creating a pull request for branch {branch_name}...")
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)


def initialize_project(repo_path: str) -> None:
    """Initialize project with required files and configuration."""
    # Initialize module if needed
    if not os.path.exists(os.path.join(repo_path, "go.mod")):
        print("Initializing module...")
        for cmd in MODULE_INIT["commands"]:
            subprocess.run(cmd, cwd=repo_path, check=True)

    # Create required files
    for rel_path, content in INIT_FILES.items():
        file_path = os.path.join(repo_path, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if not os.path.exists(file_path):
            print(f"Creating {rel_path}...")
            with open(file_path, "w") as f:
                f.write(content)


def process_files(repo_path: str, llm: ChatOpenAI):
    """Process files in the repository according to the configured patterns."""
    # First apply any initial file templates
    apply_additions(EXAMPLES, repo_path)

    # Get list of files to process based on config
    target_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip files in directories that should be ignored
            if any(ignore in root for ignore in IGNORE_DIRS):
                continue
                
            # Only process files with configured extensions
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                target_files.append(os.path.join(root, file))

    # Sort files by dependency order if specified
    if DEPENDENCY_ORDER:
        target_files.sort(key=lambda x: next(
            (i for i, pattern in enumerate(DEPENDENCY_ORDER) if pattern in x), 
            len(DEPENDENCY_ORDER)
        ))

    # Process each file
    for file_path in target_files:
        try:
            print(f"\nProcessing {file_path}...")
            
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()

            # Get suggestions from LLM
            suggested_code = suggest_upgrades_llm(file_path, content, EXAMPLES, llm)
            
            # If changes were made
            if suggested_code != content:
                # Write changes to file
                with open(file_path, 'w') as f:
                    f.write(suggested_code)
                
                # Validate the changes if validation command is configured
                if VALIDATE_COMMAND:
                    if not validate_changes(repo_path, file_path):
                        # If validation fails, restore original content
                        with open(file_path, 'w') as f:
                            f.write(content)
                        print(f"Failed to validate changes for {file_path}. Reverting changes.")
                    else:
                        print(f"Successfully updated {file_path}")
                else:
                    print(f"Changes applied to {file_path} (no validation configured)")
            else:
                print(f"No changes needed for {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue


def main():
    """Main entry point for the code migration tool."""
    # Clone the repository if it doesn't exist
    if not os.path.exists(REPO_PATH):
        print(f"Cloning repository from {GITHUB_URL}...")
        subprocess.run(["git", "clone", GITHUB_URL, REPO_PATH], check=True)
    else:
        print("Repository already cloned.")

    # Initialize the project
    initialize_project(REPO_PATH)

    # Initialize the LLM
    llm = initialize_llm(LLM_API_KEY)

    # Process files
    process_files(REPO_PATH, llm)


if __name__ == "__main__":
    main()

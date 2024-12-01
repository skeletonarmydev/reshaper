import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Repository configuration
REPO_PATH = os.getenv("REPO_PATH", "/tmp/reshaper-repos/front-door")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/ascii27/front-door.git")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# File processing settings
FILE_EXTENSIONS = [".go"]  # Files to process
IGNORE_DIRS = ["vendor", "node_modules", ".git"]  # Directories to ignore
DEPENDENCY_ORDER = ["utils", "cmd", "main.go"]  # Process files in this order

# Validation settings
VALIDATE_COMMAND = {
    "command": "go build",
    "working_dir": "{{repo_path}}",  # {{repo_path}} will be replaced with actual path
    "pre_commands": ["go mod tidy"]  # Commands to run before validation
}

# Project-specific initialization
INIT_FILES = {
    "utils/errors.go": """package utils

// CheckErr logs an error if it exists
func CheckErr(err error) {
    if err != nil {
        panic(err)
    }
}
"""
}  # Close INIT_FILES

# Module initialization settings
MODULE_INIT = {
    "name": "front-door",
    "commands": [
        ["go", "mod", "init", "front-door"],
        ["go", "mod", "tidy"]
    ]
}

# Code transformation examples
EXAMPLES = [
    # Error handling patterns
    {
        "before": """if err != nil {
    fmt.Println(err.Error())
    return
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
    return
}"""
    },
    {
        "before": """if err != nil {
    fmt.Println(err)
    return
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
    return
}"""
    },
    {
        "before": """if err != nil {
    fmt.Println(err.Error())
    os.Exit(1)
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
}"""
    },
    {
        "before": """if err != nil {
    fmt.Println(err)
    os.Exit(1)
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
}"""
    },
    # More specific error handling cases
    {
        "before": """if err != nil {
    fmt.Println(err.Error())
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
}"""
    },
    {
        "before": """if err != nil {
    fmt.Println(err)
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
}"""
    },
    # Import cleanup patterns
    {
        "before": """import (
    "os"
    "fmt"
)""",
        "after": """import (
    "front-door/utils"
)"""
    },
    {
        "before": """import (
    "fmt"
    "os"
)""",
        "after": """import (
    "front-door/utils"
)"""
    },
    # Single import cleanup
    {
        "before": 'import "os"',
        "after": 'import "front-door/utils"'
    },
    {
        "before": 'import "fmt"',
        "after": 'import "front-door/utils"'
    },
    # More specific error patterns for Cobra commands
    {
        "before": """if err != nil {
    os.Exit(1)
}""",
        "after": """if err != nil {
    utils.CheckErr(err)
}"""
    },
    # Handle direct error printing without checks
    {
        "before": "fmt.Println(err.Error())",
        "after": "utils.CheckErr(err)"
    },
    {
        "before": "fmt.Println(err)",
        "after": "utils.CheckErr(err)"
    },
    # Import cleanup patterns with preserved imports
    {
        "before": """import (
    "fmt"
    "os"
    "strings"
)""",
        "after": """import (
    "front-door/utils"
    "strings"
)"""
    },
    {
        "before": """import (
    "os"
    "fmt"
    "strings"
)""",
        "after": """import (
    "front-door/utils"
    "strings"
)"""
    },
    {
        "before": """import (
    "fmt"
    "strings"
    "os"
)""",
        "after": """import (
    "front-door/utils"
    "strings"
)"""
    },
    {
        "before": """import (
    "fmt"
    "os"
    "github.com/jedib0t/go-pretty/v6/table"
)""",
        "after": """import (
    "front-door/utils"
    "github.com/jedib0t/go-pretty/v6/table"
)"""
    },
    {
        "before": """import (
    "fmt"
    "os"
    "strings"
    "github.com/jedib0t/go-pretty/v6/table"
)""",
        "after": """import (
    "front-door/utils"
    "strings"
    "github.com/jedib0t/go-pretty/v6/table"
)"""
    },
    # New patterns based on list.go and jira.go files
    {
        "before": """import (
    "fmt"
    "os"
    "strings"
)""",
        "after": """import (
    "front-door/utils"
    "strings"
)"""
    },
    {
        "before": """import (
    "fmt"
    "github.com/spf13/cobra"
)""",
        "after": """import (
    "front-door/utils"
    "github.com/spf13/cobra"
)"""
    },
    {
        "before": """import (
    "fmt"
    "github.com/andygrunwald/go-jira"
    "github.com/jedib0t/go-pretty/v6/table"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
    "os"
    "strings"
)""",
        "after": """import (
    "front-door/utils"
    "github.com/andygrunwald/go-jira"
    "github.com/jedib0t/go-pretty/v6/table"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
    "strings"
)"""
    },
    {
        "before": """if err != nil {             // Handle errors reading the config file
            panic(fmt.Errorf("fatal error config file: %w", err))
        }""",
        "after": """if err != nil {             // Handle errors reading the config file
            utils.CheckErr(err)
        }"""
    },
    {
        "before": """if err != nil {
            fmt.Println(err.Error())
            return
        }""",
        "after": """if err != nil {
            utils.CheckErr(err)
            return
        }"""
    },
    {
        "before": """if err != nil {
            fmt.Println(err.Error())
            return nil
        }""",
        "after": """if err != nil {
            utils.CheckErr(err)
            return nil
        }"""
    },
    {
        "before": """fmt.Println("Error: must also specify a resource like jira")""",
        "after": """utils.CheckErr(fmt.Errorf("Error: must also specify a resource like jira"))"""
    },
    {
        "before": """if err != nil { // Handle errors reading the config file
            fmt.Println(err.Error())
            return
        }""",
        "after": """if err != nil { // Handle errors reading the config file
            utils.CheckErr(err)
            return
        }"""
    },
    # Root command specific patterns
    {
        "before": """import (
    "os"

    "github.com/spf13/cobra"
)""",
        "after": """import (
    "front-door/utils"

    "github.com/spf13/cobra"
)"""
    },
    {
        "before": """if err != nil {
        os.Exit(1)
    }""",
        "after": """if err != nil {
        utils.CheckErr(err)
    }"""
    },
]

# Go-specific configuration
GO_IMPORT_RULES = {
    "utils_package": {
        "cmd_dir": "front-door/utils",  # For files in cmd/ directory
        "other_dir": "front-door/utils"  # For other files
    }
}

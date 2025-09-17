import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";
import chalk from "chalk";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

interface InstallationTask {
  name: string;
  status: "OK" | "SKIP" | "FAIL" | "MANUAL";
  detail: string;
}

export async function handleCommand(command: string): Promise<void> {
  if (command === "install") {
    await install();
  } else if (command === "uninstall") {
    await uninstall();
  } else {
    console.error(chalk.red(`Unknown command: ${command}`));
    process.exit(1);
  }
}

async function install(): Promise<void> {
  console.log(chalk.cyan.bold("\n============================================================"));
  console.log(chalk.cyan.bold("                SuperFlag v4.0.0 - Installer"));
  console.log(chalk.cyan.bold("            Contextual AI Enhancement Framework"));
  console.log(chalk.cyan.bold("                 TypeScript Edition"));
  console.log(chalk.cyan.bold("============================================================\n"));

  const tasks: InstallationTask[] = [];

  // 1. Setup flags.yaml
  const flagsPath = path.join(os.homedir(), ".superflag", "flags.yaml");
  if (await setupFlagsYaml(flagsPath)) {
    tasks.push({
      name: "Flags config",
      status: "OK",
      detail: "~/.superflag/flags.yaml",
    });
  } else {
    tasks.push({
      name: "Flags config",
      status: "SKIP",
      detail: "Already exists",
    });
  }

  // 2. Setup Claude context files
  if (await setupClaudeContext()) {
    tasks.push({
      name: "Context files",
      status: "OK",
      detail: "~/.claude/",
    });
  } else {
    tasks.push({
      name: "Context files",
      status: "SKIP",
      detail: "Already configured",
    });
  }

  // 3. Setup Python hooks (hybrid approach)
  if (await setupPythonHooks()) {
    tasks.push({
      name: "Hook system",
      status: "OK",
      detail: "~/.claude/hooks/",
    });
  } else {
    tasks.push({
      name: "Hook system",
      status: "SKIP",
      detail: "MCP will still work",
    });
  }

  // 4. Display MCP registration instructions
  tasks.push({
    name: "MCP server",
    status: "MANUAL",
    detail: "Manual registration required",
  });

  // Display results
  displayResults(tasks);

  // Show next steps
  console.log(chalk.yellow("\n📝 Next Steps:"));
  console.log(chalk.white("1. Register MCP server with Claude:"));
  console.log(chalk.cyan(`   claude mcp add superflag "npx" "-y" "superflag-mcp" -s user`));
  console.log(chalk.white("\n2. Restart Claude Code to activate changes"));
  console.log(chalk.white("\n3. Test with a prompt containing flags:"));
  console.log(chalk.green(`   "Analyze this code --analyze --strict"`));
}

async function uninstall(): Promise<void> {
  console.log(chalk.yellow.bold("\n============================================================"));
  console.log(chalk.yellow.bold("                SuperFlag v4.0.0 - Uninstaller"));
  console.log(chalk.yellow.bold("============================================================\n"));

  const tasks: InstallationTask[] = [];

  // Remove hook file
  const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");
  if (await removeFile(hookPath)) {
    tasks.push({
      name: "Hook file",
      status: "OK",
      detail: "Removed",
    });
  } else {
    tasks.push({
      name: "Hook file",
      status: "SKIP",
      detail: "Not found",
    });
  }

  // Remove context files
  const claudeDir = path.join(os.homedir(), ".claude");
  const contextFiles = ["SUPERFLAG.md", "CLAUDE.md"];
  for (const file of contextFiles) {
    const filePath = path.join(claudeDir, file);
    if (await removeFile(filePath)) {
      tasks.push({
        name: file,
        status: "OK",
        detail: "Removed",
      });
    }
  }

  // Note about MCP removal
  tasks.push({
    name: "MCP server",
    status: "MANUAL",
    detail: "Remove with: claude mcp remove superflag",
  });

  displayResults(tasks);
}

async function setupFlagsYaml(flagsPath: string): Promise<boolean> {
  try {
    // Check if already exists
    await fs.access(flagsPath);
    return false; // Already exists
  } catch {
    // Create directory
    await fs.mkdir(path.dirname(flagsPath), { recursive: true });

    // Copy from package or use embedded default
    const sourcePath = path.join(__dirname, "..", "flags.yaml");
    try {
      await fs.copyFile(sourcePath, flagsPath);
    } catch {
      // Create default if source doesn't exist
      const defaultContent = getDefaultFlagsYaml();
      await fs.writeFile(flagsPath, defaultContent, "utf-8");
    }

    return true;
  }
}

async function setupClaudeContext(): Promise<boolean> {
  const claudeDir = path.join(os.homedir(), ".claude");

  try {
    await fs.mkdir(claudeDir, { recursive: true });

    // Copy CLAUDE.md and SUPERFLAG.md
    const files = [
      { name: "CLAUDE.md", content: getClaudeMdContent() },
      { name: "SUPERFLAG.md", content: getSuperflagMdContent() },
    ];

    for (const file of files) {
      const filePath = path.join(claudeDir, file.name);
      await fs.writeFile(filePath, file.content, "utf-8");
    }

    return true;
  } catch {
    return false;
  }
}

async function setupPythonHooks(): Promise<boolean> {
  const hooksDir = path.join(os.homedir(), ".claude", "hooks");

  try {
    await fs.mkdir(hooksDir, { recursive: true });

    // Copy Python hook file (keeping Python for hook compatibility)
    const hookPath = path.join(hooksDir, "superflag.py");
    const hookContent = getPythonHookContent();
    await fs.writeFile(hookPath, hookContent, "utf-8");

    // Update settings.json to register hook
    const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
    await updateClaudeSettings(settingsPath);

    return true;
  } catch {
    return false;
  }
}

async function updateClaudeSettings(settingsPath: string): Promise<void> {
  let settings: any = {};

  try {
    const content = await fs.readFile(settingsPath, "utf-8");
    settings = JSON.parse(content);
  } catch {
    // Create new settings if doesn't exist
  }

  // Ensure hooks structure exists
  if (!settings.hooks) {
    settings.hooks = {};
  }
  if (!settings.hooks.UserPromptSubmit) {
    settings.hooks.UserPromptSubmit = [];
  }

  // Remove old superflag hooks
  settings.hooks.UserPromptSubmit = settings.hooks.UserPromptSubmit.filter(
    (hook: any) => !hook.hooks?.[0]?.command?.includes("superflag.py")
  );

  // Add new hook
  const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");
  settings.hooks.UserPromptSubmit.push({
    description: "SuperFlag Context Engine",
    hooks: [
      {
        trigger: "UserPromptSubmit",
        command: `python "${hookPath}"`,
      },
    ],
  });

  await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2), "utf-8");
}

async function removeFile(filePath: string): Promise<boolean> {
  try {
    await fs.unlink(filePath);
    return true;
  } catch {
    return false;
  }
}

function displayResults(tasks: InstallationTask[]): void {
  console.log(chalk.bold("\n📋 Installation Summary:"));
  console.log("─".repeat(60));

  for (const task of tasks) {
    const statusColor =
      task.status === "OK"
        ? chalk.green
        : task.status === "SKIP"
        ? chalk.yellow
        : task.status === "FAIL"
        ? chalk.red
        : chalk.cyan;

    const statusIcon =
      task.status === "OK"
        ? "✓"
        : task.status === "SKIP"
        ? "○"
        : task.status === "FAIL"
        ? "✗"
        : "⚠";

    console.log(
      `${statusColor(statusIcon)} ${task.name.padEnd(20)} ${statusColor(
        `[${task.status}]`
      )} ${chalk.gray(task.detail)}`
    );
  }
  console.log("─".repeat(60));
}

// Content generation functions (simplified versions)
function getDefaultFlagsYaml(): string {
  return `# SuperFlag Configuration
available_flags:
  - name: "--analyze"
    description: "Analyze through pattern, root, and validation lenses"
    directive: "Identify root causes through multi-perspective analysis."
    verification: "Analyzed from 3+ perspectives"
    priority: 1

  - name: "--strict"
    description: "Execute with zero errors and full transparency"
    directive: "Ensure zero-error execution with complete transparency."
    verification: "Zero warnings/errors"
    priority: 1
`;
}

function getClaudeMdContent(): string {
  return `# Context Engine Instructions
@SUPERFLAG.md
`;
}

function getSuperflagMdContent(): string {
  return `# SuperFlag Context Engine
MCP Protocol: get_directives([flags])

<core_workflow>
When --flag detected:
1. Call MCP tool: get_directives([flags])
2. Apply directives completely
</core_workflow>
`;
}

function getPythonHookContent(): string {
  // This remains in Python for Claude Code compatibility
  return `#!/usr/bin/env python3
"""SuperFlag Claude Code Hook - TypeScript Edition Bridge"""

import sys
import json

def main():
    try:
        user_input = sys.stdin.read()
        # Basic flag detection (simplified)
        flags = []
        for word in user_input.split():
            if word.startswith('--'):
                flags.append(word)

        if flags:
            print(json.dumps({
                "type": "system",
                "message": f"Flags detected: {', '.join(flags)}. Use get_directives() tool."
            }))
    except Exception as e:
        pass

if __name__ == "__main__":
    main()
`;
}
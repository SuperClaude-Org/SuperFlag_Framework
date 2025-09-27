import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";
import chalk from "chalk";
import * as yaml from "js-yaml";
import inquirer from "inquirer";
import { VERSION } from "./version.js";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface InstallationTask {
  name: string;
  status: "OK" | "SKIP" | "FAIL";
  detail: string;
}

interface Platform {
  name: string;
  configDir: string;
  mainFile: string;
  contextFile: string;
  type: "markdown" | "yaml";
}

const PLATFORMS: Platform[] = [
  {
    name: "Claude Code",
    configDir: path.join(os.homedir(), ".claude"),
    mainFile: "CLAUDE.md",
    contextFile: "SUPERFLAG.md",
    type: "markdown"
  },
  {
    name: "Gemini CLI",
    configDir: path.join(os.homedir(), ".gemini"),
    mainFile: "GEMINI.md",
    contextFile: "SUPERFLAG.md",
    type: "markdown"
  },
  {
    name: "Continue",
    configDir: path.join(os.homedir(), ".continue"),
    mainFile: "config.yaml",
    contextFile: "",
    type: "yaml"
  }
];

export async function handleCommand(command: string, args: string[] = []): Promise<void> {
  // Handle version in install command
  if (args.includes("--version") || args.includes("-v")) {
    console.log(VERSION);
    process.exit(0);
  }

  // Check if --target argument is provided for non-interactive mode
  const targetIndex = args.indexOf("--target");
  const hasExplicitTarget = targetIndex !== -1 && args[targetIndex + 1];

  // Also check for direct target argument (e.g., "install cc")
  const directTarget = args.length > 0 && !args[0].startsWith("-") ? args[0] : null;
  const target = hasExplicitTarget ? args[targetIndex + 1] : directTarget;

  if (target) {
    // Non-interactive mode with explicit target
    if (command === "install") {
      await install(target);
    } else if (command === "uninstall") {
      await uninstall(target);
    } else {
      console.error(chalk.red(`Unknown command: ${command}`));
      showUsage();
      process.exit(1);
    }
  } else {
    // Interactive mode - action determined by command
    if (command === "install") {
      await interactiveInstall();
    } else if (command === "uninstall") {
      await interactiveUninstall();
    } else {
      console.error(chalk.red(`Unknown command: ${command}`));
      showUsage();
      process.exit(1);
    }
  }
}

async function interactiveInstall(): Promise<void> {
  console.log(chalk.cyan.bold("\n============================================================"));
  console.log(chalk.cyan.bold(`                SuperFlag v${VERSION} - Installer`));
  console.log(chalk.cyan.bold("============================================================\n"));

  // Check current installation status
  const installedPlatforms = await checkInstalledPlatforms();

  // Ask which platforms to install
  const platformChoices = PLATFORMS.map(p => ({
    name: installedPlatforms.includes(p.name)
      ? `${p.name} ${chalk.green("(installed)")}`
      : p.name,
    value: p.name,
    checked: !installedPlatforms.includes(p.name) // Pre-select non-installed platforms
  }));

  const platformAnswer = await inquirer.prompt([
    {
      type: "checkbox",
      name: "platforms",
      message: "Select platforms to install:",
      choices: platformChoices,
      validate: (answer) => {
        if (answer.length === 0) {
          return "Please select at least one platform.";
        }
        return true;
      }
    }
  ]);

  if (platformAnswer.platforms.length === 0) {
    console.log(chalk.yellow("No platforms selected. Exiting."));
    process.exit(0);
  }

  // Confirmation
  const confirmAnswer = await inquirer.prompt([
    {
      type: "confirm",
      name: "confirm",
      message: `Install SuperFlag for ${platformAnswer.platforms.join(", ")}?`,
      default: true
    }
  ]);

  if (!confirmAnswer.confirm) {
    console.log(chalk.gray("Operation cancelled."));
    process.exit(0);
  }

  await installInteractive(platformAnswer.platforms);
}

async function interactiveUninstall(): Promise<void> {
  console.log(chalk.yellow.bold("\n============================================================"));
  console.log(chalk.yellow.bold(`                SuperFlag v${VERSION} - Uninstaller`));
  console.log(chalk.yellow.bold("============================================================\n"));

  // Check current installation status
  const installedPlatforms = await checkInstalledPlatforms();

  if (installedPlatforms.length === 0) {
    console.log(chalk.yellow("SuperFlag is not installed on any platform."));
    process.exit(0);
  }

  // Ask which platforms to uninstall
  const platformChoices = PLATFORMS.map(p => ({
    name: installedPlatforms.includes(p.name)
      ? `${p.name} ${chalk.green("(installed)")}`
      : `${p.name} ${chalk.gray("(not installed)")}`,
    value: p.name,
    disabled: !installedPlatforms.includes(p.name),
    checked: installedPlatforms.includes(p.name) // Pre-select installed platforms
  }));

  const platformAnswer = await inquirer.prompt([
    {
      type: "checkbox",
      name: "platforms",
      message: "Select platforms to uninstall:",
      choices: platformChoices,
      validate: (answer) => {
        if (answer.length === 0) {
          return "Please select at least one platform.";
        }
        return true;
      }
    }
  ]);

  if (platformAnswer.platforms.length === 0) {
    console.log(chalk.yellow("No platforms selected. Exiting."));
    process.exit(0);
  }

  // Confirmation
  const confirmAnswer = await inquirer.prompt([
    {
      type: "confirm",
      name: "confirm",
      message: `Uninstall SuperFlag from ${platformAnswer.platforms.join(", ")}?`,
      default: true
    }
  ]);

  if (!confirmAnswer.confirm) {
    console.log(chalk.gray("Operation cancelled."));
    process.exit(0);
  }

  await uninstallInteractive(platformAnswer.platforms);
}

async function checkInstalledPlatforms(): Promise<string[]> {
  const installed: string[] = [];

  for (const platform of PLATFORMS) {
    try {
      if (platform.type === "markdown") {
        const mainPath = path.join(platform.configDir, platform.mainFile);
        const content = await fs.readFile(mainPath, "utf-8");
        if (content.includes("@SUPERFLAG.md")) {
          installed.push(platform.name);
        }
      } else if (platform.type === "yaml") {
        const configPath = path.join(platform.configDir, platform.mainFile);
        const content = await fs.readFile(configPath, "utf-8");
        const config = yaml.load(content) as any;
        if (config.rules?.some((rule: any) => rule.title === "SuperFlag")) {
          installed.push(platform.name);
        }
      }
    } catch {
      // Not installed or file doesn't exist
    }
  }

  return installed;
}

async function installInteractive(platformNames: string[]): Promise<void> {
  const tasks: InstallationTask[] = [];

  // 1. Ensure SuperFlag profile files
  const flagsPath = path.join(os.homedir(), ".superflag", "default.yaml");
  if (await setupFlagsYaml(flagsPath)) {
    tasks.push({
      name: "Flags config",
      status: "OK",
      detail: "~/.superflag/default.yaml",
    });
  } else {
    tasks.push({
      name: "Flags config",
      status: "SKIP",
      detail: "Already exists",
    });
  }

  // 2. Setup selected platforms
  const selectedPlatforms = PLATFORMS.filter(p => platformNames.includes(p.name));

  for (const platform of selectedPlatforms) {
    const result = await setupPlatform(platform, "install");
    tasks.push(result);

    // Setup Python hooks for Claude only
    if (platform.name === "Claude Code") {
      const hookResult = await setupPythonHooks();
      tasks.push({
        name: "Claude hooks",
        status: hookResult ? "OK" : "SKIP",
        detail: hookResult ? "~/.claude/hooks/" : "Already exists"
      });

      // Register hook in settings.json
      const settingsResult = await registerHookInSettings();
      tasks.push({
        name: "Claude settings",
        status: settingsResult ? "OK" : "SKIP",
        detail: settingsResult ? "Hook registered" : "Already registered"
      });
    }

    // Register MCP server for all platforms
    const mcpResult = await registerMcpServer(platform);
    tasks.push(mcpResult);
  }

  // Display results
  displayResults(tasks);

  // Show next steps
  showNextSteps(platformNames);
}

async function uninstallInteractive(platformNames: string[]): Promise<void> {
  const tasks: InstallationTask[] = [];

  // Remove from selected platforms
  const selectedPlatforms = PLATFORMS.filter(p => platformNames.includes(p.name));

  for (const platform of selectedPlatforms) {
    const result = await setupPlatform(platform, "uninstall");
    tasks.push(result);

    // Remove Python hooks for Claude only
    if (platform.name === "Claude Code") {
      const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");
      if (await removeFile(hookPath)) {
        tasks.push({
          name: "Claude hooks",
          status: "OK",
          detail: "Removed",
        });
      } else {
        tasks.push({
          name: "Claude hooks",
          status: "SKIP",
          detail: "Not found",
        });
      }

      // Remove hook from settings.json
      const settingsResult = await unregisterHookFromSettings();
      tasks.push({
        name: "Claude settings",
        status: settingsResult ? "OK" : "SKIP",
        detail: settingsResult ? "Hook unregistered" : "Not found"
      });
    }

    // Unregister MCP server for all platforms
    const mcpResult = await unregisterMcpServer(platform);
    tasks.push(mcpResult);
  }

  displayResults(tasks);
}

async function install(targetArg: string): Promise<void> {
  console.log(chalk.cyan.bold("\n============================================================"));
  console.log(chalk.cyan.bold(`                SuperFlag v${VERSION} - Installer`));
  console.log(chalk.cyan.bold("============================================================\n"));

  const tasks: InstallationTask[] = [];

  // 1. Ensure SuperFlag profile files
  const flagsPath = path.join(os.homedir(), ".superflag", "default.yaml");
  if (await setupFlagsYaml(flagsPath)) {
    tasks.push({
      name: "Flags config",
      status: "OK",
      detail: "~/.superflag/default.yaml",
    });
  } else {
    tasks.push({
      name: "Flags config",
      status: "SKIP",
      detail: "Already exists",
    });
  }

  // 2. Setup platforms
  const platforms = getPlatforms(targetArg);

  for (const platform of platforms) {
    const result = await setupPlatform(platform, "install");
    tasks.push(result);

    // Setup Python hooks for Claude only
    if (platform.name === "Claude Code") {
      const hookResult = await setupPythonHooks();
      tasks.push({
        name: "Claude hooks",
        status: hookResult ? "OK" : "SKIP",
        detail: hookResult ? "~/.claude/hooks/" : "Already exists"
      });

      // Register hook in settings.json
      const settingsResult = await registerHookInSettings();
      tasks.push({
        name: "Claude settings",
        status: settingsResult ? "OK" : "SKIP",
        detail: settingsResult ? "Hook registered" : "Already registered"
      });
    }

    // Register MCP server for all platforms
    const mcpResult = await registerMcpServer(platform);
    tasks.push(mcpResult);
  }

  // Display results
  displayResults(tasks);

  // Show next steps
  const platformNames = platforms.map(p => p.name);
  showNextSteps(platformNames);
}

async function uninstall(targetArg: string): Promise<void> {
  console.log(chalk.yellow.bold("\n============================================================"));
  console.log(chalk.yellow.bold(`                SuperFlag v${VERSION} - Uninstaller`));
  console.log(chalk.yellow.bold("============================================================\n"));

  const tasks: InstallationTask[] = [];

  // Remove from platforms
  const platforms = getPlatforms(targetArg);

  for (const platform of platforms) {
    const result = await setupPlatform(platform, "uninstall");
    tasks.push(result);

    // Remove Python hooks for Claude only
    if (platform.name === "Claude Code") {
      const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");
      if (await removeFile(hookPath)) {
        tasks.push({
          name: "Claude hooks",
          status: "OK",
          detail: "Removed",
        });
      } else {
        tasks.push({
          name: "Claude hooks",
          status: "SKIP",
          detail: "Not found",
        });
      }

      // Remove hook from settings.json
      const settingsResult = await unregisterHookFromSettings();
      tasks.push({
        name: "Claude settings",
        status: settingsResult ? "OK" : "SKIP",
        detail: settingsResult ? "Hook unregistered" : "Not found"
      });
    }

    // Unregister MCP server for all platforms
    const mcpResult = await unregisterMcpServer(platform);
    tasks.push(mcpResult);
  }

  displayResults(tasks);

  // Check if Claude Code was in the uninstall and show manual MCP removal note
  const claudeCodeIncluded = platforms.some(p => p.name === "Claude Code");
  if (claudeCodeIncluded) {
    console.log(chalk.yellow("\n⚠  Note: Remove Claude Code MCP server manually with:"));
    console.log(chalk.gray("   claude mcp remove superflag"));
  }
}

function showNextSteps(platformNames: string[]): void {
  console.log(chalk.yellow("\n📝 Next Steps:"));

  if (platformNames.includes("Claude Code")) {
    console.log(chalk.white("\nFor Claude Code:"));
    console.log(chalk.cyan("  1. Restart Claude Code"));
    console.log(chalk.cyan("  2. Verify connection: claude mcp list"));
  }

  if (platformNames.includes("Gemini CLI")) {
    console.log(chalk.white("\nFor Gemini CLI:"));
    console.log(chalk.cyan("  1. Restart Gemini CLI"));
    console.log(chalk.cyan("  2. MCP server already configured"));
  }

  if (platformNames.includes("Continue")) {
    console.log(chalk.white("\nFor Continue:"));
    console.log(chalk.cyan("  1. Restart VS Code with Continue extension"));
    console.log(chalk.cyan("  2. MCP server already configured"));
  }

  console.log(chalk.green("\n✅ Test with: \"Analyze this code --analyze --strict\""));
}

function showUsage(): void {
  console.log("\nUsage:");
  console.log("  Interactive mode:");
  console.log("    superflag-install install");
  console.log("    superflag-install uninstall");
  console.log("\n  Non-interactive mode:");
  console.log("    superflag-install install --target claude-code|gemini-cli|cn|all");
  console.log("    superflag-install uninstall --target claude-code|gemini-cli|cn|all");
}

function getPlatforms(targetArg: string): Platform[] {
  if (targetArg === "all") {
    return PLATFORMS;
  }

  const platformMap: Record<string, Platform> = {
    "claude-code": PLATFORMS[0],
    "cc": PLATFORMS[0],  // Add shortcut
    "gemini-cli": PLATFORMS[1],
    "gemini": PLATFORMS[1],  // Add shortcut
    "cn": PLATFORMS[2],
    "continue": PLATFORMS[2]  // Add full name
  };

  if (!platformMap[targetArg]) {
    console.error(chalk.red(`Error: Invalid target '${targetArg}'`));
    console.log(chalk.yellow("Valid targets: claude-code (cc), gemini-cli (gemini), cn (continue), all"));
    process.exit(1);
  }

  return [platformMap[targetArg]];
}

async function setupPlatform(platform: Platform, mode: "install" | "uninstall"): Promise<InstallationTask> {
  try {
    if (platform.type === "markdown") {
      if (mode === "install") {
        return await installMarkdownPlatform(platform);
      } else {
        return await uninstallMarkdownPlatform(platform);
      }
    } else if (platform.type === "yaml") {
      if (mode === "install") {
        return await installYamlPlatform(platform);
      } else {
        return await uninstallYamlPlatform(platform);
      }
    }

    return {
      name: platform.name,
      status: "FAIL",
      detail: "Unknown platform type"
    };
  } catch (error) {
    return {
      name: platform.name,
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

async function installMarkdownPlatform(platform: Platform): Promise<InstallationTask> {
  // Create directory if needed
  await fs.mkdir(platform.configDir, { recursive: true });

  // 1. Create SUPERFLAG.md
  const contextPath = path.join(platform.configDir, platform.contextFile);
  await fs.writeFile(contextPath, getSuperflagMdContent(), "utf-8");

  // 2. Update main file (CLAUDE.md or GEMINI.md)
  const mainPath = path.join(platform.configDir, platform.mainFile);
  let mainContent = "";
  let fileExists = false;

  try {
    mainContent = await fs.readFile(mainPath, "utf-8");
    fileExists = true;
  } catch {
    // File doesn't exist, will create new
    mainContent = "";
  }

  // Check if already has @SUPERFLAG.md
  if (!mainContent.includes("@SUPERFLAG.md")) {
    // Add @SUPERFLAG.md at the end
    if (mainContent && !mainContent.endsWith("\n")) {
      mainContent += "\n";
    }
    mainContent += "@SUPERFLAG.md\n";
    await fs.writeFile(mainPath, mainContent, "utf-8");

    return {
      name: platform.name,
      status: "OK",
      detail: fileExists ? `${platform.mainFile} updated` : `${platform.mainFile} created`
    };
  }

  return {
    name: platform.name,
    status: "SKIP",
    detail: "@SUPERFLAG.md already exists"
  };
}

async function uninstallMarkdownPlatform(platform: Platform): Promise<InstallationTask> {
  let hasChanges = false;

  // 1. Remove SUPERFLAG.md file
  const contextPath = path.join(platform.configDir, platform.contextFile);
  if (await removeFile(contextPath)) {
    hasChanges = true;
  }

  // 2. Remove @SUPERFLAG.md from main file
  const mainPath = path.join(platform.configDir, platform.mainFile);
  try {
    let content = await fs.readFile(mainPath, "utf-8");
    // Remove all occurrences of @SUPERFLAG.md (with or without newline)
    const newContent = content.replace(/@SUPERFLAG\.md\n?/g, "");

    if (newContent !== content) {
      await fs.writeFile(mainPath, newContent, "utf-8");
      hasChanges = true;
    }
  } catch {
    // File doesn't exist, nothing to remove
  }

  return {
    name: platform.name,
    status: hasChanges ? "OK" : "SKIP",
    detail: hasChanges ? "Removed" : "Not found"
  };
}

async function installYamlPlatform(platform: Platform): Promise<InstallationTask> {
  // For Continue platform
  await fs.mkdir(platform.configDir, { recursive: true });

  const configPath = path.join(platform.configDir, platform.mainFile);
  let config: any = {};
  let fileExists = false;

  try {
    const content = await fs.readFile(configPath, "utf-8");
    config = yaml.load(content) || {};
    fileExists = true;
  } catch {
    // File doesn't exist, create new config
    config = {};
  }

  // Ensure rules array exists
  if (!config.rules) {
    config.rules = [];
  }

  // Check if SuperFlag rule already exists
  const hasSuperflag = config.rules.some((rule: any) =>
    rule.title === "SuperFlag"
  );

  if (!hasSuperflag) {
    // Add SuperFlag rule
    config.rules.push({
      title: "SuperFlag",
      pattern: "--\\w+",
      message: "Flag detected. Execute MCP: get_directives([detected_flags])\n" +
               "Available: --analyze, --strict, --performance, --refactor, --lean, --discover, " +
               "--explain, --save, --parallel, --todo, --seq, --concise, --git, --readonly, " +
               "--load, --collab, --reset, --auto"
    });

    const yamlStr = yaml.dump(config, {
      indent: 2,
      lineWidth: 120,
      noRefs: true
    });

    await fs.writeFile(configPath, yamlStr, "utf-8");

    return {
      name: platform.name,
      status: "OK",
      detail: fileExists ? "Rule added" : "config.yaml created"
    };
  }

  return {
    name: platform.name,
    status: "SKIP",
    detail: "Rule already exists"
  };
}

async function uninstallYamlPlatform(platform: Platform): Promise<InstallationTask> {
  const configPath = path.join(platform.configDir, platform.mainFile);

  try {
    const content = await fs.readFile(configPath, "utf-8");
    const config = yaml.load(content) as any;

    if (config.rules) {
      const originalLength = config.rules.length;
      // Remove SuperFlag rule
      config.rules = config.rules.filter((rule: any) =>
        rule.title !== "SuperFlag"
      );

      if (config.rules.length < originalLength) {
        const yamlStr = yaml.dump(config, {
          indent: 2,
          lineWidth: 120,
          noRefs: true
        });

        await fs.writeFile(configPath, yamlStr, "utf-8");

        return {
          name: platform.name,
          status: "OK",
          detail: "Rule removed"
        };
      }
    }
  } catch {
    // File doesn't exist or error reading
  }

  return {
    name: platform.name,
    status: "SKIP",
    detail: "Not found"
  };
}

async function setupFlagsYaml(defaultProfilePath: string): Promise<boolean> {
  const configDir = path.dirname(defaultProfilePath);
  const legacyFlagsPath = path.join(configDir, "flags.yaml");
  const legacySuperflagPath = path.join(configDir, "superflag.yaml");

  await fs.mkdir(configDir, { recursive: true });

  // Handle legacy files
  try {
    await fs.access(legacyFlagsPath);
    const backupPath = path.join(configDir, `flags.yaml.backup_${Date.now()}`);
    await fs.rename(legacyFlagsPath, backupPath);
    console.log(chalk.gray(`Legacy flags.yaml backed up to ${backupPath}`));
  } catch {
    // No legacy flags.yaml to migrate
  }

  let created = false;

  const packagedRoot = path.join(__dirname, "..", ".superflag");
  const profileFiles = [
    "default.yaml",
    "claude.yaml",
    "codex.yaml",
    "continue.yaml",
    "gemini.yaml",
  ];

  for (const file of profileFiles) {
    const targetPath = path.join(configDir, file);
    try {
      await fs.access(targetPath);
    } catch {
      const sourcePath = path.join(packagedRoot, file);
      await fs.copyFile(sourcePath, targetPath);
      created = true;
    }
  }

  const packagedConfigsDir = path.join(packagedRoot, "configs");
  const targetConfigsDir = path.join(configDir, "configs");
  await fs.mkdir(targetConfigsDir, { recursive: true });

  if (await exists(legacySuperflagPath)) {
    const backupPath = path.join(configDir, `superflag.yaml.legacy_${Date.now()}`);
    await fs.rename(legacySuperflagPath, backupPath);
    console.log(chalk.gray(`Legacy superflag.yaml backed up to ${backupPath}`));
  }

  const entries = await fs.readdir(packagedConfigsDir, { withFileTypes: true });
  for (const entry of entries) {
    const source = path.join(packagedConfigsDir, entry.name);
    const destination = path.join(targetConfigsDir, entry.name);

    if (await exists(destination)) {
      continue;
    }

    if (entry.isDirectory()) {
      await copyDirectoryRecursive(source, destination);
    } else {
      await fs.copyFile(source, destination);
    }
    created = true;
  }

  return created;
}

async function exists(targetPath: string): Promise<boolean> {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function copyDirectoryRecursive(source: string, destination: string): Promise<void> {
  await fs.mkdir(destination, { recursive: true });
  const entries = await fs.readdir(source, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(source, entry.name);
    const destPath = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      await copyDirectoryRecursive(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

async function unregisterHookFromSettings(): Promise<boolean> {
  const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
  const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");

  try {
    const settingsContent = await fs.readFile(settingsPath, 'utf-8');
    const settings = JSON.parse(settingsContent);

    if (!settings.hooks || !settings.hooks.UserPromptSubmit) {
      return false; // No hooks to remove
    }

    const hookCommand = `python "${hookPath}"`;
    const initialLength = settings.hooks.UserPromptSubmit.length;

    // Remove SuperFlag hook
    settings.hooks.UserPromptSubmit = settings.hooks.UserPromptSubmit.filter((h: any) => {
      if (h.hooks && h.hooks.some((hook: any) =>
        hook.command && hook.command.includes("superflag.py"))) return false;
      return true;
    });

    if (settings.hooks.UserPromptSubmit.length === initialLength) {
      return false; // Nothing was removed
    }

    // Save updated settings
    await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2), 'utf-8');
    return true;
  } catch (error) {
    return false;
  }
}

async function registerHookInSettings(): Promise<boolean> {
  const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
  const hookPath = path.join(os.homedir(), ".claude", "hooks", "superflag.py");

  try {
    // Read existing settings or create new
    let settings: any = {};
    try {
      const settingsContent = await fs.readFile(settingsPath, 'utf-8');
      settings = JSON.parse(settingsContent);
    } catch {
      // Create new settings if doesn't exist
      settings = { hooks: { UserPromptSubmit: [] } };
    }

    // Ensure hooks structure exists
    if (!settings.hooks) {
      settings.hooks = {};
    }
    if (!settings.hooks.UserPromptSubmit) {
      settings.hooks.UserPromptSubmit = [];
    }

    // Check if hook already exists
    const hookCommand = `python "${hookPath}"`;
    const existingHook = settings.hooks.UserPromptSubmit.find((h: any) =>
      h.hooks && h.hooks.some((hook: any) => hook.command === hookCommand)
    );

    if (existingHook) {
      return false; // Already registered
    }

    // Add hook (matching Python format exactly)
    settings.hooks.UserPromptSubmit.push({
      matcher: "",
      hooks: [{
        type: "command",
        command: hookCommand
      }]
    });

    // Save settings
    await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2), 'utf-8');
    return true;
  } catch (error) {
    return false;
  }
}

async function setupPythonHooks(): Promise<boolean> {
  const hooksDir = path.join(os.homedir(), ".claude", "hooks");

  try {
    await fs.mkdir(hooksDir, { recursive: true });

    const hookPath = path.join(hooksDir, "superflag.py");

    // Check if already exists
    try {
      await fs.access(hookPath);
      return false; // Already exists
    } catch {
      // Copy the actual hook file from hooks directory
      const sourceHookPath = path.join(__dirname, '..', 'hooks', 'superflag.py');
      try {
        const hookContent = await fs.readFile(sourceHookPath, 'utf-8');
        await fs.writeFile(hookPath, hookContent, "utf-8");
        return true;
      } catch {
        // Fallback to simple hook if source file not found
        await fs.writeFile(hookPath, getPythonHookContent(), "utf-8");
        return true;
      }
    }
  } catch {
    return false;
  }
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
  console.log(chalk.blue("\n📋 Summary:"));
  console.log("─".repeat(60));

  for (const task of tasks) {
    const symbol =
      task.status === "OK"
        ? chalk.green("✓")
        : task.status === "SKIP"
        ? chalk.gray("○")
        : chalk.red("✗");

    const statusColor =
      task.status === "OK"
        ? chalk.green
        : task.status === "SKIP"
        ? chalk.gray
        : chalk.red;

    console.log(
      `${symbol} ${task.name.padEnd(20)} ${statusColor(
        `[${task.status}]`
      )} ${chalk.gray(task.detail)}`
    );
  }
  console.log("─".repeat(60));
}

function getSuperflagMdContent(): string {
  return `# SuperFlag
MCP Protocol: get_directives([flags])

## Core Workflow
<core_workflow>
When flags detected in user input:
1. Execute MCP tool: get_directives([detected_flags])
2. Apply directives completely and in order
3. Verify compliance at checkpoints
</core_workflow>

## Available Flags

### Analysis & Optimization
- **--analyze**: Multi-perspective root cause analysis
- **--performance**: Measure and optimize bottlenecks
- **--refactor**: Safe code structure improvements
- **--strict**: Zero-error execution with transparency
- **--lean**: Eliminate waste with minimal implementation

### Discovery & Documentation
- **--discover**: Research existing solutions first
- **--explain**: Progressive disclosure from overview to details
- **--save**: Create handoff documents for continuity
- **--load**: Restore context from handoff documents

### Workflow Management
- **--parallel**: Execute independent tasks simultaneously
- **--todo**: Track progress with structured task management
- **--seq**: Sequential step-by-step problem solving
- **--collab**: Co-develop with quantitative validation

### Output Control
- **--concise**: Professional, culturally neutral content
- **--git**: Anonymous, ASCII-only commit messages
- **--readonly**: Analysis without file modifications

### Meta Control
- **--reset**: Clear session and force fresh directives
- **--auto**: Grant autonomous flag selection authority

## Flag Selection Strategy
<flag_selection_strategy>
When --auto is used:
1. Analyze user intent and task requirements
2. Select complementary flags that work together
3. Avoid conflicting flags (e.g., --readonly with --git)
4. Prioritize based on task type:
   - Bugs: --analyze, --strict, --todo
   - Performance: --performance, --lean
   - Features: --discover, --parallel, --todo
   - Documentation: --explain, --save, --concise
</flag_selection_strategy>

## Examples
\`\`\`
"Fix this bug --analyze --strict"
"Optimize the code --performance --lean"
"Refactor safely --refactor --git"
"Research alternatives --discover --parallel"
"Track complex task --todo --seq"
\`\`\`
`;
}

function getPythonHookContent(): string {
  return `#!/usr/bin/env python3
"""SuperFlag Claude Code Hook - TypeScript Edition Bridge"""

import sys
import json
import re

def main():
    try:
        user_input = sys.stdin.read()

        # Detect flags in user input
        flags = re.findall(r'--\\w+', user_input)

        if flags:
            # Output hook message for Claude Code
            message = {
                "type": "system",
                "message": f"Flags detected: {', '.join(flags)}\\n" +
                          "Execute: get_directives(" + str(flags) + ") for systematic implementation."
            }
            print(json.dumps(message))
            return 0

    except Exception:
        pass

    return 1

if __name__ == "__main__":
    sys.exit(main())
`;
}

// =====================================================
// MCP Auto-Registration Functions
// =====================================================

async function registerMcpServer(platform: Platform): Promise<InstallationTask> {
  try {
    switch (platform.name) {
      case "Claude Code":
        return await registerClaudeCodeMcp();
      case "Gemini CLI":
        return await registerGeminiMcp();
      case "Continue":
        return await registerContinueMcp();
      default:
        return {
          name: `${platform.name} MCP`,
          status: "SKIP",
          detail: "Not supported"
        };
    }
  } catch (error) {
    return {
      name: `${platform.name} MCP`,
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

async function unregisterMcpServer(platform: Platform): Promise<InstallationTask> {
  try {
    switch (platform.name) {
      case "Claude Code":
        return await unregisterClaudeCodeMcp();
      case "Gemini CLI":
        return await unregisterGeminiMcp();
      case "Continue":
        return await unregisterContinueMcp();
      default:
        return {
          name: `${platform.name} MCP`,
          status: "SKIP",
          detail: "Not supported"
        };
    }
  } catch (error) {
    return {
      name: `${platform.name} MCP`,
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

// Claude Code MCP Registration
async function registerClaudeCodeMcp(): Promise<InstallationTask> {
  const configPath = path.join(os.homedir(), ".claude.json");

  try {
    let config: any = {};

    // Read existing config
    try {
      const content = await fs.readFile(configPath, "utf-8");
      config = JSON.parse(content);
    } catch {
      // File doesn't exist, create new config
      config = {};
    }

    // Ensure mcpServers section exists
    if (!config.mcpServers) {
      config.mcpServers = {};
    }

    // Add SuperFlag MCP server
    config.mcpServers.superflag = {
      type: "stdio",
      command: "npx",
      args: ["@superclaude-org/superflag@latest"],
      env: {
        SUPERFLAG_PROFILES: "claude"
      }
    };

    // Write back to file
    await fs.writeFile(configPath, JSON.stringify(config, null, 2) + "\n");

    return {
      name: "Claude Code MCP",
      status: "OK",
      detail: "Registered"
    };
  } catch (error) {
    return {
      name: "Claude Code MCP",
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

async function unregisterClaudeCodeMcp(): Promise<InstallationTask> {
  const configPath = path.join(os.homedir(), ".claude.json");

  try {
    const content = await fs.readFile(configPath, "utf-8");
    const config = JSON.parse(content);

    if (config.mcpServers && config.mcpServers.superflag) {
      delete config.mcpServers.superflag;
      await fs.writeFile(configPath, JSON.stringify(config, null, 2) + "\n");

      return {
        name: "Claude Code MCP",
        status: "OK",
        detail: "Unregistered"
      };
    }

    return {
      name: "Claude Code MCP",
      status: "SKIP",
      detail: "Not found"
    };
  } catch {
    return {
      name: "Claude Code MCP",
      status: "SKIP",
      detail: "Config not found"
    };
  }
}

// Gemini CLI MCP Registration
async function registerGeminiMcp(): Promise<InstallationTask> {
  const configPath = path.join(os.homedir(), ".gemini", "settings.json");

  try {
    // Ensure directory exists
    await fs.mkdir(path.dirname(configPath), { recursive: true });

    let config: any = {};

    // Read existing config
    try {
      const content = await fs.readFile(configPath, "utf-8");
      config = JSON.parse(content);
    } catch {
      // File doesn't exist, create new config
      config = {};
    }

    // Ensure mcpServers section exists
    if (!config.mcpServers) {
      config.mcpServers = {};
    }

    // Add SuperFlag MCP server
    config.mcpServers.superflag = {
      type: "stdio",
      command: "npx",
      args: ["@superclaude-org/superflag@latest"],
      env: {
        SUPERFLAG_PROFILES: "gemini"
      }
    };

    // Write back to file
    await fs.writeFile(configPath, JSON.stringify(config, null, 2) + "\n");

    return {
      name: "Gemini CLI MCP",
      status: "OK",
      detail: "Registered"
    };
  } catch (error) {
    return {
      name: "Gemini CLI MCP",
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

async function unregisterGeminiMcp(): Promise<InstallationTask> {
  const configPath = path.join(os.homedir(), ".gemini", "settings.json");

  try {
    const content = await fs.readFile(configPath, "utf-8");
    const config = JSON.parse(content);

    if (config.mcpServers && config.mcpServers.superflag) {
      delete config.mcpServers.superflag;
      await fs.writeFile(configPath, JSON.stringify(config, null, 2) + "\n");

      return {
        name: "Gemini CLI MCP",
        status: "OK",
        detail: "Unregistered"
      };
    }

    return {
      name: "Gemini CLI MCP",
      status: "SKIP",
      detail: "Not found"
    };
  } catch {
    return {
      name: "Gemini CLI MCP",
      status: "SKIP",
      detail: "Config not found"
    };
  }
}

// Continue MCP Registration
async function registerContinueMcp(): Promise<InstallationTask> {
  const mcpDir = path.join(os.homedir(), ".continue", "mcpServers");
  const configPath = path.join(mcpDir, "superflag.yaml");

  try {
    // Ensure directory exists
    await fs.mkdir(mcpDir, { recursive: true });

    const mcpConfig = {
      name: "SuperFlag",
      command: "npx",
      args: ["@superclaude-org/superflag@latest"],
      env: {
        SUPERFLAG_PROFILES: "continue"
      }
    };

    // Write MCP server config
    await fs.writeFile(configPath, yaml.dump(mcpConfig));

    return {
      name: "Continue MCP",
      status: "OK",
      detail: "Registered"
    };
  } catch (error) {
    return {
      name: "Continue MCP",
      status: "FAIL",
      detail: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

async function unregisterContinueMcp(): Promise<InstallationTask> {
  const configPath = path.join(os.homedir(), ".continue", "mcpServers", "superflag.yaml");

  try {
    await fs.unlink(configPath);
    return {
      name: "Continue MCP",
      status: "OK",
      detail: "Unregistered"
    };
  } catch {
    return {
      name: "Continue MCP",
      status: "SKIP",
      detail: "Not found"
    };
  }
}

// Main execution (only for direct execution)
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const commandArgs = args.slice(1);

  await handleCommand(command || "", commandArgs);
}

// Run only if this is the main module (not imported)
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

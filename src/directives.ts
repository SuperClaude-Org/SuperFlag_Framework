import * as yaml from "js-yaml";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

interface FlagConfig {
  name: string;
  description: string;
  directive: string;
  verification: string;
  priority: number;
}

interface FlagsYaml {
  available_flags: FlagConfig[];
  hook_messages?: Record<string, any>;
  meta_instructions?: {
    list_available_flags?: string;
    get_directives?: string;
  };
}

interface Directive {
  task: string;
  raw: string;
}

export class DirectiveLoader {
  private cachedConfig: FlagsYaml | null = null;
  private lastLoadTime: number = 0;
  private cacheTimeout: number = 60000; // 1 minute cache

  /**
   * Load directives for specified flags from YAML file
   */
  async loadDirectives(
    flags: string[],
    yamlPath: string
  ): Promise<Record<string, Directive>> {
    // Load configuration
    const config = await this.loadYamlConfig(yamlPath);

    // Map flags to directives
    const directives: Record<string, Directive> = {};

    for (const flag of flags) {
      const flagConfig = config.available_flags.find(
        (f) => f.name === flag
      );

      if (flagConfig) {
        directives[flag] = this.formatDirective(flagConfig);
      } else {
        // Handle unknown flag
        directives[flag] = {
          task: "Unknown flag",
          raw: `<task>\nUnknown flag: ${flag}\n</task>\n\n<verify>\n☐ Flag not found in configuration\n</verify>`,
        };
      }
    }

    return directives;
  }

  /**
   * Load and cache YAML configuration
   */
  async loadYamlConfig(yamlPath: string): Promise<FlagsYaml> {
    const now = Date.now();

    // Check cache
    if (
      this.cachedConfig &&
      now - this.lastLoadTime < this.cacheTimeout
    ) {
      return this.cachedConfig;
    }

    try {
      // Check if file exists
      await fs.access(yamlPath);

      // Read and parse YAML
      const content = await fs.readFile(yamlPath, "utf-8");
      const config = yaml.load(content) as FlagsYaml;

      // Update cache
      this.cachedConfig = config;
      this.lastLoadTime = now;

      return config;
    } catch (error) {
      // If user's file doesn't exist, copy from package
      try {
        return await this.copyBundledConfig(yamlPath);
      } catch (copyError) {
        // Fatal error: No flags.yaml found
        throw new Error(`Cannot find flags.yaml. The package is corrupted or incomplete. Please reinstall.`);
      }
    }
  }

  /**
   * Format a flag config into a directive
   */
  private formatDirective(flagConfig: FlagConfig): Directive {
    const parts: string[] = [];

    // Add task section
    if (flagConfig.directive) {
      const taskLines = flagConfig.directive.split("\\n");
      parts.push("<task>");
      parts.push(taskLines[0]); // First line as main task
      parts.push("</task>");

      // Add approach if available
      if (taskLines.length > 1) {
        parts.push("");
        parts.push("<approach>");
        parts.push(...taskLines.slice(1));
        parts.push("</approach>");
      }
    }

    // Add verification section
    if (flagConfig.verification) {
      parts.push("");
      parts.push("<verify>");
      const verifyLines = flagConfig.verification
        .split("\\n")
        .map((line) => `☐ ${line}`);
      parts.push(...verifyLines);
      parts.push("</verify>");
    }

    const raw = parts.join("\n");

    return {
      task: flagConfig.directive || flagConfig.description,
      raw: raw,
    };
  }

  /**
   * Copy bundled flags.yaml to user directory
   */
  private async copyBundledConfig(yamlPath: string): Promise<FlagsYaml> {
    const packageFlagsPath = path.join(__dirname, '..', 'flags.yaml');
    const content = await fs.readFile(packageFlagsPath, 'utf-8');
    const config = yaml.load(content) as FlagsYaml;

    // Copy to user's home directory
    const dir = path.dirname(yamlPath);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(yamlPath, content, 'utf-8');

    return config;
  }

  /**
   * Clear the cache (useful for testing or forced reload)
   */
  clearCache(): void {
    this.cachedConfig = null;
    this.lastLoadTime = 0;
  }
}
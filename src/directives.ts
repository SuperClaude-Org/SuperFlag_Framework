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
  private async loadYamlConfig(yamlPath: string): Promise<FlagsYaml> {
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
      // If file doesn't exist or is invalid, create default config
      return this.createDefaultConfig(yamlPath);
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
   * Create default configuration if file doesn't exist
   */
  private async createDefaultConfig(yamlPath: string): Promise<FlagsYaml> {
    const defaultConfig: FlagsYaml = {
      available_flags: [
        {
          name: "--analyze",
          description: "Analyze through pattern, root, and validation lenses",
          directive: "Identify root causes through multi-perspective analysis.\\nPattern Recognition - discover hidden connections\\nRoot Understanding - explain from multiple angles\\nScientific Validation - test hypotheses systematically",
          verification: "Analyzed from 3+ perspectives\\nEvidence supports each claim\\nSteps are reproducible",
          priority: 1,
        },
        {
          name: "--performance",
          description: "Optimize performance through measurement and profiling",
          directive: "Measure, profile, and optimize performance bottlenecks.\\nBaseline metrics first\\nProfile before optimizing\\nMeasure impact of changes",
          verification: "Baseline metrics recorded\\nBottlenecks identified\\nImprovements measured",
          priority: 2,
        },
        {
          name: "--refactor",
          description: "Refactor code for quality and maintainability",
          directive: "Improve code structure without changing functionality.\\nSmall steps with continuous testing\\nStructure improvement, not features\\nExpress intent through naming",
          verification: "Tests still pass\\nCyclomatic complexity ≤ 10\\nMethod length ≤ 20 lines",
          priority: 3,
        },
        {
          name: "--strict",
          description: "Execute with zero errors and full transparency",
          directive: "Ensure zero-error execution with complete transparency.\\nValidate ALL assumptions\\nReport failures immediately\\nComplete solutions only",
          verification: "Zero warnings/errors\\nAll tests pass\\n100% error handling",
          priority: 1,
        },
      ],
    };

    // Ensure directory exists
    const dir = path.dirname(yamlPath);
    await fs.mkdir(dir, { recursive: true });

    // Write default config
    const yamlContent = yaml.dump(defaultConfig, {
      indent: 2,
      lineWidth: 120,
    });
    await fs.writeFile(yamlPath, yamlContent, "utf-8");

    return defaultConfig;
  }

  /**
   * Clear the cache (useful for testing or forced reload)
   */
  clearCache(): void {
    this.cachedConfig = null;
    this.lastLoadTime = 0;
  }
}
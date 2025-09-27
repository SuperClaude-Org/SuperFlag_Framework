import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { SessionManager } from "./session.js";
import { DirectiveLoader } from "./directives.js";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

// Type matches MCP SDK expectations
type DirectiveResult = {
  content: Array<{
    type: string;
    text: string;
  }>;
  isError?: boolean;
};

export class SuperFlagServer {
  private sessionManager: SessionManager;
  private directiveLoader: DirectiveLoader;
  private flagsYamlPath: string;
  private profiles: string[];

  constructor() {
    this.sessionManager = new SessionManager();
    this.directiveLoader = new DirectiveLoader();
    this.flagsYamlPath = path.join(os.homedir(), ".superflag", "superflag.yaml");
    this.profiles = this.resolveProfiles();
  }

  getTools(): Tool[] {
    return [
      {
        name: "get_directives",
        description: `Returns combined directives for selected flags.

Args:
    flags: List of flag names (e.g., ["--analyze", "--performance"])`,
        inputSchema: {
          type: "object",
          properties: {
            flags: {
              type: "array",
              items: {
                type: "string",
              },
              description: "List of flag names to get directives for",
            },
          },
          required: ["flags"],
        },
      },
    ];
  }

  async handleToolCall(
    name: string,
    args: unknown
  ): Promise<DirectiveResult> {
    if (name === "get_directives") {
      return this.getDirectives(args);
    }

    return {
      content: [
        {
          type: "text",
          text: `Unknown tool: ${name}`,
        },
      ],
      isError: true,
    };
  }

  private async getDirectives(args: unknown): Promise<DirectiveResult> {
    try {
      // Validate input
      const input = args as Record<string, unknown>;
      if (!Array.isArray(input.flags)) {
        throw new Error("flags must be an array");
      }

      let flags = input.flags as string[];

      // Check for --auto flag special handling
      if (flags.includes("--auto")) {
        // --auto is a META flag that should guide flag selection
        // For now, return guidance message
        const otherFlags = flags.filter(f => f !== "--auto");
        if (otherFlags.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: "META FLAG: Skip get_directives(['--auto']). Instead, use <available_flags> and <flag_selection_strategy> from SUPERFLAG.md.\nExecute get_directives([your_selected_flags]) with contextually chosen flags only.",
              },
            ],
          };
        }
        // If --auto with other flags, just process the other flags
        flags = otherFlags;
      }

      // Check for --reset flag
      const resetRequested = flags.includes("--reset");
      if (resetRequested) {
        this.sessionManager.resetCurrentSession();
        // Remove --reset from processing
        flags = flags.filter(f => f !== "--reset");

        if (flags.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: "Session reset successfully. Ready for new flags.",
              },
            ],
          };
        }
        // Continue processing other flags after reset
      }

      // Check for duplicates
      const duplicateInfo = this.sessionManager.checkDuplicateFlags(flags);

      // Process flags and build response
      return this.processFlags(flags, duplicateInfo, resetRequested);
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  private async processFlags(
    flags: string[],
    duplicateInfo: ReturnType<SessionManager['checkDuplicateFlags']>,
    resetRequested: boolean
  ): Promise<DirectiveResult> {
    // Load directives
    const directives = await this.directiveLoader.loadDirectives(flags, this.flagsYamlPath, {
      profiles: this.profiles,
    });

    // Load YAML configuration for enforcement text
    const config = await this.directiveLoader.loadYamlConfig(this.flagsYamlPath, {
      profiles: this.profiles,
    });

    // Categorize flags
    const newFlags: string[] = [];
    const duplicateFlags: string[] = [];
    const validFlags: string[] = [];
    const notFoundFlags: string[] = [];

    for (const flag of flags) {
      if (directives[flag] && directives[flag].brief !== "Unknown flag") {
        validFlags.push(flag);
        if (duplicateInfo && duplicateInfo.detected.includes(flag)) {
          duplicateFlags.push(flag);
        } else {
          newFlags.push(flag);
        }
      } else {
        notFoundFlags.push(flag);
      }
    }

    // Handle unknown flags
    if (notFoundFlags.length > 0) {
      const flagText = notFoundFlags.length === 1 ? "flag" : "flags";
      const availableFlags = Object.keys(directives)
        .filter(flag => directives[flag] && directives[flag].brief !== "Unknown flag")
        .join(", ");
      return {
        content: [
          {
            type: "text",
            text: `Unknown ${flagText}: ${notFoundFlags}\n\nAvailable flags: ${availableFlags}\n\nReference <available_flags> section in <system-reminder>'s SUPERFLAG.md`,
          },
        ],
      };
    }

    // Build response parts
    const resultParts: string[] = [];

    // Handle duplicates
    if (duplicateFlags.length > 0 && !resetRequested) {
      // Return duplicate hint with guidance (not an error)
      const flagText = duplicateFlags.length === 1 ? "Flag" : "Flags";
      resultParts.push(`${flagText} ${duplicateFlags.join(", ")} already active in current session.`);
      resultParts.push("\nDirectives already in <system-reminder>.");
      resultParts.push("IF duplicate AND directives NOT in <system-reminder>: IMMEDIATE get_directives(['--reset', ...flags])");
      resultParts.push(""); // Empty line
    } else if (resetRequested && (duplicateFlags.length > 0 || newFlags.length > 0)) {
      // Reset confirmation
      resultParts.push("Session cache cleared.");
      resultParts.push("");
    }

    // Announce new flags
    if (newFlags.length > 0) {
      const newList = newFlags.map((flag) => {
        const directive = directives[flag];
        if (directive && directive.brief !== "Unknown flag") {
          // Use brief field, taking first 3 words like Python version
          const keywords = directive.brief.split(/\s+/).slice(0, 3).join(" ");
          return `'${flag}' (${keywords})`;
        }
        return `'${flag}'`;
      });
      resultParts.push(`New: ${newList.join(", ")}`);
      resultParts.push("");
    }

    // Add directives only for new flags (or all if reset)
    const flagsToShow = resetRequested ? validFlags : newFlags;
    if (flagsToShow.length > 0) {
      const directiveText = flagsToShow
        .map((flag) => {
          const directive = directives[flag];
          if (directive) {
            return `## ${flag}\n${directive.raw}`;
          }
          return "";
        })
        .filter(text => text !== "")
        .join('\n\n');

      resultParts.push(directiveText);
    }

    // Add enforcement text if we have directives
    if ((newFlags.length > 0 || (resetRequested && validFlags.length > 0)) && config.meta_instructions?.get_directives) {
      resultParts.push("=".repeat(50));
      resultParts.push(config.meta_instructions.get_directives.trim());
      resultParts.push("=".repeat(50));
    }

    // Update session only with new flags
    if (!duplicateFlags.length || resetRequested) {
      this.sessionManager.updateFlags(validFlags);
    }

    // Add applied flags at the end
    if (validFlags.length > 0) {
      resultParts.push("");
      const appliedText = validFlags.length === 1 ? "Applied flag" : "Applied flags";
      resultParts.push(`${appliedText}: ${validFlags.join(", ")}`);
    }

    return {
      content: [
        {
          type: "text",
          text: resultParts.join("\n"),
        },
      ],
    };
  }

  private resolveProfiles(): string[] {
    const envProfiles =
      process.env.SUPERFLAG_PROFILES ??
      process.env.SUPERFLAG_PROFILE ??
      process.env.SUPERFLAG_PLATFORM ?? "";

    const profiles = envProfiles
      .split(/[,\s]+/)
      .map(profile => profile.trim())
      .filter(profile => profile.length > 0);

    if (profiles.length === 0) {
      return ["superflag"];
    }

    const seen = new Set<string>();
    const result: string[] = [];
    for (const profile of profiles) {
      const normalized = profile.replace(/\.ya?ml$/i, "");
      if (!normalized || seen.has(normalized)) {
        continue;
      }
      seen.add(normalized);
      result.push(normalized);
    }

    return result;
  }
}

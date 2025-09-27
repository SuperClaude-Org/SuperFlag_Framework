import * as yaml from "js-yaml";
import * as fs from "fs/promises";
import * as path from "path";
import type { Stats } from "fs";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface FlagConfig {
  brief: string;
  directive: string;
  verification?: string;
  aliases?: string[];
  variations?: string[];
}

interface FlagsYaml {
  server?: Record<string, unknown>;
  mcp?: Record<string, unknown>;
  directives?: Record<string, FlagConfig | null>;
  hook_messages?: Record<string, any>;
  meta_instructions?: {
    list_available_flags?: string;
    get_directives?: string;
  };
  [key: string]: unknown;
}

interface Directive {
  brief: string;
  raw: string;
}

interface LoadOptions {
  profiles?: string[];
}

export class DirectiveLoader {
  /**
   * Load directives for specified flags from YAML file
   */
  async loadDirectives(
    flags: string[],
    yamlPath: string,
    options: LoadOptions = {}
  ): Promise<Record<string, Directive>> {
    const config = await this.loadYamlConfig(yamlPath, options);

    const directives: Record<string, Directive> = {};
    for (const flag of flags) {
      const flagConfig = config.directives?.[flag];

      if (flagConfig) {
        directives[flag] = this.formatDirective(flagConfig);
      } else {
        directives[flag] = {
          brief: "Unknown flag",
          raw: `<task>\nUnknown flag: ${flag}\n</task>\n\n<verify>\n☐ Flag not found in configuration\n</verify>`,
        };
      }
    }

    return directives;
  }

  /**
   * Load YAML configuration from disk using profile includes
   */
  async loadYamlConfig(yamlPath: string, options: LoadOptions = {}): Promise<FlagsYaml> {
    const profilesDir = path.dirname(yamlPath);
    const profiles = this.resolveProfiles(options, yamlPath);
    
    try {
      const config = await this.buildConfigFromProfiles(profilesDir, profiles);
      this.normalizeDirectives(config);
      return config;
    } catch (error) {
      if (!this.isMissingConfigError(error)) {
        throw error;
      }

      await this.copyBundledStructure(profilesDir);
      const config = await this.buildConfigFromProfiles(profilesDir, profiles);
      this.normalizeDirectives(config);
      return config;
    }
  }

  private formatDirective(flagConfig: FlagConfig): Directive {
    return {
      brief: flagConfig.brief,
      raw: flagConfig.directive,
    };
  }
  private mergeConfig(target: FlagsYaml, overlay: Partial<FlagsYaml>): void {
    if (overlay.server) {
      target.server = {
        ...(target.server ?? {}),
        ...overlay.server,
      };
    }

    if (overlay.mcp) {
      target.mcp = {
        ...(target.mcp ?? {}),
        ...overlay.mcp,
      };
    }

    if (overlay.meta_instructions) {
      target.meta_instructions = {
        ...(target.meta_instructions ?? {}),
        ...overlay.meta_instructions,
      };
    }

    if (overlay.hook_messages) {
      target.hook_messages = {
        ...(target.hook_messages ?? {}),
        ...overlay.hook_messages,
      };
    }

    if (overlay.directives) {
      target.directives = {
        ...(target.directives ?? {}),
      };

      for (const [rawKey, directive] of Object.entries(overlay.directives)) {
        const keys = this.parseDirectiveKeys(rawKey, directive ?? undefined);

        if (directive === null) {
          for (const key of keys) {
            delete target.directives[key];
          }
          continue;
        }

        if (!directive) {
          continue;
        }

        const cleaned = this.cleanDirectiveConfig(directive);
        for (const key of keys) {
          target.directives[key] = this.cloneDirectiveConfig(cleaned);
        }
      }
    }

    for (const [key, value] of Object.entries(overlay)) {
      if (["server", "mcp", "meta_instructions", "hook_messages", "directives"].includes(key)) {
        continue;
      }

      const existing = (target as Record<string, unknown>)[key];
      if (value === null) {
        delete (target as Record<string, unknown>)[key];
      } else if (existing && typeof existing === "object" && !Array.isArray(existing) && value && typeof value === "object" && !Array.isArray(value)) {
        (target as Record<string, unknown>)[key] = {
          ...(existing as Record<string, unknown>),
          ...(value as Record<string, unknown>),
        };
      } else {
        (target as Record<string, unknown>)[key] = value as unknown;
      }
    }
  }

  private async buildConfigFromProfiles(profilesDir: string, profiles: string[]): Promise<FlagsYaml> {
    if (profiles.length === 0) {
      throw new Error("No profiles specified for SuperFlag configuration");
    }

    const visited = new Set<string>();
    const config: FlagsYaml = {};

    for (const profile of profiles) {
      const profilePath = this.resolveProfilePath(profile, profilesDir);
      const profileConfig = await this.loadConfigTree(profilePath, visited);
      this.mergeConfig(config, profileConfig);
    }

    return config;
  }

  private resolveProfilePath(profile: string, profilesDir: string): string {
    const trimmed = profile.trim();
    if (!trimmed) {
      throw new Error("Empty profile name in configuration");
    }

    const fileName = /\.ya?ml$/i.test(trimmed) ? trimmed : `${trimmed}.yaml`;
    return path.resolve(profilesDir, fileName);
  }

  private async loadConfigTree(filePath: string, visited: Set<string>): Promise<FlagsYaml> {
    const resolvedPath = path.resolve(filePath);
    const canonicalPath = await fs.realpath(resolvedPath);

    if (visited.has(canonicalPath)) {
      return {};
    }
    visited.add(canonicalPath);

    const content = await fs.readFile(canonicalPath, "utf-8");
    const parsed = (yaml.load(content) as (FlagsYaml & { includes?: unknown })) ?? {};

    const includesRaw = Array.isArray(parsed.includes) ? parsed.includes : [];
    delete (parsed as Record<string, unknown>).includes;

    const combined: FlagsYaml = {};
    for (const includeRef of includesRaw) {
      if (typeof includeRef !== "string" || includeRef.trim().length === 0) {
        continue;
      }

      const includeTargets = await this.resolveIncludeTargets(includeRef, canonicalPath);
      for (const includePath of includeTargets) {
        const includeConfig = await this.loadConfigTree(includePath, visited);
        this.mergeConfig(combined, includeConfig);
      }
    }

    this.mergeConfig(combined, parsed);
    return combined;
  }

  private async resolveIncludeTargets(includeRef: string, fromPath: string): Promise<string[]> {
    const trimmed = includeRef.trim();
    if (!trimmed) {
      throw new Error(`Encountered empty include in ${fromPath}`);
    }

    const baseDir = path.dirname(fromPath);
    const resolvedBase = path.isAbsolute(trimmed) ? trimmed : path.resolve(baseDir, trimmed);

    const directStat = await this.tryStat(resolvedBase);
    if (directStat?.isDirectory()) {
      return await this.collectYamlFiles(resolvedBase);
    }
    if (directStat?.isFile()) {
      return [resolvedBase];
    }

    if (!this.hasYamlExtension(trimmed)) {
      for (const extension of [".yaml", ".yml"]) {
        const candidate = resolvedBase + extension;
        const candidateStat = await this.tryStat(candidate);
        if (candidateStat?.isDirectory()) {
          return await this.collectYamlFiles(candidate);
        }
        if (candidateStat?.isFile()) {
          return [candidate];
        }
      }
    }

    throw new Error(`Unable to resolve include '${includeRef}' referenced from ${fromPath}`);
  }

  private hasYamlExtension(value: string): boolean {
    return /\.ya?ml$/i.test(value);
  }

  private async collectYamlFiles(directory: string): Promise<string[]> {
    const files: string[] = [];
    const entries = await fs.readdir(directory, { withFileTypes: true });

    for (const entry of entries) {
      const entryPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        const subFiles = await this.collectYamlFiles(entryPath);
        files.push(...subFiles);
      } else if (entry.isFile() && this.hasYamlExtension(entry.name)) {
        files.push(entryPath);
      }
    }

    files.sort();
    return files;
  }

  private async tryStat(target: string): Promise<Stats | null> {
    try {
      return await fs.stat(target);
    } catch {
      return null;
    }
  }

  private resolveProfiles(options: LoadOptions, defaultPath: string): string[] {
    const ordered = options.profiles?.slice() ?? this.readProfilesFromEnv();
    const normalized = ordered.length > 0 ? ordered : [this.profileFromPath(defaultPath) ?? "superflag"];

    const seen = new Set<string>();
    const result: string[] = [];
    for (const entry of normalized) {
      const name = this.normalizeProfileName(entry);
      if (!name || seen.has(name)) {
        continue;
      }
      seen.add(name);
      result.push(name);
    }

    return result;
  }

  private readProfilesFromEnv(): string[] {
    const raw =
      process.env.SUPERFLAG_PROFILES ??
      process.env.SUPERFLAG_PROFILE ??
      process.env.SUPERFLAG_PLATFORM ?? "";

    return raw
      .split(/[\s,;]+/)
      .map(profile => profile.trim())
      .filter(profile => profile.length > 0);
  }

  private profileFromPath(filePath: string): string | null {
    const base = path.basename(filePath);
    if (!base) return null;
    const removed = base.replace(/\.ya?ml$/i, "");
    return removed || null;
  }

  private normalizeProfileName(profile: string): string | null {
    const trimmed = profile.trim();
    if (!trimmed) {
      return null;
    }
    return trimmed.replace(/\.ya?ml$/i, "");
  }

  private isMissingConfigError(error: unknown): boolean {
    if (!error || typeof error !== "object") {
      return false;
    }

    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return true;
    }

    const cause = (error as { cause?: unknown }).cause;
    if (cause && typeof cause === "object" && (cause as NodeJS.ErrnoException).code === "ENOENT") {
      return true;
    }

    return false;
  }

  private async copyBundledStructure(targetDir: string): Promise<void> {
    const packageRoot = path.join(__dirname, "..");
    await fs.mkdir(targetDir, { recursive: true });

    const sourceProfileDir = path.join(packageRoot, ".superflag");
    const profileFiles = [
      "superflag.yaml",
      "claude.yaml",
      "codex.yaml",
      "continue.yaml",
      "gemini.yaml",
    ];

    for (const file of profileFiles) {
      const source = path.join(sourceProfileDir, file);
      const destination = path.join(targetDir, file);
      try {
        await fs.access(destination);
      } catch {
        await fs.copyFile(source, destination);
      }
    }

    const sourceConfigs = path.join(sourceProfileDir, "configs");
    const targetConfigs = path.join(targetDir, "configs");
    await fs.mkdir(targetConfigs, { recursive: true });
    const entries = await fs.readdir(sourceConfigs, { withFileTypes: true });
    for (const entry of entries) {
      const sourcePath = path.join(sourceConfigs, entry.name);
      const targetPath = path.join(targetConfigs, entry.name);
      if (entry.isDirectory()) {
        await this.copyDirectory(sourcePath, targetPath);
      } else {
        try {
          await fs.access(targetPath);
        } catch {
          await fs.copyFile(sourcePath, targetPath);
        }
      }
    }
  }

  private async copyDirectory(source: string, destination: string): Promise<void> {
    await fs.mkdir(destination, { recursive: true });
    const entries = await fs.readdir(source, { withFileTypes: true });
    for (const entry of entries) {
      const sourcePath = path.join(source, entry.name);
      const targetPath = path.join(destination, entry.name);
      if (entry.isDirectory()) {
        await this.copyDirectory(sourcePath, targetPath);
      } else {
        try {
          await fs.access(targetPath);
        } catch {
          await fs.copyFile(sourcePath, targetPath);
        }
      }
    }
  }

  private parseDirectiveKeys(rawKey: string, directive?: FlagConfig | null): string[] {
    const keys = new Set<string>();
    const patternMatches = rawKey.match(/--[^,|\s]+/g);

    if (patternMatches) {
      for (const match of patternMatches) {
        const trimmed = match.trim();
        if (trimmed) {
          keys.add(trimmed);
        }
      }
    }

    if (keys.size === 0) {
      for (const part of rawKey.split(/[,|]/)) {
        const trimmed = part.trim();
        if (trimmed) {
          keys.add(trimmed);
        }
      }
    }

    if (directive && typeof directive === "object") {
      const aliasSources = [directive.aliases, directive.variations];
      for (const source of aliasSources) {
        if (!source) continue;
        for (const alias of source) {
          const trimmed = alias.trim();
          if (trimmed) {
            keys.add(trimmed);
          }
        }
      }
    }

    return Array.from(keys);
  }

  private cleanDirectiveConfig(directive: FlagConfig): FlagConfig {
    const { aliases, variations, ...rest } = directive;
    return { ...rest };
  }

  private cloneDirectiveConfig(directive: FlagConfig): FlagConfig {
    return JSON.parse(JSON.stringify(directive));
  }

  private normalizeDirectives(config: FlagsYaml): void {
    if (!config.directives) {
      return;
    }

    const normalized: Record<string, FlagConfig | null> = {};

    for (const [rawKey, value] of Object.entries(config.directives)) {
      const keys = this.parseDirectiveKeys(rawKey, value ?? undefined);

      if (value === null) {
        for (const key of keys) {
          normalized[key] = null;
        }
        continue;
      }

      if (!value) {
        continue;
      }

      const cleaned = this.cleanDirectiveConfig(value);
      for (const key of keys) {
        normalized[key] = this.cloneDirectiveConfig(cleaned);
      }
    }

    config.directives = normalized;
  }
}

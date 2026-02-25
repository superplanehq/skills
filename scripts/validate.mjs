#!/usr/bin/env node

import { promises as fs } from "node:fs";
import path from "node:path";
import process from "node:process";

const repoRoot = process.cwd();
const errors = [];
const warnings = [];

const skillNamePattern = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;

function addError(msg) {
  errors.push(msg);
}

function addWarning(msg) {
  warnings.push(msg);
}

async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function readJson(filePath, label) {
  let raw;
  try {
    raw = await fs.readFile(filePath, "utf8");
  } catch {
    addError(`${label} is missing: ${filePath}`);
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (e) {
    addError(`${label} contains invalid JSON (${filePath}): ${e.message}`);
    return null;
  }
}

function parseFrontmatter(content) {
  const text = content.replace(/\r\n/g, "\n");
  if (!text.startsWith("---\n")) return null;

  const end = text.indexOf("\n---\n", 4);
  if (end === -1) return null;

  const block = text.slice(4, end);
  const fields = {};
  for (const line of block.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const sep = line.indexOf(":");
    if (sep === -1) continue;
    fields[line.slice(0, sep).trim()] = line.slice(sep + 1).trim();
  }
  return fields;
}

function extractMarkdownLinks(content) {
  const links = [];
  const re = /\[([^\]]*)\]\(([^)]+)\)/g;
  let match;
  while ((match = re.exec(content)) !== null) {
    const href = match[2];
    if (!href.startsWith("http://") && !href.startsWith("https://") && !href.startsWith("#")) {
      links.push(href);
    }
  }
  return links;
}

// --- Validate skills ---

async function validateSkills() {
  const skillsDir = path.join(repoRoot, "skills");
  if (!(await pathExists(skillsDir))) {
    addError("skills/ directory not found");
    return;
  }

  const entries = await fs.readdir(skillsDir, { withFileTypes: true });
  const skillDirs = entries.filter((e) => e.isDirectory());

  if (skillDirs.length === 0) {
    addError("No skill directories found in skills/");
    return;
  }

  for (const dir of skillDirs) {
    const skillDir = path.join(skillsDir, dir.name);
    const skillMd = path.join(skillDir, "SKILL.md");

    if (!(await pathExists(skillMd))) {
      addError(`${dir.name}: missing SKILL.md`);
      continue;
    }

    const content = await fs.readFile(skillMd, "utf8");
    const fm = parseFrontmatter(content);

    if (!fm) {
      addError(`${dir.name}: SKILL.md missing YAML frontmatter (must start with ---)`);
      continue;
    }

    if (!fm.name || fm.name.length === 0) {
      addError(`${dir.name}: SKILL.md frontmatter missing "name"`);
    } else {
      if (!skillNamePattern.test(fm.name)) {
        addError(
          `${dir.name}: name "${fm.name}" must be lowercase alphanumeric with hyphens, no leading/trailing hyphens`
        );
      }
      if (fm.name !== dir.name) {
        addError(
          `${dir.name}: frontmatter name "${fm.name}" does not match directory name "${dir.name}"`
        );
      }
      if (fm.name.length > 64) {
        addError(`${dir.name}: name exceeds 64 characters`);
      }
    }

    if (!fm.description || fm.description.length === 0) {
      addError(`${dir.name}: SKILL.md frontmatter missing "description"`);
    } else if (fm.description.length > 1024) {
      addWarning(`${dir.name}: description exceeds 1024 characters (${fm.description.length})`);
    }

    const lineCount = content.split("\n").length;
    if (lineCount > 500) {
      addWarning(`${dir.name}: SKILL.md is ${lineCount} lines (recommended max 500)`);
    }

    const links = extractMarkdownLinks(content);
    for (const link of links) {
      const resolved = path.resolve(skillDir, link);
      if (!(await pathExists(resolved))) {
        addError(`${dir.name}: broken reference in SKILL.md: "${link}"`);
      }
    }
  }
}

// --- Validate .cursor-plugin manifests ---

async function validatePlugin() {
  const pluginJsonPath = path.join(repoRoot, ".cursor-plugin", "plugin.json");
  const plugin = await readJson(pluginJsonPath, "Plugin manifest");
  if (!plugin) return;

  if (typeof plugin.name !== "string" || !skillNamePattern.test(plugin.name)) {
    addError('plugin.json: "name" must be lowercase kebab-case');
  }

  if (!plugin.displayName) {
    addWarning('plugin.json: missing "displayName"');
  }

  if (!plugin.version) {
    addWarning('plugin.json: missing "version"');
  }

  if (!plugin.description) {
    addError('plugin.json: missing "description"');
  }

  if (Array.isArray(plugin.skills)) {
    for (const skillPath of plugin.skills) {
      const resolved = path.resolve(repoRoot, skillPath);
      const skillMd = path.join(resolved, "SKILL.md");
      if (!(await pathExists(skillMd))) {
        addError(`plugin.json: skill path "${skillPath}" does not contain a SKILL.md`);
      }
    }
  }

  const marketplacePath = path.join(repoRoot, ".cursor-plugin", "marketplace.json");
  if (await pathExists(marketplacePath)) {
    const marketplace = await readJson(marketplacePath, "Marketplace manifest");
    if (marketplace) {
      if (!marketplace.name) {
        addError('marketplace.json: missing "name"');
      }
      if (!marketplace.owner?.name) {
        addError('marketplace.json: missing "owner.name"');
      }
      if (Array.isArray(marketplace.plugins)) {
        for (const entry of marketplace.plugins) {
          if (!entry.name) {
            addError("marketplace.json: plugin entry missing name");
            continue;
          }
          const source = entry.source || ".";
          const pluginDir = path.resolve(repoRoot, source);
          if (!(await pathExists(pluginDir))) {
            addError(
              `marketplace.json: plugin "${entry.name}" source "${source}" directory not found`
            );
          }
        }
      }
    }
  }
}

// --- Main ---

async function main() {
  console.log("Validating SuperPlane skills repo...\n");

  await validateSkills();
  await validatePlugin();

  if (warnings.length > 0) {
    console.log("Warnings:");
    for (const w of warnings) {
      console.log(`  ⚠ ${w}`);
    }
    console.log();
  }

  if (errors.length > 0) {
    console.error("Errors:");
    for (const e of errors) {
      console.error(`  ✗ ${e}`);
    }
    console.log();
    console.error(`Validation failed with ${errors.length} error(s).`);
    process.exit(1);
  }

  console.log(`Validation passed. ${warnings.length} warning(s).`);
}

await main();

import fs from "fs";
import path from "path";

export function findRepoRoot(start = process.cwd()): string {
  let current = path.resolve(start);
  while (true) {
    if (
      fs.existsSync(path.join(current, "REAL_ONLY_START_HERE.md")) ||
      fs.existsSync(path.join(current, "pyproject.toml"))
    ) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(start);
    current = parent;
  }
}

export function resolveDataDir(): string {
  const repoRoot = findRepoRoot();
  const configured = process.env.DATA_DIR?.trim();
  if (!configured) return path.join(repoRoot, "data");
  return path.isAbsolute(configured) ? configured : path.resolve(repoRoot, configured);
}

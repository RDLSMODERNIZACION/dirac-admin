from pathlib import Path

root = Path.cwd()
front = root / "front"
if not front.exists():
    raise SystemExit("ERROR: ejecutá esto desde la raíz de dirac-admin")

cfg = front / "next.config.mjs"
cfg.write_text('''/** @type {import("next").NextConfig} */
const nextConfig = {
  basePath: "/admin",
};

export default nextConfig;
''', encoding="utf-8")

print("OK: dirac-admin configurado con basePath /admin")

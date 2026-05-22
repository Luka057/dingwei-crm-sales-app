import { createServer } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createBrotliCompress, createGzip } from "node:zlib";

const host = "0.0.0.0";
const port = 8088;
const rootDir = dirname(fileURLToPath(import.meta.url));
const homeFile = "/crm-sales-timepage-prototype.html";

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8"
};

const compressibleTypes = new Set([
  ".html",
  ".css",
  ".js",
  ".json",
  ".svg",
  ".txt"
]);

function sendError(res, statusCode, message) {
  res.writeHead(statusCode, {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": "no-store"
  });
  res.end(message);
}

function etagFor(stat) {
  return `W/"${stat.size.toString(16)}-${Math.trunc(stat.mtimeMs).toString(16)}"`;
}

function cacheControl(ext) {
  if (ext === ".html") return "public, max-age=30, stale-while-revalidate=300";
  return "public, max-age=604800, immutable";
}

function resolveFile(urlPath) {
  const pathname = decodeURIComponent((urlPath || "/").split("?")[0]);
  if (pathname === "/") {
    const homePath = resolve(join(rootDir, homeFile));
    if (existsSync(homePath) && statSync(homePath).isFile()) return homePath;
  }
  const safePath = normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  const candidate = resolve(join(rootDir, safePath));
  if (!candidate.startsWith(rootDir)) return null;
  if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  return null;
}

function pickEncoding(req, ext) {
  if (!compressibleTypes.has(ext)) return null;
  const accept = req.headers["accept-encoding"] || "";
  if (accept.includes("br")) return "br";
  if (accept.includes("gzip")) return "gzip";
  return null;
}

const server = createServer((req, res) => {
  const filePath = resolveFile(req.url);
  if (!filePath) return sendError(res, 404, "Not Found");

  const stat = statSync(filePath);
  const ext = extname(filePath).toLowerCase();
  const etag = etagFor(stat);

  if (req.headers["if-none-match"] === etag) {
    res.writeHead(304, {
      ETag: etag,
      "Cache-Control": cacheControl(ext),
      Vary: "Accept-Encoding"
    });
    return res.end();
  }

  const headers = {
    "Content-Type": mimeTypes[ext] || "application/octet-stream",
    "Cache-Control": cacheControl(ext),
    ETag: etag,
    "Last-Modified": stat.mtime.toUTCString(),
    Vary: "Accept-Encoding"
  };

  const encoding = pickEncoding(req, ext);
  let stream = createReadStream(filePath);

  if (encoding === "br") {
    headers["Content-Encoding"] = "br";
    delete headers["Content-Length"];
    stream = stream.pipe(createBrotliCompress());
  } else if (encoding === "gzip") {
    headers["Content-Encoding"] = "gzip";
    delete headers["Content-Length"];
    stream = stream.pipe(createGzip({ level: 9 }));
  } else {
    headers["Content-Length"] = stat.size;
  }

  res.writeHead(200, headers);
  if (req.method === "HEAD") return res.end();
  stream.pipe(res);
});

server.listen(port, host, () => {
  console.log(`CRM prototype server running at http://${host}:${port}`);
});

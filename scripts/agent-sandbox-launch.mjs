// Pinned srt CLI adapter: bounded exact path unions and file-backed SBPL.
// The original CLI still owns proxy setup, signals, child status and cleanup.
import childProcess from 'node:child_process';
import { syncBuiltinESMExports } from 'node:module';
import { createHash } from 'node:crypto';
import { accessSync, constants, chmodSync, readFileSync, realpathSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// Decode only the canonical quoting emitted by srt 0.0.79's quote(). No shell
// evaluation, expansion, operators or general-purpose command parsing.
export function decodeArgv(text) {
  const argv = [];
  let i = 0;
  while (i < text.length) {
    const parts = [];
    let started = false;
    while (i < text.length && text[i] !== ' ') {
      started = true;
      if (text[i] === "'") {
        const end = text.indexOf("'", i + 1);
        if (end < 0) throw new Error('unterminated srt quoted word');
        parts.push(text.slice(i + 1, end));
        i = end + 1;
      } else if (text.slice(i, i + 3) === '"\'"') {
        parts.push("'");
        i += 3;
      } else {
        const start = i;
        while (i < text.length && /[A-Za-z0-9_./:=@+,-]/.test(text[i])) i++;
        if (start === i) throw new Error('unsupported srt shell syntax');
        parts.push(text.slice(start, i));
      }
    }
    if (!started) throw new Error('noncanonical srt word separator');
    argv.push(parts.join(''));
    if (i < text.length) {
      i++;
      if (i === text.length) throw new Error('trailing srt word separator');
    }
  }
  return argv;
}

// Only sibling, top-level literal/subpath deny filters are unioned. Allows,
// rule order, operations, non-path filters and logging are never rewritten.
// Native Seatbelt has a 65535-byte literal data table as well as argv limits.
const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export function compactDenyRules(profile) {
  return profile.replace(/^\(deny (file-read\*|file-write\*|file-write-unlink file-write-create|file-write-unlink)\n([\s\S]*?)^  \(with message ("(?:\\.|[^"\\])*")\)\)/gm,
    (rule, operations, body, message) => {
      const lines = body.trimEnd().split('\n');
      if (lines.length < 128) return rule;
      const groups = new Map();
      lines.forEach((line, index) => {
        const match = /^  \((subpath|literal) ("(?:\\.|[^"\\])*")\)$/.exec(line);
        if (!match) return;
        const value = JSON.parse(match[2]);
        if (!path.posix.isAbsolute(value) || value === '/' || value.endsWith('/')) return;
        const dir = path.posix.dirname(value);
        const key = JSON.stringify([match[1], dir]);
        if (!groups.has(key)) groups.set(key, {kind: match[1], dir, entries: []});
        groups.get(key).entries.push({index, name: path.posix.basename(value)});
      });
      const replacements = new Map(), removed = new Set();
      for (const {kind, dir, entries} of groups.values()) {
        if (entries.length < 4) continue;
        const prefix = '^' + escapeRegex(dir === '/' ? '/' : dir + '/') + '(';
        // Include newlines in descendant names, just as subpath does.
        const tail = kind === 'subpath' ? ')(/(.|\n)*)?$' : ')$';
        let chunk = [];
        const flush = () => {
          if (chunk.length < 4) { chunk = []; return; }
          const regex = prefix + chunk.map(e => escapeRegex(e.name)).join('|') + tail;
          replacements.set(chunk[0].index, '  (regex ' + JSON.stringify(regex) + ')');
          chunk.slice(1).forEach(e => removed.add(e.index));
          chunk = [];
        };
        for (const entry of entries) {
          const candidate = prefix + [...chunk, entry].map(e => escapeRegex(e.name)).join('|') + tail;
          // Same conservative 900-byte SBPL string bound used by pinned srt.
          if (Buffer.byteLength(JSON.stringify(candidate)) - 2 > 900) {
            flush();
            if (Buffer.byteLength(JSON.stringify(prefix + escapeRegex(entry.name) + tail)) - 2 > 900) continue;
          }
          chunk.push(entry);
        }
        flush();
      }
      const compacted = lines.flatMap((line, i) => removed.has(i) ? [] : [replacements.get(i) ?? line]);
      return `(deny ${operations}\n${compacted.join('\n')}\n  (with message ${message}))`;
    });
}

export function fileBackedArgv(command, profilePath, expectedCommand, quote) {
  const argv = decodeArgv(command);
  if (quote(argv) !== command) throw new Error('srt command quoting changed');
  const index = argv.indexOf('/usr/bin/sandbox-exec');
  if (argv[0] !== 'env' || index < 1 || argv.lastIndexOf('/usr/bin/sandbox-exec') !== index ||
      argv.length !== index + 6 || argv[index + 1] !== '-p' ||
      !argv[index + 2].startsWith('(version 1)') || !path.isAbsolute(argv[index + 3]) ||
      argv[index + 4] !== '-c' || argv[index + 5] !== expectedCommand) {
    throw new Error('unsupported srt macOS launch layout; refusing to start runner');
  }
  // Accept only env's -u NAME / NAME=value prefix, never another command.
  for (let i = 1; i < index; i++) {
    if (argv[i] === '-u') {
      if (++i >= index || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(argv[i])) {
        throw new Error('unsupported srt env removal');
      }
    } else if (!/^[A-Za-z_][A-Za-z0-9_]*=/.test(argv[i])) {
      throw new Error('unsupported srt env prefix');
    }
  }
  // Exclusive creation in fresh private state; the policy denies direct-path
  // writes/moves. Hard-link aliases can alter retained files after load, so
  // report hashes of the exact pre-spawn bytes to the caller's stderr capture.
  const original = argv[index + 2];
  const profile = compactDenyRules(original);
  if (profile !== original) {
    const source = path.join(path.dirname(profilePath), 'seatbelt.source.sb');
    writeFileSync(source, original, { flag: 'wx', mode: 0o400 });
  }
  writeFileSync(profilePath, profile, { flag: 'wx', mode: 0o600 });
  chmodSync(profilePath, 0o400);
  argv.splice(index + 1, 2, '-f', profilePath);
  const sha256 = value => createHash('sha256').update(value).digest('hex');
  return { argv, profileBytes: Buffer.byteLength(profile), sourceBytes: Buffer.byteLength(original),
           profileSha256: sha256(profile), sourceSha256: sha256(original) };
}

export function validateRuntime(srt) {
  try {
    const cli = realpathSync(srt);
    const packageRoot = path.dirname(path.dirname(cli));
    const pkg = JSON.parse(readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));
    if (pkg.name !== '@anthropic-ai/sandbox-runtime' || pkg.version !== '0.0.79' ||
        path.resolve(packageRoot, pkg.bin?.srt ?? '') !== cli) throw new Error('package/layout mismatch');
    for (const file of [cli, path.join(packageRoot, 'dist/utils/shell-quote.js'),
                       path.join(packageRoot, 'dist/sandbox/macos-sandbox-utils.js')]) {
      if (!statSync(file).isFile()) throw new Error(`required module is not a file: ${file}`);
      accessSync(file, constants.R_OK);
    }
    return { cli, packageRoot };
  } catch (error) {
    throw new Error(`srt 0.0.79 Node package CLI and required modules must be readable; reinstall with install-agent-sandbox.sh (${error.message})`);
  }
}

async function main() {
  if (process.platform !== 'darwin') throw new Error('file-backed Seatbelt requires macOS');
  if (process.argv[2] === '--validate' && process.argv.length === 4) {
    validateRuntime(process.argv[3]);
    return;
  }
  const [srt, profilePath, ...cliArgs] = process.argv.slice(2);
  if (!srt || !profilePath || !path.isAbsolute(profilePath) ||
      cliArgs[0] !== '--settings' || cliArgs[2] !== '--' || cliArgs.length < 4) {
    throw new Error('invalid internal srt launch');
  }
  const { cli, packageRoot } = validateRuntime(srt);
  const { quote } = await import(pathToFileURL(path.join(packageRoot, 'dist/utils/shell-quote.js')).href);
  const expectedCommand = quote(cliArgs.slice(3));
  const originalSpawn = childProcess.spawn;
  let launched = false;
  childProcess.spawn = function (command, args, options) {
    const opts = Array.isArray(args) ? options : args;
    if (opts?.shell) {
      if (opts.shell !== true || Array.isArray(args) || launched || typeof command !== 'string') {
        throw new Error('unsupported srt spawn layout; refusing shell fallback');
      }
      const result = fileBackedArgv(command, profilePath, expectedCommand, quote);
      launched = true;
      console.error(`agent-sandbox: seatbelt_profile=${profilePath} bytes=${result.profileBytes} source_bytes=${result.sourceBytes} profile_sha256=${result.profileSha256} source_sha256=${result.sourceSha256} file-backed`);
      return originalSpawn.call(this, result.argv[0], result.argv.slice(1), { ...opts, shell: false });
    }
    return originalSpawn.apply(this, arguments);
  };
  // Update the CLI's ESM named spawn import. Non-shell helper spawns pass
  // through unchanged; all shell spawns must match the pinned sandbox layout.
  syncBuiltinESMExports();
  process.argv = [process.execPath, cli, ...cliArgs];
  await import(pathToFileURL(cli).href);
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch(error => {
    console.error(`agent-sandbox-launch: ${error.message}`);
    process.exitCode = 1;
  });
}

#!/usr/bin/env node
"use strict";

// Start the hook script with the first Python 3 interpreter this machine has.
// The hook config calls `node run-python.cjs anger_hook.py`, so a Windows host
// that has `py -3` and never `python3` still runs the same hook.

const { spawnSync } = require("node:child_process");
const path = require("node:path");

function interpreterCandidates(platform = process.platform) {
	if (platform === "win32") {
		return [
			{ command: "py", prefixArgs: ["-3"] },
			{ command: "python", prefixArgs: [] },
			{ command: "python3", prefixArgs: [] },
		];
	}
	return [
		{ command: "python3", prefixArgs: [] },
		{ command: "python", prefixArgs: [] },
	];
}

function findPython(platform = process.platform, env = process.env) {
	for (const candidate of interpreterCandidates(platform)) {
		const probe = spawnSync(
			candidate.command,
			[
				...candidate.prefixArgs,
				"-c",
				"import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)",
			],
			{ env, stdio: "ignore", windowsHide: true },
		);
		if (probe.status === 0) return candidate;
	}
	return null;
}

function main(argv = process.argv.slice(2)) {
	if (argv.length === 0) {
		console.error("anger-think-alert: supply the path of a Python script.");
		return 2;
	}
	const script = path.resolve(argv[0]);
	const python = findPython();
	if (!python) {
		console.error(
			"anger-think-alert: no Python 3 interpreter found. Install Python 3 or add it to PATH.",
		);
		return 1;
	}
	const result = spawnSync(
		python.command,
		[...python.prefixArgs, script, ...argv.slice(1)],
		{ stdio: "inherit", windowsHide: true },
	);
	if (result.error) {
		console.error(`anger-think-alert: Python 3 did not start: ${result.error.message}`);
		return 1;
	}
	return result.status ?? 1;
}

if (require.main === module) process.exitCode = main();

module.exports = { findPython, interpreterCandidates, main };

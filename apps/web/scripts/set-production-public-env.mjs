#!/usr/bin/env node
/**
 * Overwrite NEXT_PUBLIC_* production/preview env vars as plain (non-sensitive).
 * Uses Vercel REST API with VERCEL_TOKEN or ~/.config / Application Support auth.json.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const TEAM = "team_cYevEwNcrS8xfqCRzHAijnAD";
const PROJECT = "prj_GSav7JjemjncZug6mVa25QJGDx3Y";

const DESIRED = {
  NEXT_PUBLIC_API_BASE_URL: "https://api.dxcon.com.vn",
  NEXT_PUBLIC_PUBLIC_SITE_URL: "https://dxcon.com.vn",
  NEXT_PUBLIC_APP_URL: "https://dxcon.com.vn",
  NEXT_PUBLIC_APP_ENV: "production",
  NEXT_PUBLIC_DEMO_MODE: "false",
};

function loadToken() {
  if (process.env.VERCEL_TOKEN?.trim()) return process.env.VERCEL_TOKEN.trim();
  const candidates = [
    join(homedir(), "Library/Application Support/com.vercel.cli/auth.json"),
    join(homedir(), ".local/share/com.vercel.cli/auth.json"),
  ];
  for (const path of candidates) {
    try {
      const auth = JSON.parse(readFileSync(path, "utf8"));
      if (auth.token) return auth.token;
    } catch {
      /* continue */
    }
  }
  throw new Error("No Vercel token found (set VERCEL_TOKEN or login via vercel CLI)");
}

async function api(token, method, url, body) {
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json = {};
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  return { status: res.status, json };
}

async function main() {
  const token = loadToken();
  const listUrl = `https://api.vercel.com/v9/projects/${PROJECT}/env?teamId=${TEAM}`;
  const { status: listStatus, json: listing } = await api(token, "GET", listUrl);
  if (listStatus >= 400) {
    throw new Error(`List env failed: ${listStatus} ${JSON.stringify(listing)}`);
  }

  const byKey = new Map();
  for (const env of listing.envs || []) {
    if (!byKey.has(env.key)) byKey.set(env.key, []);
    byKey.get(env.key).push(env);
  }

  for (const [key, value] of Object.entries(DESIRED)) {
    for (const existing of byKey.get(key) || []) {
      const del = await api(
        token,
        "DELETE",
        `https://api.vercel.com/v9/projects/${PROJECT}/env/${existing.id}?teamId=${TEAM}`,
      );
      console.log(`delete ${key} -> ${del.status}`);
    }
    const created = await api(
      token,
      "POST",
      `https://api.vercel.com/v10/projects/${PROJECT}/env?teamId=${TEAM}`,
      {
        key,
        value,
        type: "plain",
        target: ["production", "preview"],
      },
    );
    console.log(
      `create ${key} -> ${created.status} type=${created.json.type} target=${JSON.stringify(created.json.target)}`,
    );
  }

  const verify = await api(
    token,
    "GET",
    `https://api.vercel.com/v9/projects/${PROJECT}/env?teamId=${TEAM}&decrypt=true`,
  );
  if (verify.status >= 400) {
    throw new Error(`Verify failed: ${verify.status}`);
  }
  console.log("==== VERIFY NEXT_PUBLIC (only) ====");
  for (const env of verify.json.envs || []) {
    if (!env.key?.startsWith("NEXT_PUBLIC_")) continue;
    console.log(`${env.key}=${env.value} type=${env.type} target=${JSON.stringify(env.target)}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

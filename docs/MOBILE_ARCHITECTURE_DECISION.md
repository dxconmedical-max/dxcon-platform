# Mobile Architecture Decision — Release 9.0

## Decision

**Continue Flutter** (`apps/mobile`) as the single DxCon mobile platform.

## Rationale

1. Patient and Collector MVP code already exists in Flutter.  
2. Shared Dio client, secure token storage, Riverpod, go_router already wired.  
3. Adding React Native/Expo would duplicate auth, offline, and camera work with no clear benefit.  
4. Multi-role single app matches current `features/*` layout (Patient → Collector → Lab → Admin sequence can be progressive feature flags / flavors).

## Alternatives rejected

| Option | Why rejected |
|---|---|
| New React Native app | Duplicate stack; existing Flutter investment wasted |
| Separate per-role RN apps | Higher maintenance; splits auth/API |
| Rewrite in Expo | Same as RN |

## Constraints

- No unsafe medical AI features in-app  
- No incorrect certificate pinning (document only until security sign-off)  
- No hardcoded API URLs or credentials — `--dart-define` / env files gitignored  
- Staging builds must point at `https://api-staging.dxcon.com.vn`

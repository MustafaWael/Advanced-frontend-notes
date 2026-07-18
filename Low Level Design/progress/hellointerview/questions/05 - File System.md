# File System — LLD Problem Breakdown

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/file-system
**Difficulty:** Medium

> **Premium-locked note:** This breakdown is only partially free. The freely visible content covers **Understanding the Problem and Requirements (clarifying questions + final requirements)**, plus the section outline. The following sections are behind the Hello Interview Premium paywall and are NOT captured here (only their headings are visible): Core Entities and Relationships (body), Class Design (FileSystem, File, Folder, Shared Abstraction: FileSystemEntry, Final Class Design), Implementation (FileSystem, Path Resolution Helpers, FileSystemEntry, Folder, File, Complete Code Implementation, Verification), Extensibility answers, and the level-expectation write-ups (Junior / Mid-level / Senior).

## Understanding the Problem

An **in-memory file system** is a normal file system (folders, files, navigation, create/move/rename) minus the disk. Everything lives in RAM, so the design focuses purely on **data structures and operations** — no persistence, caching, or I/O performance concerns.

Initial prompt:

> "Design an in-memory file system that supports creating files and directories, navigating paths, and basic file operations."

Warning from the article: file systems are familiar territory, which makes this **deceptively tricky** — candidates skip clarification because they "know" file systems, but the interviewer has specific scope expectations that may not match your mental model.

## Requirements (~5 minutes)

Structure questions around: what the system does, what the structure looks like, and what's explicitly out of scope.

### Clarifying Questions (key takeaways)

- **Hierarchy:** Single root, Unix-style paths like `/home/user/file.txt` (not Windows drive letters). This simplifies path resolution significantly.
- **Operations:** create, delete, list contents, **move and rename**, navigate to any path and get its contents.
- **File content:** Files store actual content — simple string content is fine (not just names in a tree).
- **Error cases:** Creating a file where the parent folder doesn't exist, deleting the root, etc. should **throw exceptions — with specific exception types** so callers can handle different failure modes appropriately.
- **Scale:** Tens of thousands of entries; must stay responsive with deep folder hierarchies. This influences data structure choices (e.g., hash-map children lookups rather than linear scans).
- **Out of scope:** permissions, timestamps, symbolic links — focus on the core tree structure and operations.

### Final Requirements

```
Requirements:
1. Hierarchical file system with single root directory
2. Files store string content
3. Folders contain files and other folders
4. Create and delete files and folders
5. List contents of a folder
6. Navigate/resolve absolute paths (e.g., /home/user/docs)
7. Rename and move files and folders
8. Retrieve full path from any file/folder reference
9. Scale to tens of thousands of entries in memory

Out of Scope:
- Search functionality
- Relative path resolution (../ or ./)
- Permissions, ownership, timestamps
- File type-specific behavior
- Persistence / disk storage
- Symbolic links
- UI layer
```

"We've scoped the problem tightly. Now we know exactly what to build."

## Core Entities and Relationships (~3 minutes) — locked

Body is premium-locked. From the visible structure, the entities the breakdown lands on are:

- **FileSystem** — the facade / entry point owning the root and path resolution
- **File** — leaf node holding string content
- **Folder** — container of files and folders
- **FileSystemEntry** — the shared abstraction (base class/interface) that File and Folder both extend — the classic **Composite pattern** shape

## Class Design (10–15 minutes) — locked

Premium sections (headings only): FileSystem, File, Folder, **Shared Abstraction: FileSystemEntry**, Final Class Design.

## Implementation (~10 minutes) — locked

Premium sections (headings only): FileSystem, **The Path Resolution Helpers**, FileSystemEntry, Folder, File, Complete Code Implementation, Verification.

## Extensibility (5 minutes, if time and level allow) — locked

The follow-up questions asked (answers are premium-locked):

1. "How would you make this file system thread-safe?"
2. "How would you add search functionality?"

## What is Expected at Each Level? — locked

The breakdown includes Junior / Mid-level / Senior expectation sections; their content is premium-locked.

---

## Study notes to fill the gaps (not from the article)

Since the design sections are paywalled, here's a standard approach consistent with the free requirements above and the visible section headings:

- **Composite pattern:** abstract `FileSystemEntry { name, parent: Folder, getPath() }`; `File extends FileSystemEntry { content: String }`; `Folder extends FileSystemEntry { children: Map<String, FileSystemEntry> }`. A `Map` for children gives O(1) lookup per path segment — important at tens of thousands of entries.
- **FileSystem facade:** `createFile(path, content)`, `createFolder(path)`, `delete(path)`, `list(path)`, `move(srcPath, destPath)`, `rename(path, newName)`, `readFile(path)`.
- **Path resolution helper:** split absolute path on `/`, walk from root through children maps; separate helpers for "resolve entry" vs. "resolve parent + last segment" (used by create/move/delete).
- **getPath():** walk `parent` pointers up to the root and join names — which is why entries keep a parent reference.
- **Specific exceptions:** e.g., `NotFoundException`, `AlreadyExistsException`, `NotAFolderException`, `CannotDeleteRootException`.
- **Thread safety follow-up:** a single global RW lock is the simple answer; per-folder locking with lock ordering (or lock coupling down the path) is the advanced one.
- **Search follow-up:** BFS/DFS over the tree for name matching; maintain an inverted index / name→entries map for scale.

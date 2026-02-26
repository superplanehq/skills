# GitHub Integration Reference

Triggers, components, payload examples, and gotchas for the GitHub integration in SuperPlane.

All payloads are wrapped in the SuperPlane envelope: `{ data: {...}, timestamp, type }`. Expression paths below include the `.data.` prefix.

## Triggers

| Trigger | Webhook Event | Type String | Key Payload Fields |
| --- | --- | --- | --- |
| `github.onPush` | `push` | `github.push` | `data.ref`, `data.commits[]`, `data.before`, `data.after`, `data.pusher`, `data.repository` |
| `github.onPullRequest` | `pull_request` | `github.pullRequest` | `data.action`, `data.pull_request`, `data.repository`, `data.sender` |
| `github.onPRComment` | `issue_comment` | `github.prComment` | `data.comment`, `data.issue`, `data.repository`, `data.sender` |
| `github.onPRReviewComment` | `pull_request_review` / `pull_request_review_comment` | `github.prReviewComment` | `data.review` or `data.comment`, `data.pull_request`, `data.repository` |
| `github.onIssue` | `issues` | `github.issue` | `data.action`, `data.issue`, `data.repository`, `data.sender` |
| `github.onIssueComment` | `issue_comment` | `github.issueComment` | `data.comment`, `data.issue`, `data.repository`, `data.sender` |
| `github.onRelease` | `release` | `github.release` | `data.action`, `data.release`, `data.repository`, `data.sender` |
| `github.onWorkflowRun` | `workflow_run` | `github.workflowRun` | `data.action`, `data.workflow_run`, `data.repository`, `data.sender` |
| `github.onBranchCreated` | `create` | `github.branchCreated` | `data.ref`, `data.ref_type`, `data.repository`, `data.sender` |
| `github.onTagCreated` | `create` | `github.tagCreated` | `data.ref`, `data.ref_type`, `data.repository`, `data.sender` |

### Trigger Configuration

All triggers require a **Repository** (integration-resource field). Additional config per trigger:

| Trigger | Config Fields |
| --- | --- |
| `github.onPush` | **Refs** — list of predicates (e.g., `equals: refs/heads/main`, `startsWith: refs/tags/`) |
| `github.onPullRequest` | **Actions** — `opened`, `closed`, `synchronize`, `reopened`, etc. |
| `github.onPRComment` | **Content Filter** — optional regex to match comment body |
| `github.onRelease` | **Actions** — `published`, `created`, `released`, etc. |
| `github.onWorkflowRun` | **Workflow Files** (optional), **Conclusions** — `success`, `failure`, `cancelled`, etc. |
| `github.onBranchCreated` | **Branches** — list of predicates |
| `github.onTagCreated` | **Tags** — list of predicates |

## Components (Actions)

| Component | Description | Output Type | Channels |
| --- | --- | --- | --- |
| `github.createIssueComment` | Post a comment on an issue or PR | `github.issueComment` | `default` |
| `github.createIssue` | Create a new issue | `github.issue` | `default` |
| `github.getIssue` | Fetch an issue by number | `github.issue` | `default` |
| `github.updateIssue` | Update an existing issue | `github.issue` | `default` |
| `github.addIssueLabel` | Add labels to an issue | `github.labels` | `default` |
| `github.removeIssueLabel` | Remove labels from an issue | `github.labels` | `default` |
| `github.addIssueAssignee` | Add assignees to an issue | `github.issue` | `default` |
| `github.removeIssueAssignee` | Remove assignees from an issue | `github.issue` | `default` |
| `github.createRelease` | Create a GitHub release | `github.release` | `default` |
| `github.getRelease` | Fetch a release | `github.release` | `default` |
| `github.updateRelease` | Update a release | `github.release` | `default` |
| `github.deleteRelease` | Delete a release | `github.release` | `default` |
| `github.createReview` | Submit a PR review | `github.pullRequestReview` | `default` |
| `github.publishCommitStatus` | Set commit status (pending/success/failure/error) | `github.commitStatus` | `default` |
| `github.runWorkflow` | Trigger a GitHub Actions workflow | `github.workflow.finished` | `passed`, `failed` |
| `github.getWorkflowUsage` | Get Actions usage stats | `github.workflowUsage` | `default` |

## Payload Examples

### `github.onPush`

```
root().data.ref                          # "refs/heads/main"
root().data.after                        # commit SHA after push
root().data.before                       # commit SHA before push
root().data.commits[0].message           # first commit message
root().data.commits[0].id               # first commit SHA
root().data.pusher.name                  # who pushed
root().data.repository.full_name         # "owner/repo"
root().data.repository.clone_url         # "https://github.com/owner/repo.git"
```

### `github.onPullRequest`

```
root().data.action                       # "opened", "closed", "synchronize", etc.
root().data.pull_request.number          # PR number
root().data.pull_request.title           # PR title
root().data.pull_request.head.ref        # source branch name
root().data.pull_request.head.sha        # head commit SHA
root().data.pull_request.base.ref        # target branch name
root().data.pull_request.html_url        # PR URL
root().data.pull_request.user.login      # PR author
root().data.repository.full_name         # "owner/repo"
```

### `github.onPRComment`

```
root().data.comment.body                 # comment text
root().data.comment.user.login           # commenter
root().data.issue.number                 # issue/PR number
root().data.issue.title                  # issue/PR title
root().data.issue.pull_request.html_url  # PR URL (this is just a URL, not the full PR object)
root().data.repository.full_name         # "owner/repo"
root().data.repository.clone_url         # "https://github.com/owner/repo.git"
root().data.sender.login                 # who triggered the event
```

### `github.onRelease`

```
root().data.action                       # "published", "created", etc.
root().data.release.tag_name             # "v1.2.3"
root().data.release.name                 # release title
root().data.release.body                 # release notes
root().data.release.html_url             # release URL
root().data.release.draft                # true/false
root().data.release.prerelease           # true/false
root().data.repository.full_name         # "owner/repo"
```

### `github.onWorkflowRun`

```
root().data.action                       # "completed", "requested"
root().data.workflow_run.conclusion      # "success", "failure", "cancelled"
root().data.workflow_run.name            # workflow name
root().data.workflow_run.head_branch     # branch that triggered the run
root().data.workflow_run.head_sha        # commit SHA
root().data.workflow_run.html_url        # run URL
root().data.repository.full_name         # "owner/repo"
```

## Gotchas

### `github.onPRComment` is NOT `github.onPullRequest`

`onPRComment` uses GitHub's `issue_comment` webhook. The payload has `data.issue`, not `data.pull_request`. The `data.issue.pull_request` sub-object only contains URLs (`url`, `html_url`, `diff_url`, `patch_url`) — it does **not** have `head.ref`, `head.sha`, or any branch information.

To get the PR branch or SHA from a PR comment event, you need to either:
- Use `data.issue.number` with the GitHub API to fetch the full PR object
- Use `data.repository.clone_url` + `data.issue.number` with `git fetch origin pull/NUMBER/head`

### `github.onPush` ref is the full ref

`data.ref` is `refs/heads/main`, not just `main`. If you need the short branch name, use an expression to strip the prefix or match against the full ref.

### `github.onPullRequest` actions matter

The trigger fires for many actions (`opened`, `closed`, `synchronize`, `reopened`, `labeled`, etc.). If you only want new PRs, configure the trigger with `actions: [opened]`. Without filtering, your canvas will run on every PR update.

### PR number is `issue.number` in comment events

In `onPRComment` and `onIssueComment`, the PR/issue number is at `data.issue.number`, not `data.pull_request.number`.

### `github.runWorkflow` has two output channels

Unlike most components that use `default`, `runWorkflow` outputs to `passed` (success) or `failed` (failure/cancelled). Wire edges accordingly.

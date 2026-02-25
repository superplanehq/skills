# Canvas Patterns

Complete real-world canvas YAML examples for common SuperPlane workflows.

Each pattern includes a description, full canvas YAML, and explanation of the edge wiring.

## Pattern 1: CI-Gated Deploy Pipeline

Push to main triggers CI. If CI passes, require human approval, then deploy.

**Graph:** `github.onPush → semaphore.runWorkflow → approval → deploy`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: CI-Gated Deploy
spec:
  nodes:
    - id: trigger-push
      name: github.onPush
      type: TYPE_TRIGGER
      trigger:
        name: github.onPush
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/myapp
        refs:
          - type: equals
            value: refs/heads/main
      position: { x: 120, y: 100 }
      paused: false
      isCollapsed: false

    - id: run-ci
      name: semaphore.runWorkflow
      type: TYPE_COMPONENT
      component:
        name: semaphore.runWorkflow
      integration:
        id: <semaphore-integration-id>
        name: ""
      configuration:
        project: myapp
        pipelineFile: .semaphore/semaphore.yml
        ref: "{{ $['github.onPush'].ref }}"
      position: { x: 600, y: 100 }
      paused: false
      isCollapsed: false

    - id: approve-deploy
      name: approval
      type: TYPE_COMPONENT
      component:
        name: approval
      configuration: {}
      position: { x: 1080, y: 100 }
      paused: false
      isCollapsed: false

    - id: deploy-prod
      name: render.deploy
      type: TYPE_COMPONENT
      component:
        name: render.deploy
      integration:
        id: <render-integration-id>
        name: ""
      configuration:
        service: <render-service-id>
      position: { x: 1560, y: 100 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-push
      targetId: run-ci
      channel: default
    - sourceId: run-ci
      targetId: approve-deploy
      channel: passed
    - sourceId: approve-deploy
      targetId: deploy-prod
      channel: approved
```

**Edge wiring:** CI connects on `passed` (not `default`) because CI components emit results on `passed`/`failed` channels. Approval connects on `approved` so rejected deploys stop the pipeline.

---

## Pattern 2: Progressive Delivery (10% → 50% → 100%)

Deploy in waves. After each wave, check health via an HTTP endpoint. If healthy, proceed to the next wave. If unhealthy, stop.

**Graph:** `trigger → deploy-10 → check-health-1 → [passed: deploy-50] / [failed: notify-rollback] → check-health-2 → [passed: deploy-100] / [failed: notify-rollback]`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: Progressive Delivery
spec:
  nodes:
    - id: trigger-deploy
      name: manual_run
      type: TYPE_TRIGGER
      trigger:
        name: manual_run
      configuration: {}
      position: { x: 120, y: 200 }
      paused: false
      isCollapsed: false

    - id: deploy-10
      name: Deploy 10%
      type: TYPE_COMPONENT
      component:
        name: http
      configuration:
        method: POST
        url: "https://deploy.example.com/api/rollout"
        headers:
          Content-Type: application/json
        body: '{"percentage": 10}'
      position: { x: 600, y: 200 }
      paused: false
      isCollapsed: false

    - id: wait-1
      name: Wait 5m
      type: TYPE_COMPONENT
      component:
        name: wait
      configuration:
        type: duration
        duration: 5m
      position: { x: 1080, y: 200 }
      paused: false
      isCollapsed: false

    - id: check-health-1
      name: Health Check 1
      type: TYPE_COMPONENT
      component:
        name: filter
      configuration:
        expression: "$['Deploy 10%'].statusCode == 200"
      position: { x: 1560, y: 200 }
      paused: false
      isCollapsed: false

    - id: deploy-50
      name: Deploy 50%
      type: TYPE_COMPONENT
      component:
        name: http
      configuration:
        method: POST
        url: "https://deploy.example.com/api/rollout"
        headers:
          Content-Type: application/json
        body: '{"percentage": 50}'
      position: { x: 2040, y: 100 }
      paused: false
      isCollapsed: false

    - id: wait-2
      name: Wait 5m Again
      type: TYPE_COMPONENT
      component:
        name: wait
      configuration:
        type: duration
        duration: 5m
      position: { x: 2520, y: 100 }
      paused: false
      isCollapsed: false

    - id: check-health-2
      name: Health Check 2
      type: TYPE_COMPONENT
      component:
        name: filter
      configuration:
        expression: "$['Deploy 50%'].statusCode == 200"
      position: { x: 3000, y: 100 }
      paused: false
      isCollapsed: false

    - id: deploy-100
      name: Deploy 100%
      type: TYPE_COMPONENT
      component:
        name: http
      configuration:
        method: POST
        url: "https://deploy.example.com/api/rollout"
        headers:
          Content-Type: application/json
        body: '{"percentage": 100}'
      position: { x: 3480, y: 100 }
      paused: false
      isCollapsed: false

    - id: notify-rollback
      name: Rollback Alert
      type: TYPE_COMPONENT
      component:
        name: slack.postMessage
      integration:
        id: <slack-integration-id>
        name: ""
      configuration:
        channel: "#deploys"
        text: "Rollout failed health check — manual rollback required."
      position: { x: 2040, y: 400 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-deploy
      targetId: deploy-10
      channel: default
    - sourceId: deploy-10
      targetId: wait-1
      channel: default
    - sourceId: wait-1
      targetId: check-health-1
      channel: default
    - sourceId: check-health-1
      targetId: deploy-50
      channel: passed
    - sourceId: check-health-1
      targetId: notify-rollback
      channel: failed
    - sourceId: deploy-50
      targetId: wait-2
      channel: default
    - sourceId: wait-2
      targetId: check-health-2
      channel: default
    - sourceId: check-health-2
      targetId: deploy-100
      channel: passed
    - sourceId: check-health-2
      targetId: notify-rollback
      channel: failed
```

**Edge wiring:** Filter nodes split on `passed`/`failed`. Both health checks route `failed` to the same rollback notification node. This creates a diamond pattern where any failure short-circuits to the alert.

---

## Pattern 3: Incident Triage ("First 5 Minutes")

When PagerDuty creates an incident, fetch context in parallel (recent deploys from GitHub + health metrics from Grafana), merge results, then post a summary to Slack.

**Graph:** `pagerduty.onIncident → [github.listDeployments + grafana.query] → merge → slack.postMessage`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: Incident Triage
spec:
  nodes:
    - id: trigger-incident
      name: pagerduty.onIncident
      type: TYPE_TRIGGER
      trigger:
        name: pagerduty.onIncident
      integration:
        id: <pagerduty-integration-id>
        name: ""
      configuration: {}
      position: { x: 120, y: 250 }
      paused: false
      isCollapsed: false

    - id: fetch-deploys
      name: Recent Deploys
      type: TYPE_COMPONENT
      component:
        name: github.listDeployments
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/myapp
      position: { x: 600, y: 100 }
      paused: false
      isCollapsed: false

    - id: fetch-health
      name: Health Metrics
      type: TYPE_COMPONENT
      component:
        name: http
      configuration:
        method: GET
        url: "https://grafana.example.com/api/ds/query?db=prometheus&query=up{job='myapp'}"
        headers:
          Authorization: "Bearer {{ secret('grafana-token') }}"
      position: { x: 600, y: 400 }
      paused: false
      isCollapsed: false

    - id: merge-context
      name: merge
      type: TYPE_COMPONENT
      component:
        name: merge
      configuration: {}
      position: { x: 1080, y: 250 }
      paused: false
      isCollapsed: false

    - id: post-summary
      name: Slack Summary
      type: TYPE_COMPONENT
      component:
        name: slack.postMessage
      integration:
        id: <slack-integration-id>
        name: ""
      configuration:
        channel: "#incidents"
        text: "Incident: {{ root().title }}\nRecent deploys: {{ $['Recent Deploys'].deployments | len }} in last 24h\nHealth: {{ $['Health Metrics'].body }}"
      position: { x: 1560, y: 250 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-incident
      targetId: fetch-deploys
      channel: default
    - sourceId: trigger-incident
      targetId: fetch-health
      channel: default
    - sourceId: fetch-deploys
      targetId: merge-context
      channel: default
    - sourceId: fetch-health
      targetId: merge-context
      channel: default
    - sourceId: merge-context
      targetId: post-summary
      channel: default
```

**Edge wiring:** The trigger fans out to two parallel nodes by having two edges from the same source. Both feed into a Merge node, which waits for all incoming edges before continuing. The Slack message references both upstream nodes by name.

---

## Pattern 4: Release Train (Multi-Repo Fan-In)

Wait for CI to pass on three different repos before triggering a coordinated deploy.

**Graph:** `[repo-a.onPush + repo-b.onPush + repo-c.onPush] → merge → deploy`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: Release Train
spec:
  nodes:
    - id: trigger-repo-a
      name: Repo A Push
      type: TYPE_TRIGGER
      trigger:
        name: github.onPush
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/service-a
        refs:
          - type: equals
            value: refs/heads/main
      position: { x: 120, y: 100 }
      paused: false
      isCollapsed: false

    - id: trigger-repo-b
      name: Repo B Push
      type: TYPE_TRIGGER
      trigger:
        name: github.onPush
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/service-b
        refs:
          - type: equals
            value: refs/heads/main
      position: { x: 120, y: 300 }
      paused: false
      isCollapsed: false

    - id: trigger-repo-c
      name: Repo C Push
      type: TYPE_TRIGGER
      trigger:
        name: github.onPush
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/service-c
        refs:
          - type: equals
            value: refs/heads/main
      position: { x: 120, y: 500 }
      paused: false
      isCollapsed: false

    - id: wait-for-all
      name: merge
      type: TYPE_COMPONENT
      component:
        name: merge
      configuration: {}
      position: { x: 600, y: 300 }
      paused: false
      isCollapsed: false

    - id: deploy-all
      name: Coordinated Deploy
      type: TYPE_COMPONENT
      component:
        name: http
      configuration:
        method: POST
        url: "https://deploy.example.com/api/release-train"
        headers:
          Content-Type: application/json
        body: '{"services": ["service-a", "service-b", "service-c"]}'
      position: { x: 1080, y: 300 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-repo-a
      targetId: wait-for-all
      channel: default
    - sourceId: trigger-repo-b
      targetId: wait-for-all
      channel: default
    - sourceId: trigger-repo-c
      targetId: wait-for-all
      channel: default
    - sourceId: wait-for-all
      targetId: deploy-all
      channel: default
```

**Edge wiring:** Three separate triggers all feed into a single Merge. The Merge waits for all three incoming edges to have an execution before it fires. This means the deploy only happens once all three repos have pushed.

---

## Pattern 5: Scheduled Maintenance Window

Run maintenance tasks only during allowed hours (weekdays 2am-5am UTC). Notify the team before and after.

**Graph:** `schedule → timegate → notify-start → maintenance-task → notify-done`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: Scheduled Maintenance
spec:
  nodes:
    - id: trigger-schedule
      name: schedule
      type: TYPE_TRIGGER
      trigger:
        name: schedule
      configuration:
        type: cron
        expression: "0 1 * * 1-5"
      position: { x: 120, y: 100 }
      paused: false
      isCollapsed: false

    - id: gate-hours
      name: timegate
      type: TYPE_COMPONENT
      component:
        name: timegate
      configuration:
        timezone: UTC
        allowedDays: [monday, tuesday, wednesday, thursday, friday]
        startHour: 2
        endHour: 5
      position: { x: 600, y: 100 }
      paused: false
      isCollapsed: false

    - id: notify-start
      name: Notify Start
      type: TYPE_COMPONENT
      component:
        name: slack.postMessage
      integration:
        id: <slack-integration-id>
        name: ""
      configuration:
        channel: "#ops"
        text: "Maintenance window starting. Automated tasks running."
      position: { x: 1080, y: 100 }
      paused: false
      isCollapsed: false

    - id: run-maintenance
      name: Run Maintenance
      type: TYPE_COMPONENT
      component:
        name: ssh
      configuration:
        host: "maintenance.example.com"
        user: "deploy"
        command: "/opt/scripts/run-maintenance.sh"
        privateKey: "{{ secret('ssh-key') }}"
      position: { x: 1560, y: 100 }
      paused: false
      isCollapsed: false

    - id: notify-done
      name: Notify Done
      type: TYPE_COMPONENT
      component:
        name: slack.postMessage
      integration:
        id: <slack-integration-id>
        name: ""
      configuration:
        channel: "#ops"
        text: "Maintenance complete."
      position: { x: 2040, y: 100 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-schedule
      targetId: gate-hours
      channel: default
    - sourceId: gate-hours
      targetId: notify-start
      channel: default
    - sourceId: notify-start
      targetId: run-maintenance
      channel: default
    - sourceId: run-maintenance
      targetId: notify-done
      channel: default
```

**Edge wiring:** All edges use `default` channel — this is a linear pipeline. The Time Gate holds execution until the allowed window opens. If the cron fires at 1am UTC, the Time Gate holds until 2am before releasing.

---

## Pattern 6: PR Review Automation

When a PR is opened, run lint and tests in parallel, merge results, then post a summary comment on the PR.

**Graph:** `github.onPullRequest → [run-lint + run-tests] → merge → post-comment`

```yaml
apiVersion: v1
kind: Canvas
metadata:
  name: PR Review Automation
spec:
  nodes:
    - id: trigger-pr
      name: github.onPullRequest
      type: TYPE_TRIGGER
      trigger:
        name: github.onPullRequest
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/myapp
        actions: [opened, synchronize]
      position: { x: 120, y: 250 }
      paused: false
      isCollapsed: false

    - id: run-lint
      name: Run Lint
      type: TYPE_COMPONENT
      component:
        name: semaphore.runWorkflow
      integration:
        id: <semaphore-integration-id>
        name: ""
      configuration:
        project: myapp
        pipelineFile: .semaphore/lint.yml
        ref: "{{ root().pull_request.head.ref }}"
      position: { x: 600, y: 100 }
      paused: false
      isCollapsed: false

    - id: run-tests
      name: Run Tests
      type: TYPE_COMPONENT
      component:
        name: semaphore.runWorkflow
      integration:
        id: <semaphore-integration-id>
        name: ""
      configuration:
        project: myapp
        pipelineFile: .semaphore/test.yml
        ref: "{{ root().pull_request.head.ref }}"
      position: { x: 600, y: 400 }
      paused: false
      isCollapsed: false

    - id: merge-results
      name: merge
      type: TYPE_COMPONENT
      component:
        name: merge
      configuration: {}
      position: { x: 1080, y: 250 }
      paused: false
      isCollapsed: false

    - id: post-comment
      name: PR Comment
      type: TYPE_COMPONENT
      component:
        name: github.createComment
      integration:
        id: <github-integration-id>
        name: ""
      configuration:
        repository: myorg/myapp
        issue_number: "{{ root().pull_request.number }}"
        body: "Lint: {{ $['Run Lint'].result }}\nTests: {{ $['Run Tests'].result }}"
      position: { x: 1560, y: 250 }
      paused: false
      isCollapsed: false

  edges:
    - sourceId: trigger-pr
      targetId: run-lint
      channel: default
    - sourceId: trigger-pr
      targetId: run-tests
      channel: default
    - sourceId: run-lint
      targetId: merge-results
      channel: default
    - sourceId: run-tests
      targetId: merge-results
      channel: default
    - sourceId: merge-results
      targetId: post-comment
      channel: default
```

**Edge wiring:** Fan-out from trigger to two parallel CI jobs, fan-in through Merge, then a single comment. The comment references both upstream nodes by name to include their results. Uses `root()` to access the original PR event payload for the PR number and branch ref.

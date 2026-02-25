# Provider Catalog

All SuperPlane integration providers organized by category. Each provider offers triggers (events that start workflows) and/or components (actions nodes can perform).

Use `superplane index triggers --from <provider>` and `superplane index components --from <provider>` for the latest list. Full docs at https://docs.superplane.com/.

## CI/CD

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| GitHub | onPush, onPullRequest, onRelease, onWorkflowRun | createComment, listDeployments, createRelease, triggerWorkflow | [docs](https://docs.superplane.com/components/github) |
| GitLab | onPush, onMergeRequest, onPipeline | triggerPipeline, createIssue | [docs](https://docs.superplane.com/components/gitlab) |
| Bitbucket | onPush, onPullRequest | triggerPipeline | [docs](https://docs.superplane.com/components/bitbucket) |
| Semaphore | onWorkflowDone, onPipelineDone | runWorkflow | [docs](https://docs.superplane.com/components/semaphore) |
| CircleCI | onPipelineComplete | triggerPipeline | [docs](https://docs.superplane.com/components/circleci) |
| Harness | onPipelineComplete | triggerPipeline | [docs](https://docs.superplane.com/components/harness) |
| Render | onDeploy, onBuild | deploy, createDeploy | [docs](https://docs.superplane.com/components/render) |

## Cloud & Infrastructure

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| AWS ECR | onImagePush | — | [docs](https://docs.superplane.com/components/aws) |
| AWS Lambda | — | runFunction | [docs](https://docs.superplane.com/components/aws) |
| AWS CodeArtifact | onPackageVersion | — | [docs](https://docs.superplane.com/components/aws) |
| AWS CloudWatch | onAlarm | — | [docs](https://docs.superplane.com/components/aws) |
| AWS SNS | onTopicMessage | — | [docs](https://docs.superplane.com/components/aws) |
| Cloudflare | — | purgeCacheByURL, updateDNSRecord | [docs](https://docs.superplane.com/components/cloudflare) |
| DigitalOcean | — | createDroplet, deleteDroplet | [docs](https://docs.superplane.com/components/digitalocean) |
| DockerHub | onImagePush | — | [docs](https://docs.superplane.com/components/dockerhub) |
| Google Cloud | — | runJob, deploy | [docs](https://docs.superplane.com/components/googlecloud) |
| Hetzner Cloud | — | createServer, deleteServer | [docs](https://docs.superplane.com/components/hetznercloud) |

## Observability

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| Datadog | — | createEvent | [docs](https://docs.superplane.com/components/datadog) |
| Dash0 | — | query | [docs](https://docs.superplane.com/components/dash0) |
| Grafana | onAlert | query | [docs](https://docs.superplane.com/components/grafana) |
| Prometheus | onAlert | — | [docs](https://docs.superplane.com/components/prometheus) |

## Incident Management

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| PagerDuty | onIncident | createIncident, resolveIncident | [docs](https://docs.superplane.com/components/pagerduty) |
| Rootly | onIncident | createIncident, updateIncident | [docs](https://docs.superplane.com/components/rootly) |
| Statuspage | — | createIncident, updateIncident | [docs](https://docs.superplane.com/components/statuspage) |
| incident.io | onIncident | createIncident | [docs](https://docs.superplane.com/components/incident) |

## Communication

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| Slack | onMessage, onReaction | postMessage, updateMessage | [docs](https://docs.superplane.com/components/slack) |
| Discord | — | sendMessage | [docs](https://docs.superplane.com/components/discord) |
| SendGrid | — | sendEmail | [docs](https://docs.superplane.com/components/sendgrid) |
| SMTP | — | sendEmail | [docs](https://docs.superplane.com/components/smtp) |
| Telegram | onMessage | sendMessage | [docs](https://docs.superplane.com/components/telegram) |

## Ticketing

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| Jira | onIssueCreated, onIssueUpdated | createIssue, updateIssue, addComment | [docs](https://docs.superplane.com/components/jira) |
| ServiceNow | onIncident | createIncident, updateIncident | [docs](https://docs.superplane.com/components/servicenow) |

## AI & LLM

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| Claude | — | generateText | [docs](https://docs.superplane.com/components/claude) |
| Cursor | — | runTask | [docs](https://docs.superplane.com/components/cursor) |
| OpenAI | — | generateText | [docs](https://docs.superplane.com/components/openai) |

## Developer Tools

| Provider | Triggers | Components | Docs |
| --- | --- | --- | --- |
| Daytona | — | createWorkspace, executeCommand | [docs](https://docs.superplane.com/components/daytona) |
| JFrog Artifactory | — | uploadArtifact, downloadArtifact | [docs](https://docs.superplane.com/components/jfrogartifactory) |

---

**Note:** Trigger and component names shown above are representative. Run `superplane index triggers --from <provider>` and `superplane index components --from <provider>` for the exact, up-to-date list on your SuperPlane instance.

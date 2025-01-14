id: python_example
namespace: company.team

inputs:
  - id: dataset_uri
    type: STRING
    displayName: Dataset URI
    defaults: https://huggingface.co/datasets/kestra/datasets/raw/main/csv/orders.csv

  - id: discount_amount
    type: FLOAT
    displayName: Discount Amount
    description: By default, it's set to 0 (no discount).
    min: 0
    max: 1
    defaults: 0

variables:
  github_repo_url: https://github.com/wrussell1999/kestra-examples
  filename: processed_orders.csv

tasks:
  - id: sync_files
    type: io.kestra.plugin.git.SyncNamespaceFiles
    url: "{{ vars.github_repo_url }}"
    namespace: "{{ flow.namespace }}"
    gitDirectory: "demos/py-etl-demo"

  - id: code
    type: io.kestra.plugin.scripts.python.Commands
    containerImage: ghcr.io/kestra-io/pydata:latest
    namespaceFiles:
      enabled: true
    beforeCommands:
      - pip install kestra
    outputFiles:
      - "{{ vars.filename }}"
    env:
      DATASET_URL: "{{ inputs.dataset_uri }}"
      DISCOUNTED_AMOUNT: "{{ inputs.discount_amount ?? 0 }}"
      FILENAME: "{{ vars.filename }}"
    commands:
      - python main.py

  - id: slack_message
    type: io.kestra.plugin.notifications.slack.SlackIncomingWebhook
    url: "{{ kv('SLACK_WEBHOOK') }}"
    payload: |
      {
        "text": "Total: ${{ outputs.code.vars.total }}"
      }

  - id: s3_upload_discounts
    type: io.kestra.plugin.aws.s3.Upload
    runIf: "{{ inputs.discount_amount > 0 }}"
    region: eu-west-2
    bucket: oss-example
    key: "processed_orders.csv"
    from: "{{ outputs.code.outputFiles['processed_orders.csv'] }}"
    accessKeyId: "{{ kv('AWS_ACCESS_KEY_ID') }}"
    secretKeyId: "{{ kv('AWS_SECRET_KEY_ID') }}"

errors:
  - id: slack_notification
    type: io.kestra.plugin.notifications.slack.SlackExecution
    url: "{{ kv('SLACK_WEBHOOK') }}"
    channel: "#general"
    executionId: "{{ execution.id }}"

triggers:
  - id: schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "@daily"

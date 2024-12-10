# ETL Demo with Python in Kestra

This demo gets the sum of orders from a CSV file, and can optionally generate a discount for each order in a new CSV file, which can be uploaded to S3.

## Inputs

This flow takes 2 inputs:
- Dataset URL
- Discount Percentage

These both have default values to them which allow them to

## Tasks

It contains 3 tasks to process a CSV file and upload a modified one to S3.

### Python Task 

Reads a CSV file with Pandas, Gets the sum and outputs to Kestra, and generates a new CSV file with a Discount total. 

The Discount total and CSV file input are dynamically passed to the Python code using Input expressions. This means we can make our Python code dynamic at execution, allowing us to pass different values at different executions quickly.

By using a `Script` task over a `Commands` task, writing expressions directly in Python is straightforward without the need for using Environment Variables to pass data in.

### Slack Message

This uses a Slack Webhook to send a message

### S3 Upload

This task uploads a file to S3.

It uses the new `runIf` property to determine whether the task should run or not. The expression used is based on an input provided. If no input provided, it will not run.

## Outputs

The Python task produces two types of Outputs:
- Variable Output
- File Output

We can use both of these in later tasks with expressions. For example, we send the Variable Output using an expression in the message property of the Slack message.

For the file, we can again, specify it with an expression in the property that requires a file path for the S3 Upload.

## Errors

It also contains Error Handling with the `errors` block. This means you can put any tasks you like under here to run if a task finishes with an error state.

In this example, if an error occurs, it will run `slack_notification` with information about the Flow Execution.

## KV Store

To pass secrets and values to tasks like the S3 upload, we use the KV Store like environment variables to prevent us hard coding our AWS secrets directly inside of our Flow. We can use this with `{{ kv('name_of_key') }}`.

## Triggers

It contains a Trigger to automatically run the workflow every day at 0:00 GMT. We are using the expression `@daily` to achieve this, but we can use a cron expression here.
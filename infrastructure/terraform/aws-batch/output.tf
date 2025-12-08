output "ecs_task_execution_role_arn" {
  value       = aws_iam_role.aws_ecs_task_execution_role.arn
  description = "ECS Task Execution Role"
}

output "ecs_task_role_arn" {
  value       = aws_iam_role.ecs_task_role.arn
  description = "ECS Task Role"
}

output "batch_job_queue_arn" {
  value       = aws_batch_job_queue.aws_batch_job_queue.arn
  description = "Batch Job Queue"
}

output "batch_compute_environment_arn" {
  value       = aws_batch_compute_environment.aws_batch_compute_environment.arn
  description = "Batch Compute Environment"
}
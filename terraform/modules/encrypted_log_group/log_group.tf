resource "aws_cloudwatch_log_group" "main" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.main.arn

  # CloudWatch Logs must be granted use of the key before the log group is created,
  # otherwise CreateLogGroup fails with AccessDeniedException. The log group only
  # references the key itself, so the dependency on the policy must be explicit.
  depends_on = [aws_kms_key_policy.main]

  lifecycle {
    prevent_destroy = true
  }
}
